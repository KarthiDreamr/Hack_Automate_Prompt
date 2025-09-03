import asyncio
import argparse
import logging
import os
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
    # Determine default text from config's prompts section (file path), if available
    default_text = "Test injection intent"
    try:
        cfg = load_config()
        prompts_cfg = (cfg or {}).get("prompts", [])
        if isinstance(prompts_cfg, list) and prompts_cfg:
            first_item = prompts_cfg[0] or {}
            rel_path = first_item.get("file")
            if isinstance(rel_path, str) and rel_path.strip():
                # Resolve path relative to this package directory
                base_dir = os.path.dirname(__file__)
                prompt_path = os.path.join(base_dir, rel_path)
                with open(prompt_path, "r", encoding="utf-8") as f:
                    default_text = f.read()
    except Exception:
        # Fallback to the static default_text if anything goes wrong
        pass

    parser = argparse.ArgumentParser(description="MATS x Trails Automation Tool")
    parser.add_argument("--launch-browser", action="store_true")
    parser.add_argument("--text", type=str, default=default_text)
    parser.add_argument("--model", type=str, default=None)
    args = parser.parse_args()
    connect_to_existing = not args.launch_browser
    await run_agent_track_submit_retry(connect_to_existing, args.text, args.model)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    asyncio.run(main())


