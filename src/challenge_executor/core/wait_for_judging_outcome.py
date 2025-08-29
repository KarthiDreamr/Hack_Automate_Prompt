import logging
import time
from ..utils import take_screenshot
from ..config import DEFAULT_TIMEOUTS


async def wait_for_judging_outcome(self) -> str:
    success_selector = 'h2:has-text("Challenge Conquered! 🎉")'
    failure_selector = 'h2:has-text("Not Quite There Yet 💪")'

    total_wait_sec = self._get_timeout(
        "judging_timeout_sec", DEFAULT_TIMEOUTS.get("judging_timeout_sec")
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
            "polling_interval_ms", DEFAULT_TIMEOUTS.get("polling_interval_ms")
        )
        await self.page.wait_for_timeout(polling_interval_ms)

    if outcome == "timeout":
        logging.warning("Timed out waiting for judging result.")
        await take_screenshot(self.page, "judging_timeout")

    return outcome


