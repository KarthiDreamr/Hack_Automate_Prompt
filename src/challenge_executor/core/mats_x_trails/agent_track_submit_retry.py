import logging
import time
import random
import yaml
import os
from ...config import DEFAULT_TIMEOUTS


def load_task_config(config_path: str = None) -> dict:
    """Load task-specific configuration from the config file."""
    if config_path is None:
        # Default path relative to the script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "config.yaml")
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            return config.get("agent_track_submit", {})
    except FileNotFoundError:
        logging.warning(f"Task config file not found at {config_path}, using defaults")
        return {}
    except Exception as e:
        logging.error(f"Error loading task config: {e}, using defaults")
        return {}


async def agent_track_submit(self, text: str, timeouts: dict | None = None):
    if timeouts is None:
        timeouts = {}

    # Load task-specific configuration
    task_config = load_task_config()
    task_timeouts = task_config.get("timeouts", {})
    task_selectors = task_config.get("selectors", {})
    task_logging = task_config.get("logging", {})

    prompt_visible_ms = timeouts.get(
        "prompt_visible_ms", 
        task_timeouts.get("prompt_visible_ms", DEFAULT_TIMEOUTS.get("prompt_visible_ms"))
    )
    submit_click_ms = timeouts.get(
        "submit_prompt_click_ms", 
        task_timeouts.get("submit_prompt_click_ms", DEFAULT_TIMEOUTS.get("submit_prompt_click_ms"))
    )
    enable_wait_ms = timeouts.get(
        "submit_template_enable_ms", 
        task_timeouts.get("submit_template_enable_ms", DEFAULT_TIMEOUTS.get("submit_for_judging_enable_ms"))
    )

    textarea_selector = task_selectors.get(
        "textarea", 
        'textarea'
    )
    submit_button_selector = task_selectors.get(
        "submit_button", 
        'button:has-text("Submit Template")'
    )

    logging.info(task_logging.get("filling_textarea", "Filling intent textarea for agent-track-submit"))
    textarea = self.page.locator(textarea_selector)
    await textarea.wait_for(state="visible", timeout=prompt_visible_ms)
    await textarea.fill(text)

    logging.info(task_logging.get("waiting_submit_button", "Waiting for 'Submit Template' button to enable, then clicking"))
    submit_button = self.page.locator(submit_button_selector)
    await submit_button.wait_for(state="visible", timeout=prompt_visible_ms)

    start_time = time.time()
    polling_interval = task_timeouts.get("polling_interval_ms", 200)
    enable_wait_fallback = task_timeouts.get("enable_wait_fallback_ms", 30000)
    while True:
        try:
            if not await submit_button.is_disabled():
                break
        except Exception:
            pass
        if (time.time() - start_time) * 1000 > (enable_wait_ms or enable_wait_fallback):
            logging.warning(task_logging.get("button_timeout_warning", "'Submit Template' button did not enable within timeout; attempting click anyway"))
            break
        await self.page.wait_for_timeout(polling_interval)

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

    # Load task-specific configuration
    task_config = load_task_config()
    task_retry_settings = task_config.get("retry_settings", {})
    task_timeouts = task_config.get("timeouts", {})
    task_selectors = task_config.get("selectors", {})
    task_logging = task_config.get("logging", {})

    # Get configuration settings
    max_retries = config.get("max_retries", task_retry_settings.get("max_retries", 1000))
    delay_min_sec = config.get("delay_min_sec", task_retry_settings.get("delay_min_sec", 4))
    delay_max_sec = config.get("delay_max_sec", task_retry_settings.get("delay_max_sec", 12))
    random_delay = config.get("random_delay", task_retry_settings.get("random_delay", False))
    
    # Get timeout settings
    prompt_visible_ms = timeouts.get(
        "prompt_visible_ms", 
        task_timeouts.get("prompt_visible_ms", DEFAULT_TIMEOUTS.get("prompt_visible_ms"))
    )
    submit_click_ms = timeouts.get(
        "submit_prompt_click_ms", 
        task_timeouts.get("submit_prompt_click_ms", DEFAULT_TIMEOUTS.get("submit_prompt_click_ms"))
    )
    enable_wait_ms = timeouts.get(
        "submit_template_enable_ms", 
        task_timeouts.get("submit_template_enable_ms", DEFAULT_TIMEOUTS.get("submit_for_judging_enable_ms"))
    )
    try_again_button_visible_ms = timeouts.get(
        "try_again_button_visible_ms", 
        task_timeouts.get("try_again_button_visible_ms", 90000)
    )
    try_again_button_click_ms = timeouts.get(
        "intent_button_click_ms", 
        task_timeouts.get("try_again_button_click_ms", DEFAULT_TIMEOUTS.get("intent_button_click_ms"))
    )

    textarea_selector = task_selectors.get(
        "textarea", 
        'textarea'
    )
    submit_button_selector = task_selectors.get(
        "submit_button", 
        'button:has-text("Submit Template")'
    )
    try_again_button_selector = task_selectors.get(
        "try_again_button", 
        'button:has-text("Try Again")'
    )

    attempt_count = 0
    
    while attempt_count < max_retries:
        attempt_count += 1
        logging.info(task_logging.get("starting_attempt", "Starting attempt {attempt}/{max_retries}").format(
            attempt=attempt_count, max_retries=max_retries
        ))

        try:
            # Fill the intent textarea
            logging.info(task_logging.get("filling_textarea", "Filling intent textarea for agent-track-submit"))
            textarea = self.page.locator(textarea_selector)
            await textarea.wait_for(state="visible", timeout=prompt_visible_ms)
            await textarea.fill(text)

            # Submit the template
            logging.info(task_logging.get("waiting_submit_button", "Waiting for 'Submit Template' button to enable, then clicking"))
            submit_button = self.page.locator(submit_button_selector)
            await submit_button.wait_for(state="visible", timeout=prompt_visible_ms)

            start_time = time.time()
            polling_interval = task_timeouts.get("polling_interval_ms", 200)
            enable_wait_fallback = task_timeouts.get("enable_wait_fallback_ms", 30000)
            while True:
                try:
                    if not await submit_button.is_disabled():
                        break
                except Exception:
                    pass
                if (time.time() - start_time) * 1000 > (enable_wait_ms or enable_wait_fallback):
                    logging.warning(task_logging.get("button_timeout_warning", "'Submit Template' button did not enable within timeout; attempting click anyway"))
                    break
                await self.page.wait_for_timeout(polling_interval)

            await submit_button.click(timeout=submit_click_ms)

            # Wait for the "Try Again" button to appear
            logging.info(task_logging.get("waiting_try_again", "Waiting for 'Try Again' button to appear"))
            try_again_button = self.page.locator(try_again_button_selector)
            
            # Wait for the button to be visible with extended timeout
            await try_again_button.wait_for(state="visible", timeout=try_again_button_visible_ms)
            
            # Check if we've reached max retries
            if attempt_count >= max_retries:
                logging.info(task_logging.get("reached_max_retries", "Reached maximum retries ({max_retries}). Stopping.").format(
                    max_retries=max_retries
                ))
                break
            
            # Click the "Try Again" button
            logging.info(task_logging.get("clicking_try_again", "Clicking 'Try Again' button (attempt {attempt})").format(
                attempt=attempt_count
            ))
            await try_again_button.click(timeout=try_again_button_click_ms)
            
            # Apply delay between attempts
            if random_delay:
                delay = random.uniform(delay_min_sec, delay_max_sec)
            else:
                delay = delay_min_sec
            
            logging.info(task_logging.get("waiting_before_next", "Waiting {delay:.2f} seconds before next attempt").format(
                delay=delay
            ))
            await self.page.wait_for_timeout(delay * 1000)
            
        except Exception as e:
            logging.error(task_logging.get("error_during_attempt", "Error during attempt {attempt}: {error}").format(
                attempt=attempt_count, error=str(e)
            ))
            if attempt_count >= max_retries:
                logging.error(task_logging.get("error_max_retries", "Reached maximum retries ({max_retries}). Stopping due to error.").format(
                    max_retries=max_retries
                ))
                break
            
            # Wait before retrying on error
            if random_delay:
                delay = random.uniform(delay_min_sec, delay_max_sec)
            else:
                delay = delay_min_sec
            
            logging.info(task_logging.get("waiting_after_error", "Waiting {delay:.2f} seconds before retrying after error").format(
                delay=delay
            ))
            await self.page.wait_for_timeout(delay * 1000)

    logging.info(task_logging.get("completed_retry", "Completed agent_track_submit_with_retry after {attempts} attempts").format(
        attempts=attempt_count
    ))
