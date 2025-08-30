import logging
from playwright.async_api import TimeoutError
from ...steps import fill_prompt_and_submit, navigate_to_challenge
from ...utils import take_screenshot
from ...config import DEFAULT_TIMEOUTS


async def run_intent_loop_2(self):
    if not self._validate_config(["base_url", "selectors", "prompts"]):
        return

    if self.automation_settings.get("navigate_to_base_url", True):
        await navigate_to_challenge(self.page, self.config["base_url"])

    prompts = self._get_prompts()
    if not prompts:
        logging.error("No valid prompts found in the configuration.")
        return

    prompt_text = prompts[0].get("text", "")
    if not prompt_text:
        logging.warning("Prompt text is empty. Stopping.")
        return

    max_retries = self.automation_settings.get("max_retries", 1000)
    logging.info(f"Starting Intent Loop 2 with max_retries={max_retries}")

    selectors_cfg = self.config.get("selectors", {})
    textarea_selector = selectors_cfg.get(
        "intent_textarea", selectors_cfg.get("prompt_textarea")
    )
    submit_selector = selectors_cfg.get(
        "submit_template_button", selectors_cfg.get("submit_prompt_button")
    )
    timeouts = self.automation_settings.get("timeouts", {})

    logging.info("--- Performing initial prompt submission ---")
    await fill_prompt_and_submit(
        self.page, textarea_selector, submit_selector, prompt_text, timeouts
    )
    await self._perform_step_delay()

    for attempt in range(max_retries):
        logging.info(
            f"--- Intent Attempt {attempt + 1}/{max_retries}: Waiting for outcome ---"
        )

        try_again_selector = 'button:has-text("Try Again")'
        outcome_wait_sec = self._get_timeout(
            "intent_outcome_wait_sec", DEFAULT_TIMEOUTS.get("intent_outcome_wait_sec")
        )

        try:
            await self.page.locator(try_again_selector).wait_for(
                state="visible", timeout=outcome_wait_sec * 1000
            )

            logging.info("'Try Again' button detected. Resetting and resubmitting.")
            await self.page.locator(try_again_selector).click(
                timeout=self._get_timeout(
                    "intent_button_click_ms", DEFAULT_TIMEOUTS.get("intent_button_click_ms")
                )
            )
            await self._perform_step_delay()

            back_button_selector = (
                "button.z-20.cursor-pointer.h-10.w-10.border-azure\\/40.rounded-none:has(svg.lucide-chevron-left)"
            )
            await self.page.locator(back_button_selector).click(
                timeout=self._get_timeout(
                    "intent_button_click_ms", DEFAULT_TIMEOUTS.get("intent_button_click_ms")
                )
            )
            await self._perform_step_delay()

            await fill_prompt_and_submit(
                self.page, textarea_selector, submit_selector, prompt_text, timeouts
            )

        except TimeoutError:
            logging.info(
                "'Try Again' button not found within timeout. Challenge Conquered!"
            )
            await take_screenshot(self.page, "intent_loop_2_success")
            return

        except Exception as e:
            logging.error(f"Unexpected error in intent loop 2, attempt {attempt + 1}: {e}")
            await take_screenshot(self.page, f"intent_loop_2_error_attempt_{attempt + 1}")
            logging.info("Refreshing page and re-submitting to recover.")
            try:
                await self.page.reload()
                await self._perform_step_delay()
                await fill_prompt_and_submit(
                    self.page, textarea_selector, submit_selector, prompt_text, timeouts
                )
            except Exception as reload_e:
                logging.error(f"Failed to recover by refreshing page: {reload_e}")
                break

    logging.warning("Intent loop 2 finished after reaching max retries without success.")


