import logging
import time
from ..config import DEFAULT_TIMEOUTS


async def wait_for_intent_outcome(self) -> str:
    failure_selector = 'h3:has-text("Challenge Failed")'
    total_wait_sec = self._get_timeout(
        "intent_wait_sec", DEFAULT_TIMEOUTS.get("intent_wait_sec")
    )
    polling_interval_ms = self._get_timeout(
        "polling_interval_ms", DEFAULT_TIMEOUTS.get("polling_interval_ms")
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


