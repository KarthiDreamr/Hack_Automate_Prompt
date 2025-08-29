import logging
import time
from ..config import DEFAULT_TIMEOUTS


async def agent_track_submit(self, text: str, timeouts: dict | None = None):
    if timeouts is None:
        timeouts = {}

    prompt_visible_ms = timeouts.get(
        "prompt_visible_ms", DEFAULT_TIMEOUTS.get("prompt_visible_ms")
    )
    submit_click_ms = timeouts.get(
        "submit_prompt_click_ms", DEFAULT_TIMEOUTS.get("submit_prompt_click_ms")
    )
    enable_wait_ms = timeouts.get(
        "submit_template_enable_ms", DEFAULT_TIMEOUTS.get("submit_for_judging_enable_ms")
    )

    textarea_selector = (
        'textarea[placeholder^="Write your injection intent directly"]'
    )
    submit_button_selector = 'button:has-text("Submit Template")'

    logging.info("Filling intent textarea for agent-track-submit")
    textarea = self.page.locator(textarea_selector)
    await textarea.wait_for(state="visible", timeout=prompt_visible_ms)
    await textarea.fill(text)

    logging.info("Waiting for 'Submit Template' button to enable, then clicking")
    submit_button = self.page.locator(submit_button_selector)
    await submit_button.wait_for(state="visible", timeout=prompt_visible_ms)

    start_time = time.time()
    while True:
        try:
            if not await submit_button.is_disabled():
                break
        except Exception:
            pass
        if (time.time() - start_time) * 1000 > (enable_wait_ms or 30000):
            logging.warning("'Submit Template' button did not enable within timeout; attempting click anyway")
            break
        await self.page.wait_for_timeout(200)

    await submit_button.click(timeout=submit_click_ms)


