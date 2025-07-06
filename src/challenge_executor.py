# Standard library
import random
import time
import os
import logging

# Third-party
from playwright.async_api import Page, TimeoutError

# Local imports
from .config_loader import load_config

# ---------------------------------------------------------------------------
# Load default timeout/delay configuration from YAML so that Python source code
# contains **no magic numbers**.  All timing values can now be changed from
# `config.yaml` alone, keeping the behaviour fully configurable.
# ---------------------------------------------------------------------------

_CFG = load_config() or {}
_AUTOMATION_SETTINGS = _CFG.get("automation_settings", {})
_DEFAULT_TIMEOUTS = _AUTOMATION_SETTINGS.get("timeouts", {})
_DEFAULT_DELAY_MIN = _AUTOMATION_SETTINGS.get("delay_min_sec", 1)
_DEFAULT_DELAY_MAX = _AUTOMATION_SETTINGS.get("delay_max_sec", 5)

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
    page: Page, prompt_selector: str, submit_selector: str, prompt_text: str, timeouts: dict | None = None
):
    """Fills the prompt textarea and clicks the submit button, using configurable timeouts."""
    if timeouts is None:
        timeouts = {}

    # Retrieve timeout values with sensible defaults
    prompt_visible_ms = timeouts.get(
        "prompt_visible_ms", _DEFAULT_TIMEOUTS.get("prompt_visible_ms")
    )
    submit_click_ms = timeouts.get(
        "submit_prompt_click_ms", _DEFAULT_TIMEOUTS.get("submit_prompt_click_ms")
    )

    logging.info(f"Filling text area ('{prompt_selector}')")
    prompt_area = page.locator(prompt_selector)
    await prompt_area.wait_for(state="visible", timeout=prompt_visible_ms)
    await prompt_area.fill(prompt_text)

    logging.info(f"Clicking submit prompt button ('{submit_selector}')")
    submit_button = page.locator(submit_selector)
    await submit_button.click(timeout=submit_click_ms)


async def _submit_for_judging(page: Page, submit_judging_selector: str, timeouts: dict | None = None):
    """Waits for and clicks the 'Submit for Judging' button, using configurable timeouts."""
    if timeouts is None:
        timeouts = {}
    enable_ms = timeouts.get(
        "submit_for_judging_enable_ms",
        _DEFAULT_TIMEOUTS.get("submit_for_judging_enable_ms"),
    )
    click_ms = timeouts.get(
        "submit_for_judging_click_ms",
        _DEFAULT_TIMEOUTS.get("submit_for_judging_click_ms"),
    )

    logging.info(f"Waiting for '{submit_judging_selector}' to become enabled...")
    submit_judging_button = page.locator(submit_judging_selector)
    try:
        await submit_judging_button.wait_for(timeout=enable_ms)
        logging.info("'Submit for Judging' button is now enabled.")
        await submit_judging_button.click(timeout=click_ms)
        logging.info("Successfully clicked 'Submit for Judging' button.")
        return True
    except Exception as e:
        logging.error(
            f"Timeout or error waiting for or clicking 'Submit for Judging' button: {e}"
        )
        return False


async def _check_for_success(page: Page, timeouts: dict | None = None) -> bool:
    """Checks if the 'Challenge Conquered' popup is visible."""
    if timeouts is None:
        timeouts = {}
    success_visible_ms = timeouts.get(
        "success_visible_ms", _DEFAULT_TIMEOUTS.get("success_visible_ms")
    )

    success_selector = 'h2:has-text("Challenge Conquered! 🎉")'
    success_element = page.locator(success_selector)
    if await success_element.is_visible(timeout=success_visible_ms):
        logging.info("Challenge Conquered! 🎉")
        return True
    return False


async def _handle_failure_and_restart(page: Page, timeouts: dict | None = None) -> bool:
    """Clicks 'Restart Challenge' assuming the failure popup is already visible."""
    if timeouts is None:
        timeouts = {}
    restart_click_ms = timeouts.get(
        "restart_click_ms", _DEFAULT_TIMEOUTS.get("restart_click_ms")
    )

    restart_selector = "button:has-text('Restart Challenge')"
    try:
        logging.info(
            "'Not Quite There Yet' popup confirmed. Clicking 'Restart Challenge'."
        )
        await page.locator(restart_selector).click(timeout=restart_click_ms)
        return True
    except Exception:
        logging.warning(
            "'Restart Challenge' button not found or clickable on failure popup."
        )
        await _take_screenshot(page, "failure_popup_no_restart_button")
        return False


async def _handle_judging_failure(page: Page, timeouts: dict | None = None) -> bool:
    """Handles the visible judging failure popup by clicking 'Continue Current Chat'."""
    if timeouts is None:
        timeouts = {}
    continue_visible_ms = timeouts.get(
        "continue_button_visible_ms",
        _DEFAULT_TIMEOUTS.get("continue_button_visible_ms"),
    )
    continue_click_ms = timeouts.get(
        "continue_button_click_ms",
        _DEFAULT_TIMEOUTS.get("continue_button_click_ms"),
    )

    continue_button_selector = "button:has-text('Continue Current Chat')"
    continue_button = page.locator(continue_button_selector)

    logging.info("'Not Quite There Yet' popup confirmed. Looking for 'Continue' button.")
    try:
        await continue_button.wait_for(state="visible", timeout=continue_visible_ms)
        logging.info("Clicking 'Continue Current Chat'.")
        await continue_button.click(timeout=continue_click_ms)
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
                    self.automation_settings.get("timeouts", {}),
                )

                await self._perform_step_delay()
                judging_clicked = await _submit_for_judging(
                    self.page, self.config["selectors"]["submit_for_judging_button"],
                    self.automation_settings.get("timeouts", {})
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
                    restarted = await _handle_failure_and_restart(self.page, self.automation_settings.get("timeouts", {}))
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
                if await _handle_judging_failure(self.page, self.automation_settings.get("timeouts", {})):
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
            self.page, self.config["selectors"]["submit_for_judging_button"],
            self.automation_settings.get("timeouts", {})
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

        total_wait_sec = self._get_timeout(
            "judging_timeout_sec", _DEFAULT_TIMEOUTS.get("judging_timeout_sec")
        )
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
            polling_interval_ms = self._get_timeout(
                "polling_interval_ms", _DEFAULT_TIMEOUTS.get("polling_interval_ms")
            )
            await self.page.wait_for_timeout(polling_interval_ms)

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
            self.automation_settings.get("delay_min_sec", _DEFAULT_DELAY_MIN),
            self.automation_settings.get("delay_max_sec", _DEFAULT_DELAY_MAX),
            self.page,
        )

    def _get_timeout(self, key: str, default: int) -> int:
        """Retrieve a timeout value (in ms or sec depending on context) from the config."""
        return (
            self.automation_settings.get("timeouts", {}).get(key,
                self.automation_settings.get(key, default)
            )
        )

    # New intent loop implementation
    async def run_intent_loop(self):
        """Runs a loop that pastes a prompt, submits it, and refreshes on failure."""
        if not self._validate_config(["base_url", "selectors", "prompts"]):
            return

        if self.automation_settings.get("navigate_to_base_url", True):
            await _navigate_to_challenge(self.page, self.config["base_url"])

        prompts = self._get_prompts()
        if not prompts:
            logging.error("No valid prompts found in the configuration.")
            return

        max_retries = self.automation_settings.get("max_retries", 1000)
        logging.info(f"Starting Intent Loop with max_retries={max_retries}")

        for attempt in range(max_retries):
            logging.info(f"--- Intent Attempt {attempt + 1}/{max_retries} ---")

            # Use the first prompt for now (intent template)
            prompt_text = prompts[0].get("text", "")
            if not prompt_text:
                logging.warning("Prompt text is empty. Skipping attempt.")
                continue

            # Step 1 & 2: Fill prompt and submit
            await self._perform_step_delay()
            selectors_cfg = self.config.get("selectors", {})
            textarea_selector = selectors_cfg.get(
                "intent_textarea", selectors_cfg.get("prompt_textarea")
            )
            submit_selector = selectors_cfg.get(
                "submit_template_button", selectors_cfg.get("submit_prompt_button")
            )

            await _fill_prompt_and_submit(
                self.page,
                textarea_selector,
                submit_selector,
                prompt_text,
                self.automation_settings.get("timeouts", {}),
            )

            # Wait for intent outcome (long wait)
            outcome = await self._wait_for_intent_outcome()

            if outcome == "failure":
                logging.info("Challenge failed detected. Refreshing page and retrying...")
                try:
                    await self.page.reload()
                except Exception as e:
                    logging.error(f"Error refreshing page: {e}")
                continue  # Start next attempt
            else:
                logging.info("No failure detected after wait. Stopping intent loop.")
                break

        logging.info("Intent loop finished.")

    async def _wait_for_intent_outcome(self) -> str:
        """Waits for either a failure popup or times out. Returns 'failure' or 'timeout'."""
        failure_selector = "h3:has-text(\"Challenge Failed\")"
        total_wait_sec = self._get_timeout(
            "intent_wait_sec", _DEFAULT_TIMEOUTS.get("intent_wait_sec")
        )
        polling_interval_ms = self._get_timeout(
            "polling_interval_ms", _DEFAULT_TIMEOUTS.get("polling_interval_ms")
        )

        logging.info(f"Waiting up to {total_wait_sec} seconds for intent outcome...")
        start_time = time.time()
        outcome = "timeout"
        while time.time() - start_time < total_wait_sec:
            if await self.page.locator(failure_selector).is_visible():
                logging.info("Failure condition met: Challenge Failed")
                outcome = "failure"
                break
            await self.page.wait_for_timeout(polling_interval_ms)
        return outcome

    async def run_intent_loop_2(self):
        """
        Runs an intent loop that submits a prompt once, then repeatedly checks
        for a 'Try Again' button. If found, it resets the state and
        resubmits. If not found after a timeout, it assumes success.
        """
        if not self._validate_config(["base_url", "selectors", "prompts"]):
            return

        if self.automation_settings.get("navigate_to_base_url", True):
            await _navigate_to_challenge(self.page, self.config["base_url"])

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

        # Prepare selectors and timeouts
        selectors_cfg = self.config.get("selectors", {})
        textarea_selector = selectors_cfg.get(
            "intent_textarea", selectors_cfg.get("prompt_textarea")
        )
        submit_selector = selectors_cfg.get(
            "submit_template_button", selectors_cfg.get("submit_prompt_button")
        )
        timeouts = self.automation_settings.get("timeouts", {})

        # Step 1: Perform the initial submission
        logging.info("--- Performing initial prompt submission ---")
        await _fill_prompt_and_submit(
            self.page, textarea_selector, submit_selector, prompt_text, timeouts
        )
        await self._perform_step_delay()

        # Step 2: Loop to check for failure ('Try Again' button) or success (timeout)
        for attempt in range(max_retries):
            logging.info(
                f"--- Intent Attempt {attempt + 1}/{max_retries}: Waiting for outcome ---"
            )

            try_again_selector = 'button:has-text("Try Again")'
            outcome_wait_sec = self._get_timeout(
                "intent_outcome_wait_sec",
                _DEFAULT_TIMEOUTS.get("intent_outcome_wait_sec"),
            )

            try:
                # Wait for the failure condition
                await self.page.locator(try_again_selector).wait_for(
                    state="visible", timeout=outcome_wait_sec * 1000
                )

                # Failure detected: Reset and re-submit
                logging.info("'Try Again' button detected. Resetting and resubmitting.")
                await self.page.locator(try_again_selector).click(
                    timeout=self._get_timeout(
                        "intent_button_click_ms",
                        _DEFAULT_TIMEOUTS.get("intent_button_click_ms"),
                    )
                )
                await self._perform_step_delay()

                back_button_selector = (
                    "button.z-20.cursor-pointer.h-10.w-10.border-azure\\/40.rounded-none"
                    ":has(svg.lucide-chevron-left)"
                )
                await self.page.locator(back_button_selector).click(
                    timeout=self._get_timeout(
                        "intent_button_click_ms",
                        _DEFAULT_TIMEOUTS.get("intent_button_click_ms"),
                    )
                )
                await self._perform_step_delay()

                await _fill_prompt_and_submit(
                    self.page, textarea_selector, submit_selector, prompt_text, timeouts
                )

            except TimeoutError:
                # Success condition: 'Try Again' button did not appear
                logging.info(
                    "'Try Again' button not found within timeout. Challenge Conquered!"
                )
                await _take_screenshot(self.page, "intent_loop_2_success")
                return  # Exit successfully

            except Exception as e:
                logging.error(f"Unexpected error in intent loop 2, attempt {attempt + 1}: {e}")
                await _take_screenshot(self.page, f"intent_loop_2_error_attempt_{attempt + 1}")
                logging.info("Refreshing page and re-submitting to recover.")
                try:
                    await self.page.reload()
                    await self._perform_step_delay()
                    await _fill_prompt_and_submit(
                        self.page, textarea_selector, submit_selector, prompt_text, timeouts
                    )
                except Exception as reload_e:
                    logging.error(f"Failed to recover by refreshing page: {reload_e}")
                    break  # Exit loop if recovery fails

        logging.warning("Intent loop 2 finished after reaching max retries without success.")


async def execute_interaction_test(
    page: Page, config: dict, automation_settings: dict
):
    """Executes the defined interaction test sequence for a challenge."""
    executor = ChallengeExecutor(page, config, automation_settings)
    await executor.run()
