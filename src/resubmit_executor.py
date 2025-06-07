import random
import asyncio
from playwright.async_api import Page, Locator
import os

async def _perform_delay(should_delay, min_sec, max_sec, page: Page):
    """Waits for a random duration within the specified range."""
    if not should_delay:
        return
    delay = random.uniform(min_sec, max_sec)
    print(f"   ...waiting for {delay:.2f} seconds...")
    await page.wait_for_timeout(delay * 1000)

async def execute_resubmit_loop(page: Page, challenge_config: dict, automation_settings: dict):
    """Executes a loop of submitting for judging."""
    if not page or not challenge_config:
        print("Error: Page object or challenge_config missing for execute_resubmit_loop.")
        return

    submit_for_judging_button_selector = challenge_config.get("submit_for_judging_button")
    challenge_name = challenge_config.get("challenge_name", "unknown_challenge")

    random_delay = automation_settings.get('random_delay', True)
    delay_min_sec = automation_settings.get('delay_min_sec', 5)
    delay_max_sec = automation_settings.get('delay_max_sec', 60)

    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)

    if not submit_for_judging_button_selector:
        print("Error: Missing submit_for_judging_button selector in challenge_config.")
        return

    print(f"\n--- Starting Resubmission Loop for '{challenge_name}' ---")
    
    submission_count = 0
    while True:
        submission_count += 1
        print(f"\n--- Attempt #{submission_count} ---")
        try:
            submit_judging_button: Locator = page.locator(submit_for_judging_button_selector)
            
            print(f"1. Waiting for '{submit_for_judging_button_selector}' to be ready...")
            try:
                await submit_judging_button.wait_for(state="visible", timeout=10000)
                await submit_judging_button.wait_for(state="enabled", timeout=180000)
                print("   'Submit for Judging' button is ready.")
            except Exception as e:
                print(f"   Timeout or error waiting for 'Submit for Judging' button: {e}")
                print("   Will attempt to click anyway...")

            print(f"2. Clicking 'Submit for Judging' button ('{submit_for_judging_button_selector}')...")
            await submit_judging_button.click(timeout=5000)
            print("   Clicked 'Submit for Judging' button.")

            await _perform_delay(random_delay, delay_min_sec, delay_max_sec, page)

            success_selector = 'h2:has-text("Challenge Conquered! 🎉")'
            if await page.locator(success_selector).is_visible(timeout=5000):
                print("🏆 Challenge Conquered! Stopping resubmission loop.")
                break

            continue_chat_button_selector = "button:has-text('Continue Current Chat')"
            continue_chat_button = page.locator(continue_chat_button_selector)
            
            if await continue_chat_button.is_visible(timeout=5000):
                print("   'Not Quite There Yet' popup detected. Clicking 'Continue Current Chat'.")
                await continue_chat_button.click(timeout=5000)
                print("   Clicked 'Continue Current Chat' button. Waiting before next attempt.")
            else:
                # If neither success nor continue is found, maybe there's another state.
                # Or maybe the button click didn't open a popup.
                # We can check if the judging button is gone or disabled as a sign of submission processing.
                if not await submit_judging_button.is_visible(timeout=2000):
                    print("   'Submit for Judging' button is no longer visible. Waiting for it to reappear for the next attempt.")
                else:
                    print("   Neither success nor 'Continue Current Chat' popup detected. Assuming page is ready for another submission attempt after delay.")

            await _perform_delay(random_delay, delay_min_sec, delay_max_sec, page)

        except Exception as e:
            print(f"   An error occurred during submission attempt #{submission_count}: {e}")
            screenshot_path = os.path.join(screenshots_dir, f"error_resubmit_loop_{challenge_name}_{submission_count}.png")
            try:
                await page.screenshot(path=screenshot_path)
                print(f"   Screenshot saved to {screenshot_path}")
            except Exception as se:
                print(f"   Could not take screenshot: {se}")
            print("   Waiting before trying again...")
            await _perform_delay(True, delay_min_sec, delay_max_sec, page) 