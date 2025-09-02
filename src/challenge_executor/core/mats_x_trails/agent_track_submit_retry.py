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


async def select_model_from_dropdown(self, model_name: str, timeouts: dict | None = None, config: dict | None = None):
    """
    Select a specific model from the dropdown menu.
    This function opens the dropdown, finds the specified model, and selects it.
    """
    if timeouts is None:
        timeouts = {}
    if config is None:
        config = {}

    # Load task-specific configuration
    task_config = load_task_config()
    task_timeouts = task_config.get("timeouts", {})
    task_selectors = task_config.get("selectors", {})
    task_logging = task_config.get("logging", {})

    # Get timeout settings (no hardcoded fallbacks; use task or global defaults)
    dropdown_open_ms = timeouts.get(
        "dropdown_open_ms",
        task_timeouts.get("dropdown_open_ms", DEFAULT_TIMEOUTS.get("dropdown_open_ms"))
    )
    dropdown_item_click_ms = timeouts.get(
        "dropdown_item_click_ms",
        task_timeouts.get("dropdown_item_click_ms", DEFAULT_TIMEOUTS.get("dropdown_item_click_ms"))
    )
    aria_poll_ms = timeouts.get(
        "dropdown_aria_expanded_poll_ms",
        task_timeouts.get("dropdown_aria_expanded_poll_ms", DEFAULT_TIMEOUTS.get("dropdown_aria_expanded_poll_ms"))
    )
    aria_max_checks = timeouts.get(
        "dropdown_aria_expanded_max_checks",
        task_timeouts.get("dropdown_aria_expanded_max_checks", DEFAULT_TIMEOUTS.get("dropdown_aria_expanded_max_checks"))
    )
    post_selection_wait_ms = timeouts.get(
        "post_selection_wait_ms",
        task_timeouts.get("post_selection_wait_ms", DEFAULT_TIMEOUTS.get("post_selection_wait_ms"))
    )

    # Get selector settings - use the working selectors we discovered
    dropdown_button_selector = task_selectors.get(
        "dropdown_button", 
        'button[aria-haspopup="menu"][data-state="closed"]:not([data-testid="user-menu-trigger"])'
    )
    dropdown_menu_selector = task_selectors.get(
        "dropdown_menu", 
        'div[role="menu"]'
    )
    raw_model_item_selector = task_selectors.get(
        "model_item", 
        'div[role="menuitem"]:has-text("{model_name}")'
    )
    # Interpolate model name if the selector template contains a placeholder
    model_item_selector = raw_model_item_selector.format(model_name=model_name)
    dropdown_button_fallbacks: list[str] = task_selectors.get(
        "dropdown_button_fallbacks",
        [
            'button:has(svg.lucide-bot):has(svg.lucide-chevron-down):not([data-testid="user-menu-trigger"])',
            'button[aria-haspopup="menu"]:not([data-testid="user-menu-trigger"])',
        ],
    )

    try:
        logging.info(task_logging.get("selecting_model", f"Selecting model: {model_name}").format(model_name=model_name))
        
        # Strategy 1: Try the primary selector, then configured fallbacks
        dropdown_button = self.page.locator(dropdown_button_selector)
        if await dropdown_button.count() == 0:
            for fallback in dropdown_button_fallbacks:
                candidate = self.page.locator(fallback)
                if await candidate.count() > 0:
                    dropdown_button = candidate
                    break
        
        if await dropdown_button.count() == 0:
            logging.error(task_logging.get("model_selection_error", f"Could not find model dropdown button").format(model_name=model_name, error="No dropdown button found"))
            return
        
        # Use the first found button
        button = dropdown_button.first
        button_text = await button.text_content()
        logging.info(task_logging.get("found_dropdown_button", f"Found dropdown button: {button_text[:50]}...").format(preview=(button_text or "").strip()[:50]))
        
        # Find and click the dropdown button to open it
        await button.wait_for(state="visible", timeout=dropdown_open_ms)
        await button.click()
        
        # Wait for dropdown to indicate it is open (aria-expanded=true) or the menu to appear
        # Poll aria-expanded on the same button while also waiting for menu
        try:
            for _ in range(int(aria_max_checks)):
                expanded = await button.get_attribute('aria-expanded')
                if expanded == 'true':
                    break
                await self.page.wait_for_timeout(int(aria_poll_ms))
        except Exception:
            pass
        
        # Wait for the dropdown menu to appear
        dropdown_menu = self.page.locator(dropdown_menu_selector)
        await dropdown_menu.wait_for(state="visible", timeout=dropdown_open_ms)
        
        # Scope the search to the opened dropdown menu only
        model_item = dropdown_menu.locator(model_item_selector)
        await model_item.wait_for(state="visible", timeout=dropdown_open_ms)
        await model_item.scroll_into_view_if_needed()
        await model_item.click(timeout=dropdown_item_click_ms)
        
        # Wait a moment for the selection to take effect and menu to close
        await self.page.wait_for_timeout(int(post_selection_wait_ms))
        
        logging.info(task_logging.get("model_selected", f"Successfully selected model: {model_name}").format(model_name=model_name))
        
    except Exception as e:
        logging.error(task_logging.get("model_selection_error", f"Error selecting model {model_name}: {str(e)}").format(model_name=model_name, error=str(e)))
        # Continue execution even if model selection fails
        pass


async def agent_track_submit_with_retry(self, text: str, model_name: str = None, timeouts: dict | None = None, config: dict | None = None):
    """
    Enhanced version of agent_track_submit that continues looping with "Try Again" button
    until max_retries is reached according to config.yaml settings.
    Now includes model selection from dropdown before each attempt.
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
    refresh_on_timeout = config.get("refresh_on_timeout", task_retry_settings.get("refresh_on_timeout", False))
    refresh_timeout_sec = config.get("refresh_timeout_sec", task_retry_settings.get("refresh_timeout_sec", 30))
    
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
        task_timeouts.get("try_again_button_visible_ms", DEFAULT_TIMEOUTS.get("try_again_button_visible_ms"))
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
            # Select model from dropdown first (if model_name is provided)
            if model_name:
                await select_model_from_dropdown(self, model_name, timeouts, config)
            
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
            polling_interval = task_timeouts.get("polling_interval_ms", DEFAULT_TIMEOUTS.get("polling_interval_ms"))
            enable_wait_fallback = task_timeouts.get("enable_wait_fallback_ms", DEFAULT_TIMEOUTS.get("enable_wait_fallback_ms"))
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
            
            if refresh_on_timeout:
                # Use refresh timeout instead of waiting for Try Again button
                logging.info(task_logging.get("refresh_timeout_reached", f"Refresh timeout reached, refreshing page instead of waiting for Try Again button"))
                await self.page.wait_for_timeout(refresh_timeout_sec * 1000)
                await self.page.reload()
                logging.info(task_logging.get("page_refreshed", "Page refreshed successfully, continuing with next attempt"))
                # Small delay after refresh to ensure page loads properly
                await self.page.wait_for_timeout(task_timeouts.get("post_refresh_wait_ms", DEFAULT_TIMEOUTS.get("post_refresh_wait_ms")))
            else:
                # Wait for the button to be visible with extended timeout
                await try_again_button.wait_for(state="visible", timeout=try_again_button_visible_ms)
            
            # Check if we've reached max retries
            if attempt_count >= max_retries:
                logging.info(task_logging.get("reached_max_retries", "Reached maximum retries ({max_retries}). Stopping.").format(
                    max_retries=max_retries
                ))
                break
            
            if not refresh_on_timeout:
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
