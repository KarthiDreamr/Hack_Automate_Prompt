import logging
import time
from ..steps import (
    navigate_to_challenge,
    fill_prompt_and_submit,
    submit_for_judging,
    handle_failure_and_restart,
)
from ..utils import take_screenshot


async def run(self):
    if not self._validate_config(["base_url", "selectors", "prompts"]):
        return

    if self.automation_settings.get("navigate_to_base_url", True):
        await navigate_to_challenge(self.page, self.config["base_url"])

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
            await fill_prompt_and_submit(
                self.page,
                self.config["selectors"]["prompt_textarea"],
                self.config["selectors"]["submit_prompt_button"],
                prompt_text,
                self.automation_settings.get("timeouts", {}),
            )

            await self._perform_step_delay()
            judging_clicked = await submit_for_judging(
                self.page,
                self.config["selectors"]["submit_for_judging_button"],
                self.automation_settings.get("timeouts", {}),
            )

            if not judging_clicked:
                await take_screenshot(self.page, "submit_for_judging_failed")
                continue

            await self._perform_step_delay()

            outcome = await self._wait_for_judging_outcome()

            if outcome == "success":
                logging.info("Challenge successfully completed.")
                return
            elif outcome == "failure":
                restarted = await handle_failure_and_restart(
                    self.page, self.automation_settings.get("timeouts", {})
                )
                if restarted:
                    logging.info("Challenge failed, restarting for another attempt.")
                    continue
                else:
                    logging.warning(
                        "Submission resulted in a failure that could not be handled. Breaking from retries for this prompt."
                    )
                    await take_screenshot(self.page, "unhandled_failure_after_judging")
                    break
            else:
                logging.warning(
                    "Submission did not result in a clear success or failure state."
                )
                await take_screenshot(self.page, "unknown_state_after_judging")
                break
        else:
            logging.warning(
                "Submission did not result in a clear success or failure state."
            )
            await take_screenshot(self.page, "unknown_state_after_judging")
            break

    logging.info("Interaction test sequence processing completed.")


