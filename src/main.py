import asyncio
from playwright.async_api import async_playwright

from config_loader import load_config, get_challenge_config
from browser_manager import get_browser_page
from challenge_executor import execute_interaction_test

async def run_challenge_automation(challenge_name: str, connect_to_existing_browser: bool = True):
    """Orchestrates the automation for a given challenge."""
    main_config = load_config()
    if not main_config:
        return

    challenge_config = get_challenge_config(main_config, challenge_name)
    if not challenge_config:
        return
    # Add challenge_name to the config dict for use in executor logging/screenshots
    challenge_config['challenge_name'] = challenge_name 

    async with async_playwright() as playwright:
        browser, page = await get_browser_page(playwright, connect_to_existing=connect_to_existing_browser)

        if not page or not browser: # Ensure page and browser are not None
            print("Failed to initialize browser or page. Exiting.")
            if browser and browser.is_connected():
                 await browser.close()
            return
        
        try:
            await execute_interaction_test(page, challenge_config)
        except Exception as e:
            print(f"An unexpected error occurred in run_challenge_automation: {e}")
        finally:
            if browser.is_connected():
                print("Closing browser connection (disconnecting if CDP, closing if launched)...")
                await browser.close()
            print("Automation run finished.")

async def main():
    # Configuration
    challenge_to_run = "getting_started"  # Or get this from CLI args, etc.
    connect_to_existing = True # Set to False to launch a new browser instance

    await run_challenge_automation(challenge_to_run, connect_to_existing)

if __name__ == "__main__":
    asyncio.run(main()) 