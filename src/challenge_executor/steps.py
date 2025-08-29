import logging
from playwright.async_api import Page


async def navigate_to_challenge(page: Page, base_url: str):
    if base_url not in page.url:
        logging.info(f"Navigating to {base_url}...")
        await page.goto(base_url)
    else:
        logging.info(f"Already on page {base_url}")


async def fill_prompt_and_submit(
    page: Page, prompt_selector: str, submit_selector: str, prompt_text: str, timeouts: dict | None = None
):
    if timeouts is None:
        timeouts = {}

    from ..config_loader import load_config
    _CFG = load_config() or {}
    _AUTOMATION_SETTINGS = _CFG.get("automation_settings", {})
    _DEFAULT_TIMEOUTS = _AUTOMATION_SETTINGS.get("timeouts", {})

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


async def submit_for_judging(page: Page, submit_judging_selector: str, timeouts: dict | None = None):
    if timeouts is None:
        timeouts = {}

    from ..config_loader import load_config
    _CFG = load_config() or {}
    _AUTOMATION_SETTINGS = _CFG.get("automation_settings", {})
    _DEFAULT_TIMEOUTS = _AUTOMATION_SETTINGS.get("timeouts", {})

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


async def check_for_success(page: Page, timeouts: dict | None = None) -> bool:
    if timeouts is None:
        timeouts = {}

    from ..config_loader import load_config
    _CFG = load_config() or {}
    _AUTOMATION_SETTINGS = _CFG.get("automation_settings", {})
    _DEFAULT_TIMEOUTS = _AUTOMATION_SETTINGS.get("timeouts", {})

    success_visible_ms = timeouts.get(
        "success_visible_ms", _DEFAULT_TIMEOUTS.get("success_visible_ms")
    )

    success_selector = 'h2:has-text("Challenge Conquered! 🎉")'
    success_element = page.locator(success_selector)
    if await success_element.is_visible(timeout=success_visible_ms):
        logging.info("Challenge Conquered! 🎉")
        return True
    return False


async def handle_failure_and_restart(page: Page, timeouts: dict | None = None) -> bool:
    if timeouts is None:
        timeouts = {}

    from ..config_loader import load_config
    _CFG = load_config() or {}
    _AUTOMATION_SETTINGS = _CFG.get("automation_settings", {})
    _DEFAULT_TIMEOUTS = _AUTOMATION_SETTINGS.get("timeouts", {})

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
        from .utils import take_screenshot
        await take_screenshot(page, "failure_popup_no_restart_button")
        return False


async def handle_judging_failure(page: Page, timeouts: dict | None = None) -> bool:
    if timeouts is None:
        timeouts = {}

    from ..config_loader import load_config
    _CFG = load_config() or {}
    _AUTOMATION_SETTINGS = _CFG.get("automation_settings", {})
    _DEFAULT_TIMEOUTS = _AUTOMATION_SETTINGS.get("timeouts", {})

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
        from .utils import take_screenshot
        await take_screenshot(page, "failure_popup_no_continue_button")
        return False


