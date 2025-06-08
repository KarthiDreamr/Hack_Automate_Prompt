import random
import time
from playwright.async_api import Page
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def _take_screenshot(page: Page, challenge_name: str, stage: str):
    """Takes a screenshot and saves it to the screenshots directory."""
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    screenshot_path = os.path.join(
        screenshots_dir, f"error_{stage}_{challenge_name}.png"
    )
    try:
        await page.screenshot(path=screenshot_path)
        logging.info(f"Screenshot saved to {screenshot_path}")
    except Exception as e:
        logging.error(f"Could not take screenshot: {e}")


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
    """Checks for the failure popup and clicks 'Restart Challenge' if found."""
    restart_selector = "button:has-text('Restart Challenge')"
    restart_button = page.locator(restart_selector)
    if await restart_button.is_visible(timeout=5000):
        logging.info(
            "'Not Quite There Yet' popup detected. Clicking 'Restart Challenge'."
        )
        await restart_button.click(timeout=5000)
        return True
    return False


async def _handle_judging_failure(page: Page, challenge_name: str) -> bool:
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
        await _take_screenshot(
            page, challenge_name, "failure_popup_no_continue_button"
        )
        return False


class ChallengeExecutor:
    def __init__(self, page: Page, challenge_config: dict, automation_settings: dict):
        self.page = page
        self.challenge_config = challenge_config
        self.automation_settings = automation_settings
        self.challenge_name = challenge_config.get(
            "challenge_name", "unknown_challenge"
        )

    async def run(self):
        """Executes the defined interaction test sequence for a challenge."""
        if not self._validate_config(
            ["base_url", "prompt_textarea", "submit_prompt_button", "submit_for_judging_button"]
        ):
            return

        if self.automation_settings.get("navigate_to_base_url", True):
            await _navigate_to_challenge(self.page, self.challenge_config["base_url"])

        prompt_text = self._get_prompt_text()
        max_retries = (
            self.automation_settings.get("max_retries", 1)
            if self.automation_settings.get("loop_on_failure", True)
            else 1
        )

        for attempt in range(max_retries):
            logging.info(
                f"\n--- Running Interaction Test for '{self.challenge_name}' (Attempt {attempt + 1}/{max_retries}) ---"
            )

            await self._perform_step_delay()
            await _fill_prompt_and_submit(
                self.page,
                self.challenge_config["prompt_textarea"],
                self.challenge_config["submit_prompt_button"],
                prompt_text,
            )

            await self._perform_step_delay()
            judging_clicked = await _submit_for_judging(
                self.page, self.challenge_config["submit_for_judging_button"]
            )

            if not judging_clicked:
                await _take_screenshot(
                    self.page, self.challenge_name, "submit_for_judging_failed"
                )
                continue  # Try again

            await self._perform_step_delay()

            if await _check_for_success(self.page):
                logging.info(
                    f"Challenge '{self.challenge_name}' successfully completed."
                )
                return  # Exit the loop and function on success

            restarted = await _handle_failure_and_restart(self.page)
            if restarted:
                logging.info("Challenge failed, restarting for another attempt.")
                continue  # Continue to the next attempt
            else:
                logging.warning(
                    "Submission did not result in a clear success or failure state."
                )
                await _take_screenshot(
                    self.page, self.challenge_name, "unknown_state_after_judging"
                )
                break  # Exit loop if not a clear failure that was restarted

        logging.info("Interaction test sequence processing completed.")

    async def run_judging_loop(self):
        """Runs a loop that repeatedly clicks the 'Submit for Judging' button."""
        if not self._validate_config(["submit_for_judging_button"]):
            return

        max_retries = self.automation_settings.get("max_retries", 10)

        for attempt in range(max_retries):
            logging.info(f"--- Judging Attempt {attempt + 1}/{max_retries} ---")
            judging_clicked = await _submit_for_judging(
                self.page, self.challenge_config["submit_for_judging_button"]
            )

            if not judging_clicked:
                logging.error("Failed to click judging button, stopping.")
                await _take_screenshot(
                    self.page, self.challenge_name, "judging_loop_failed"
                )
                break

            await self._perform_step_delay()

            # Wait for either success or failure popup
            success_selector = 'h2:has-text("Challenge Conquered! 🎉")'
            failure_selector = 'h2:has-text("Not Quite There Yet 💪")'

            total_wait_sec = self.automation_settings.get("judging_timeout_sec", 180)
            logging.info(f"Waiting for judging result (up to {total_wait_sec} seconds)...")

            start_time = time.time()
            outcome = None
            while time.time() - start_time < total_wait_sec:
                if await self.page.locator(success_selector).is_visible():
                    outcome = "success"
                    break
                if await self.page.locator(failure_selector).is_visible():
                    outcome = "failure"
                    break
                await self.page.wait_for_timeout(500)  # poll every 500ms

            if outcome == "success":
                logging.info("Challenge Conquered! Stopping judging loop.")
                break
            elif outcome == "failure":
                if await _handle_judging_failure(self.page, self.challenge_name):
                    logging.info("Challenge failed, continuing to next attempt.")
                    continue
                else:
                    logging.error(
                        "Failure popup detected, but could not be handled. Stopping."
                    )
                    await _take_screenshot(
                        self.page, self.challenge_name, "judging_failure_unhandled"
                    )
                    break
            else:  # Timeout
                logging.warning(
                    "Submission did not result in a clear success or failure state."
                )
                await _take_screenshot(
                    self.page, self.challenge_name, "unknown_state_after_judging"
                )
                break
        logging.info("Judging loop finished.")

    async def run_resubmission_loop(self, submission_id: str):
        """Runs a loop that repeatedly clicks the 'Submit for Judging' button."""
        if not self._validate_config(["base_url", "submit_for_judging_button"]):
            return

        resubmission_url = (
            f"{self.challenge_config['base_url']}/submission/{submission_id}"
        )
        logging.info(f"Navigating to resubmission URL: {resubmission_url}")
        await self.page.goto(resubmission_url)

        max_retries = self.automation_settings.get("max_retries", 10)

        for attempt in range(max_retries):
            logging.info(f"--- Resubmission Attempt {attempt + 1}/{max_retries} ---")
            judging_clicked = await _submit_for_judging(
                self.page, self.challenge_config["submit_for_judging_button"]
            )

            if not judging_clicked:
                logging.error("Failed to click judging button, stopping.")
                await _take_screenshot(
                    self.page, self.challenge_name, "resubmission_loop_failed"
                )
                break

            await self._perform_step_delay()

            if await _check_for_success(self.page):
                logging.info("Challenge Conquered! Stopping resubmission loop.")
                break

            # In resubmission, we look for a "Continue" button instead of "Restart"
            continue_button = self.page.locator("button:has-text('Continue Current Chat')")
            if await continue_button.is_visible(timeout=5000):
                logging.info("Popup detected. Clicking 'Continue Current Chat'.")
                await continue_button.click(timeout=5000)
            else:
                logging.warning(
                    "Submission did not result in a clear success or continue state."
                )
                await _take_screenshot(
                    self.page,
                    f"resubmission_{submission_id}",
                    "unknown_state_after_judging",
                )
        logging.info("Resubmission loop finished.")

    def _validate_config(self, required_keys: list[str]) -> bool:
        """Validates that the essential configuration keys are present."""
        if self.challenge_config is None:
            logging.error("challenge_config is not loaded.")
            return False

        for key in required_keys:
            if key not in self.challenge_config:
                logging.error(f"Missing required key '{key}' in challenge_config.")
                return False
        return True

    def _get_prompt_text(self) -> str:
        """Returns the prompt text, either from a list or a single string."""
        prompts_config = self.challenge_config.get("prompts")
        if prompts_config and len(prompts_config) > 0:
            return prompts_config[0].get("text", "Default test prompt")
        return "Default test prompt"

    async def _perform_step_delay(self):
        """Performs a delay based on automation settings."""
        await _perform_delay(
            self.automation_settings.get("random_delay", True),
            self.automation_settings.get("delay_min_sec", 5),
            self.automation_settings.get("delay_max_sec", 60),
            self.page,
        )


async def execute_interaction_test(
    page: Page, challenge_config: dict, automation_settings: dict
):
    """Executes the defined interaction test sequence for a challenge."""
    executor = ChallengeExecutor(page, challenge_config, automation_settings)
    await executor.run()
