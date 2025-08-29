import logging
from ..utils import take_screenshot
from ..steps import handle_judging_failure


async def run_judging_loop(self):
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
            if await handle_judging_failure(self.page, self.automation_settings.get("timeouts", {})):
                logging.info("Challenge failed, continuing to next attempt.")
                continue
            else:
                logging.error(
                    "Failure popup detected, but could not be handled. Stopping."
                )
                await take_screenshot(self.page, "judging_failure_unhandled")
                break
        else:
            logging.warning(
                "Submission did not result in a clear success or failure state. Stopping."
            )
            break
    logging.info("Judging loop finished.")


