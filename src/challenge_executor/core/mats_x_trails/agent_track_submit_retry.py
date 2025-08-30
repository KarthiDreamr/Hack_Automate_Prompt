import logging
import time
import random
from ...config import DEFAULT_TIMEOUTS


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


async def agent_track_submit_with_retry(self, text: str, timeouts: dict | None = None, config: dict | None = None):
    """
    Enhanced version of agent_track_submit that continues looping with "Try Again" button
    until max_retries is reached according to config.yaml settings.
    """
    if timeouts is None:
        timeouts = {}
    if config is None:
        config = {}

    # Get configuration settings
    max_retries = config.get("max_retries", 1000)
    delay_min_sec = config.get("delay_min_sec", 4)
    delay_max_sec = config.get("delay_max_sec", 12)
    random_delay = config.get("random_delay", False)
    
    # Get timeout settings
    prompt_visible_ms = timeouts.get(
        "prompt_visible_ms", DEFAULT_TIMEOUTS.get("prompt_visible_ms")
    )
    submit_click_ms = timeouts.get(
        "submit_prompt_click_ms", DEFAULT_TIMEOUTS.get("submit_prompt_click_ms")
    )
    enable_wait_ms = timeouts.get(
        "submit_template_enable_ms", DEFAULT_TIMEOUTS.get("submit_for_judging_enable_ms")
    )
    try_again_button_click_ms = timeouts.get(
        "intent_button_click_ms", DEFAULT_TIMEOUTS.get("intent_button_click_ms")
    )

    textarea_selector = (
        'textarea[placeholder^="Write your injection intent directly"]'
    )
    submit_button_selector = 'button:has-text("Submit Template")'
    try_again_button_selector = 'button:has-text("Try Again")'

    attempt_count = 0
    
    while attempt_count < max_retries:
        attempt_count += 1
        logging.info(f"Starting attempt {attempt_count}/{max_retries}")

        try:
            # Fill the intent textarea
            logging.info("Filling intent textarea for agent-track-submit")
            textarea = self.page.locator(textarea_selector)
            await textarea.wait_for(state="visible", timeout=prompt_visible_ms)
            await textarea.fill(text)

            # Submit the template
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

            # Wait for the "Try Again" button to appear
            logging.info("Waiting for 'Try Again' button to appear")
            try_again_button = self.page.locator(try_again_button_selector)
            
            # Wait for the button to be visible
            await try_again_button.wait_for(state="visible", timeout=prompt_visible_ms)
            
            # Check if we've reached max retries
            if attempt_count >= max_retries:
                logging.info(f"Reached maximum retries ({max_retries}). Stopping.")
                break
            
            # Click the "Try Again" button
            logging.info(f"Clicking 'Try Again' button (attempt {attempt_count})")
            await try_again_button.click(timeout=try_again_button_click_ms)
            
            # Apply delay between attempts
            if random_delay:
                delay = random.uniform(delay_min_sec, delay_max_sec)
            else:
                delay = delay_min_sec
            
            logging.info(f"Waiting {delay:.2f} seconds before next attempt")
            await self.page.wait_for_timeout(delay * 1000)
            
        except Exception as e:
            logging.error(f"Error during attempt {attempt_count}: {str(e)}")
            if attempt_count >= max_retries:
                logging.error(f"Reached maximum retries ({max_retries}). Stopping due to error.")
                break
            
            # Wait before retrying on error
            if random_delay:
                delay = random.uniform(delay_min_sec, delay_max_sec)
            else:
                delay = delay_min_sec
            
            logging.info(f"Waiting {delay:.2f} seconds before retrying after error")
            await self.page.wait_for_timeout(delay * 1000)

    logging.info(f"Completed agent_track_submit_with_retry after {attempt_count} attempts")
