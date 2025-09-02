import asyncio
import argparse
import logging
from playwright.async_api import async_playwright

from .config_loader import load_config
from ..browser import BrowserManager
from .agent_track_submit_retry import agent_track_submit_with_retry


async def run_agent_track_submit_retry(connect_to_existing_browser: bool = True, text: str = "", model: str = None):
    config = load_config()
    if not config:
        return
    automation_settings = config.get("automation_settings", {})
    async with async_playwright() as playwright:
        browser_manager = BrowserManager(playwright, config)
        page = await browser_manager.get_page(connect_to_existing=connect_to_existing_browser)
        if not page:
            print("Failed to initialize browser or page. Exiting.")
            return
        class Dummy:
            def __init__(self, page, config, automation_settings):
                self.page = page
                self.config = config
                self.automation_settings = automation_settings
        ctx = Dummy(page, config, automation_settings)
        await agent_track_submit_with_retry(ctx, text, model, automation_settings.get("timeouts", {}))


async def main():
    parser = argparse.ArgumentParser(description="MATS x Trails Automation Tool")
    parser.add_argument("--launch-browser", action="store_true")
    parser.add_argument("--text", type=str, default="Test injection intent")
    parser.add_argument("--model", type=str, default=None)
    args = parser.parse_args()
    connect_to_existing = not args.launch_browser
    await run_agent_track_submit_retry(connect_to_existing, args.text, args.model)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    asyncio.run(main())


