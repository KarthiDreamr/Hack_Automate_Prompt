import random
import time
from playwright.async_api import Page
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def _take_screenshot(page: Page, stage: str):
    """Takes a screenshot and saves it to the screenshots directory."""
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    screenshot_path = os.path.join(
        screenshots_dir, f"error_{stage}.png"
    )
    try:
        await page.screenshot(path=screenshot_path)
        logging.info(f"Screenshot saved to {screenshot_path}")
    except Exception as e:
        logging.error(f"Could not take screenshot: {e}")


def _load_prompt_from_file(prompt_config: dict, config_dir: str) -> dict:
    """
    Loads prompt text from a file specified in the prompt's configuration.
    """
    prompt_file_path = os.path.join(config_dir, prompt_config["file"])
    if not os.path.exists(prompt_file_path):
        print(f"Warning: Prompt file not found: {prompt_file_path}")
        prompt_config["text"] = ""
        return prompt_config

    with open(prompt_file_path, "r") as f:
        prompt_config["text"] = f.read().strip()
    return prompt_config


async def _perform_delay(
    should_delay: bool, min_sec: float, max_sec: float, page: Page
):
    """Waits for a random duration within the specified range."""
    if not should_delay:
        return
    delay = random.uniform(min_sec, max_sec)
    logging.info(f"   ...waiting for {delay:.2f} seconds...")
    await page.wait_for_timeout(delay * 1000)


async def _navigate_to_challenge(page: Page, base_url: str):
    """Navigates to the challenge URL if not already there."""
    if base_url not in page.url:
        logging.info(f"Navigating to {base_url}...")
        await page.goto(base_url)
    else:
        logging.info(f"Already on page {base_url}")


async def _fill_prompt_and_submit(
    page: Page, prompt_selector: str, submit_selector: str, prompt_text: str
):
    """Fills the prompt textarea and clicks the submit button."""
    logging.info(f"Filling text area ('{prompt_selector}')")
    prompt_area = page.locator(prompt_selector)
    await prompt_area.wait_for(state="visible", timeout=10000)
    await prompt_area.fill(prompt_text)

    logging.info(f"Clicking submit prompt button ('{submit_selector}')")
    submit_button = page.locator(submit_selector)
    await submit_button.click(timeout=5000)


async def _submit_for_judging(page: Page, submit_judging_selector: str):
    """Waits for and clicks the 'Submit for Judging' button."""
    logging.info(f"Waiting for '{submit_judging_selector}' to become enabled...")
    submit_judging_button = page.locator(submit_judging_selector)
    try:
        await submit_judging_button.wait_for(timeout=180000)
        logging.info("'Submit for Judging' button is now enabled.")
        await submit_judging_button.click(timeout=180000)
        logging.info("Successfully clicked 'Submit for Judging' button.")
        return True
    except Exception as e:
        logging.error(
            f"Timeout or error waiting for or clicking 'Submit for Judging' button: {e}"
        )
        return False


async def _check_for_success(page: Page) -> bool:
    """Checks if the 'Challenge Conquered' popup is visible."""
    success_selector = 'h2:has-text("Challenge Conquered! 🎉")'
    success_element = page.locator(success_selector)
    if await success_element.is_visible(timeout=5000):
        logging.info("Challenge Conquered! 🎉")
        return True
    return False


async def _handle_failure_and_restart(page: Page) -> bool:
    """Clicks 'Restart Challenge' assuming the failure popup is already visible."""
    restart_selector = "button:has-text('Restart Challenge')"
    try:
        logging.info(
            "'Not Quite There Yet' popup confirmed. Clicking 'Restart Challenge'."
        )
        await page.locator(restart_selector).click(timeout=5000)
        return True
    except Exception:
        logging.warning(
            "'Restart Challenge' button not found or clickable on failure popup."
        )
        await _take_screenshot(page, "failure_popup_no_restart_button")
        return False


async def _handle_judging_failure(page: Page) -> bool:
    """Handles the visible judging failure popup by clicking 'Continue Current Chat'."""
    continue_button_selector = "button:has-text('Continue Current Chat')"
    continue_button = page.locator(continue_button_selector)

    logging.info("'Not Quite There Yet' popup confirmed. Looking for 'Continue' button.")
    try:
        await continue_button.wait_for(state="visible", timeout=5000)
        logging.info("Clicking 'Continue Current Chat'.")
        await continue_button.click(timeout=5000)
        return True
    except Exception:
        logging.warning("'Continue Current Chat' button not found on failure popup.")
        await _take_screenshot(page, "failure_popup_no_continue_button")
        return False


class ChallengeExecutor:
    def __init__(self, page: Page, config: dict, automation_settings: dict):
        self.page = page
        self.config = config
        self.automation_settings = automation_settings

    async def run(self):
        """Executes the defined interaction test sequence for a challenge."""
        if not self._validate_config(
            ["base_url", "selectors", "prompts"]
        ):
            return

        if self.automation_settings.get("navigate_to_base_url", True):
            await _navigate_to_challenge(self.page, self.config["base_url"])

        prompts = self._get_prompts()
        if not prompts:
            logging.error("No valid prompts found in the configuration.")
            return
            
        max_retries = (
            self.automation_settings.get("max_retries", 1)
            if self.automation_settings.get("loop_on_failure", True)
            else 1
        )

        for prompt in prompts:
            prompt_text = prompt.get("text")
            if not prompt_text:
                continue

            for attempt in range(max_retries):
                logging.info(
                    f"\n--- Running Interaction Test (Attempt {attempt + 1}/{max_retries}) ---"
                )
                logging.info(f"Using prompt: {prompt_text[:80]}...")

                await self._perform_step_delay()
                await _fill_prompt_and_submit(
                    self.page,
                    self.config["selectors"]["prompt_textarea"],
                    self.config["selectors"]["submit_prompt_button"],
                    prompt_text,
                )

                await self._perform_step_delay()
                judging_clicked = await _submit_for_judging(
                    self.page, self.config["selectors"]["submit_for_judging_button"]
                )

                if not judging_clicked:
                    await _take_screenshot(
                        self.page, "submit_for_judging_failed"
                    )
                    continue  # Try again

                await self._perform_step_delay()

                outcome = await self._wait_for_judging_outcome()

                if outcome == "success":
                    logging.info(
                        "Challenge successfully completed."
                    )
                    return  # Exit after first success

                elif outcome == "failure":
                    restarted = await _handle_failure_and_restart(self.page)
                    if restarted:
                        logging.info(
                            "Challenge failed, restarting for another attempt."
                        )
                        continue
                    else:
                        logging.warning(
                            "Submission resulted in a failure that could not be handled. Breaking from retries for this prompt."
                        )
                        await _take_screenshot(
                            self.page, "unhandled_failure_after_judging"
                        )
                        break  # Exit loop for this prompt

                else:  # timeout
                    logging.warning(
                        "Submission did not result in a clear success or failure state."
                    )
                    await _take_screenshot(self.page, "unknown_state_after_judging")
                    break  # Exit loop for this prompt
            else:  # Timeout
                logging.warning(
                    "Submission did not result in a clear success or failure state."
                )
                await _take_screenshot(self.page, "unknown_state_after_judging")
                break  # Exit loop for this prompt

        logging.info("Interaction test sequence processing completed.")

    async def run_judging_loop(self):
        """Runs a loop that repeatedly clicks the 'Submit for Judging' button."""
        if not self._validate_config(["selectors"]):
            return

        max_retries = self.automation_settings.get("max_retries", 10)

        for attempt in range(max_retries):
            logging.info(f"--- Judging Attempt {attempt + 1}/{max_retries} ---")

            outcome = await self._submit_and_wait_for_judging_outcome()

            if outcome == "success":
                logging.info("Challenge Conquered! Stopping judging loop.")
                break
            elif outcome == "failure":
                if await _handle_judging_failure(self.page):
                    logging.info("Challenge failed, continuing to next attempt.")
                    continue
                else:
                    logging.error(
                        "Failure popup detected, but could not be handled. Stopping."
                    )
                    await _take_screenshot(self.page, "judging_failure_unhandled")
                    break
            else:  # Timeout
                logging.warning(
                    "Submission did not result in a clear success or failure state. Stopping."
                )
                break
        logging.info("Judging loop finished.")

    async def _submit_and_wait_for_judging_outcome(self) -> str:
        """
        Submits for judging, waits for the result, and returns the outcome.
        Possible outcomes: "success", "failure", "timeout".
        """
        judging_clicked = await _submit_for_judging(
            self.page, self.config["selectors"]["submit_for_judging_button"]
        )
        if not judging_clicked:
            return "failure"  # Error already logged in _submit_for_judging

        await self._perform_step_delay()

        return await self._wait_for_judging_outcome()

    async def _wait_for_judging_outcome(self) -> str:
        """
        Waits for the result of judging and returns the outcome.
        Possible outcomes: "success", "failure", "timeout".
        """
        success_selector = 'h2:has-text("Challenge Conquered! 🎉")'
        failure_selector = 'h2:has-text("Not Quite There Yet 💪")'

        total_wait_sec = self.automation_settings.get("judging_timeout_sec", 180)
        logging.info(f"Waiting for judging result (up to {total_wait_sec} seconds)...")

        start_time = time.time()
        outcome = "timeout"
        while time.time() - start_time < total_wait_sec:
            if await self.page.locator(success_selector).is_visible():
                logging.info("Success condition met: Challenge Conquered! 🎉")
                outcome = "success"
                break
            if await self.page.locator(failure_selector).is_visible():
                logging.info("Failure condition met: Not Quite There Yet 💪")
                outcome = "failure"
                break
            await self.page.wait_for_timeout(500)

        if outcome == "timeout":
            logging.warning("Timed out waiting for judging result.")
            await _take_screenshot(self.page, "judging_timeout")

        return outcome

    def _validate_config(self, required_keys: list[str]) -> bool:
        """Validates that the required keys are in the config."""
        for key in required_keys:
            if key not in self.config:
                logging.error(f"Missing required key in config: '{key}'")
                return False
        if "selectors" in required_keys:
            for selector in ["prompt_textarea", "submit_prompt_button", "submit_for_judging_button"]:
                if selector not in self.config.get("selectors", {}):
                    logging.error(f"Missing required selector in config: '{selector}'")
                    return False
        return True

    def _get_prompts(self) -> list[dict]:
        """
        Loads all prompts from the configuration, processing file links as needed.
        """
        prompts = self.config.get("prompts", [])
        loaded_prompts = []
        for prompt_config in prompts:
            if "file" in prompt_config:
                # Correct the path to be relative to the project root (where config.yaml is)
                config_dir = os.path.dirname(os.path.abspath("config.yaml"))
                loaded_prompts.append(_load_prompt_from_file(prompt_config, config_dir))
            elif "text" in prompt_config:
                loaded_prompts.append(prompt_config)
        return loaded_prompts

    async def _perform_step_delay(self):
        """Performs a delay if configured."""
        await _perform_delay(
            self.automation_settings.get("random_delay", False),
            self.automation_settings.get("delay_min_sec", 1),
            self.automation_settings.get("delay_max_sec", 5),
            self.page,
        )


async def execute_interaction_test(
    page: Page, config: dict, automation_settings: dict
):
    """Executes the defined interaction test sequence for a challenge."""
    executor = ChallengeExecutor(page, config, automation_settings)
    await executor.run()
