import asyncio
import argparse
import logging
from playwright.async_api import async_playwright

from .config_loader import load_config
from ..browser import BrowserManager
from . import ChallengeExecutor


async def run_all(connect_to_existing_browser: bool = True):
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
        executor = ChallengeExecutor(page, config, automation_settings)
        await executor.run()


async def run_judge(connect_to_existing_browser: bool = True):
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
        executor = ChallengeExecutor(page, config, automation_settings)
        await executor.run_judging_loop()


async def run_intent(connect_to_existing_browser: bool = True):
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
        executor = ChallengeExecutor(page, config, automation_settings)
        await executor.run_intent_loop_2()


async def main():
    parser = argparse.ArgumentParser(description="CBRNE Automation Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for cmd in ("run", "judge", "run-intent"):
        p = subparsers.add_parser(cmd)
        p.add_argument("--launch-browser", action="store_true")

    args = parser.parse_args()
    connect_to_existing = not args.launch_browser
    if args.command == "run":
        await run_all(connect_to_existing)
    elif args.command == "judge":
        await run_judge(connect_to_existing)
    elif args.command == "run-intent":
        await run_intent(connect_to_existing)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    asyncio.run(main())


