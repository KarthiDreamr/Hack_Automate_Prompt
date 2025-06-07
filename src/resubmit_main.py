import asyncio
from playwright.async_api import async_playwright

from config_loader import load_config, get_challenge_config
from browser_manager import get_browser_page
from resubmit_executor import execute_resubmit_loop

async def run_resubmission(challenge_name: str, connect_to_existing_browser: bool = True):
    """Orchestrates the resubmission automation for a given challenge."""
    main_config = load_config()
    if not main_config:
        return

    automation_settings = main_config.get("automation_settings", {})
    challenge_config = get_challenge_config(main_config, challenge_name)
    if not challenge_config:
        return
    
    challenge_config['challenge_name'] = challenge_name 

    async with async_playwright() as playwright:
        browser, page = await get_browser_page(playwright, connect_to_existing=connect_to_existing_browser)

        if not page or not browser:
            print("Failed to initialize browser or page. Exiting.")
            if browser and browser.is_connected():
                 await browser.close()
            return
        
        try:
            # Make sure we are on the right page
            base_url = main_config.get("base_url")
            if base_url and base_url not in page.url:
                print(f"Navigating to challenge page: {base_url}")
                await page.goto(base_url, wait_until="networkidle")

            await execute_resubmit_loop(page, challenge_config, automation_settings)
        except Exception as e:
            print(f"An unexpected error occurred in run_resubmission: {e}")
        finally:
            if browser.is_connected():
                print("Closing browser connection...")
                await browser.close()
            print("Resubmission run finished.")

async def main():
    challenge_to_run = "getting_started"
    connect_to_existing = True

    await run_resubmission(challenge_to_run, connect_to_existing)

if __name__ == "__main__":
    asyncio.run(main()) 