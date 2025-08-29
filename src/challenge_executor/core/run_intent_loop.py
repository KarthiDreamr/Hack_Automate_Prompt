import logging
from ..steps import navigate_to_challenge, fill_prompt_and_submit


async def run_intent_loop(self):
    if not self._validate_config(["base_url", "selectors", "prompts"]):
        return

    if self.automation_settings.get("navigate_to_base_url", True):
        await navigate_to_challenge(self.page, self.config["base_url"])

    prompts = self._get_prompts()
    if not prompts:
        logging.error("No valid prompts found in the configuration.")
        return

    max_retries = self.automation_settings.get("max_retries", 1000)
    logging.info(f"Starting Intent Loop with max_retries={max_retries}")

    for attempt in range(max_retries):
        logging.info(f"--- Intent Attempt {attempt + 1}/{max_retries} ---")

        prompt_text = prompts[0].get("text", "")
        if not prompt_text:
            logging.warning("Prompt text is empty. Skipping attempt.")
            continue

        await self._perform_step_delay()
        selectors_cfg = self.config.get("selectors", {})
        textarea_selector = selectors_cfg.get(
            "intent_textarea", selectors_cfg.get("prompt_textarea")
        )
        submit_selector = selectors_cfg.get(
            "submit_template_button", selectors_cfg.get("submit_prompt_button")
        )

        await fill_prompt_and_submit(
            self.page,
            textarea_selector,
            submit_selector,
            prompt_text,
            self.automation_settings.get("timeouts", {}),
        )

        outcome = await self._wait_for_intent_outcome()

        if outcome == "failure":
            logging.info("Challenge failed detected. Refreshing page and retrying...")
            try:
                await self.page.reload()
            except Exception as e:
                logging.error(f"Error refreshing page: {e}")
            continue
        else:
            logging.info("No failure detected after wait. Stopping intent loop.")
            break

    logging.info("Intent loop finished.")


