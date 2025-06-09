import asyncio
import argparse
import logging
from playwright.async_api import async_playwright

from .config_loader import load_config
from .browser import BrowserManager
from .challenge_executor import ChallengeExecutor


async def run_challenge_automation(connect_to_existing_browser: bool = True):
    """Orchestrates the automation for a given challenge."""
    config = load_config()
    if not config:
        return

    automation_settings = config.get("automation_settings", {})

    async with async_playwright() as playwright:
        browser_manager = BrowserManager(playwright)
        try:
            page = await browser_manager.get_page(
                connect_to_existing=connect_to_existing_browser
            )

            if not page:
                print("Failed to initialize browser or page. Exiting.")
                return

            executor = ChallengeExecutor(page, config, automation_settings)
            await executor.run()
        except asyncio.CancelledError:
            logging.info("Challenge automation cancelled.")
        except Exception as e:
            print(f"An unexpected error occurred in run_challenge_automation: {e}")
        finally:
            # The browser cleanup logic has been removed to allow manual closing.
            print("Automation run finished.")


async def run_judging_loop_automation(connect_to_existing_browser: bool = True):
    """Orchestrates the judging loop automation."""
    config = load_config()
    if not config:
        return

    automation_settings = config.get("automation_settings", {})

    async with async_playwright() as playwright:
        browser_manager = BrowserManager(playwright)
        try:
            page = await browser_manager.get_page(
                connect_to_existing=connect_to_existing_browser
            )

            if not page:
                print("Failed to initialize browser or page. Exiting.")
                return

            executor = ChallengeExecutor(page, config, automation_settings)
            await executor.run_judging_loop()
        except asyncio.CancelledError:
            logging.info("Judging loop cancelled.")
        except Exception as e:
            print(f"An unexpected error occurred in judging loop automation: {e}")
        finally:
            # The browser cleanup logic has been removed to allow manual closing.
            print("Judging loop finished.")


async def main():
    parser = argparse.ArgumentParser(description="Hack-a-Prompt 2.0 Automation Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'run' command
    run_parser = subparsers.add_parser(
        "run", help="Run the full automation loop (input, submit, judge)."
    )
    run_parser.add_argument(
        "--launch-browser",
        action="store_true",
        help="Launch a new browser instance instead of connecting to an existing one.",
    )

    # 'judge' command
    judge_parser = subparsers.add_parser(
        "judge", help="Run only the judging loop (submit for judging, continue)."
    )
    judge_parser.add_argument(
        "--launch-browser",
        action="store_true",
        help="Launch a new browser instance instead of connecting to an existing one.",
    )

    args = parser.parse_args()

    connect_to_existing = not args.launch_browser

    if args.command == "run":
        await run_challenge_automation(connect_to_existing)
    elif args.command == "judge":
        await run_judging_loop_automation(connect_to_existing)


if __name__ == "__main__":
    # This allows running the script directly from the command line, e.g., python -m src.app
    # The project root should be in PYTHONPATH.
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(main())
    finally:
        tasks = asyncio.all_tasks(loop=loop)
        for task in tasks:
            task.cancel()
        group = asyncio.gather(*tasks, return_exceptions=True)
        loop.run_until_complete(group)
        loop.close()
        logging.info("Event loop closed.")
