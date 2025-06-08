import asyncio
import argparse
import signal
import sys
import logging
from playwright.async_api import async_playwright

from .config_loader import load_config, get_challenge_config
from .browser import BrowserManager
from .challenge_executor import ChallengeExecutor


async def shutdown(signal, loop):
    """Gracefully stop all running tasks."""
    logging.info(f"Received exit signal {signal.name}...")

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]

    logging.info("Cancelling tasks...")
    await asyncio.gather(*tasks, return_exceptions=True)
    # loop.stop() # This is not needed and can cause issues.


async def run_challenge_automation(
    challenge_name: str, connect_to_existing_browser: bool = True
):
    """Orchestrates the automation for a given challenge."""
    main_config = load_config()
    if not main_config:
        return

    automation_settings = main_config.get("automation_settings", {})
    challenge_config = get_challenge_config(main_config, challenge_name)
    if not challenge_config:
        return
    # Add challenge_name to the config dict for use in executor logging/screenshots
    challenge_config["challenge_name"] = challenge_name

    async with async_playwright() as playwright:
        browser_manager = BrowserManager(playwright)
        try:
            page = await browser_manager.get_page(
                connect_to_existing=connect_to_existing_browser
            )

            if not page:
                print("Failed to initialize browser or page. Exiting.")
                return

            executor = ChallengeExecutor(page, challenge_config, automation_settings)
            await executor.run()
        except asyncio.CancelledError:
            logging.info("Challenge automation cancelled.")
        except Exception as e:
            print(f"An unexpected error occurred in run_challenge_automation: {e}")
        finally:
            try:
                if browser_manager.browser_process:
                    browser_manager.cleanup_browser()
                elif browser_manager.browser and browser_manager.browser.is_connected():
                    print("Closing browser connection...")
                    await browser_manager.browser.close()
            except asyncio.CancelledError:
                pass  # Ignore cancellation errors during cleanup
            print("Automation run finished.")


async def run_judging_loop_automation(
    challenge_name: str, connect_to_existing_browser: bool = True
):
    """Orchestrates the judging loop automation for a given challenge."""
    main_config = load_config()
    if not main_config:
        return

    automation_settings = main_config.get("automation_settings", {})
    challenge_config = get_challenge_config(main_config, challenge_name)
    if not challenge_config:
        return
    challenge_config["challenge_name"] = challenge_name

    async with async_playwright() as playwright:
        browser_manager = BrowserManager(playwright)
        try:
            page = await browser_manager.get_page(
                connect_to_existing=connect_to_existing_browser
            )

            if not page:
                print("Failed to initialize browser or page. Exiting.")
                return

            executor = ChallengeExecutor(page, challenge_config, automation_settings)
            await executor.run_judging_loop()
        except asyncio.CancelledError:
            logging.info("Judging loop cancelled.")
        except Exception as e:
            print(f"An unexpected error occurred in judging loop automation: {e}")
        finally:
            try:
                if browser_manager.browser_process:
                    browser_manager.cleanup_browser()
                elif browser_manager.browser and browser_manager.browser.is_connected():
                    print("Closing browser connection...")
                    await browser_manager.browser.close()
            except asyncio.CancelledError:
                pass  # Ignore cancellation errors during cleanup
            print("Judging loop finished.")


async def run_resubmission_automation(
    submission_id: str, connect_to_existing_browser: bool = True
):
    """Orchestrates the resubmission automation for a given submission ID."""
    main_config = load_config()
    if not main_config:
        return

    automation_settings = main_config.get("automation_settings", {})
    # For resubmission, we don't need a specific challenge config,
    # but the executor expects one. We can create a minimal one.
    challenge_config = {"challenge_name": f"resubmission_{submission_id}"}
    challenge_config.update(main_config)

    async with async_playwright() as playwright:
        browser_manager = BrowserManager(playwright)
        try:
            page = await browser_manager.get_page(
                connect_to_existing=connect_to_existing_browser
            )

            if not page:
                print("Failed to initialize browser or page. Exiting.")
                return

            executor = ChallengeExecutor(page, challenge_config, automation_settings)
            await executor.run_resubmission_loop(submission_id)
        except asyncio.CancelledError:
            logging.info("Resubmission automation cancelled.")
        except Exception as e:
            print(f"An unexpected error occurred in resubmission automation: {e}")
        finally:
            try:
                if browser_manager.browser_process:
                    browser_manager.cleanup_browser()
                elif browser_manager.browser and browser_manager.browser.is_connected():
                    print("Closing browser connection...")
                    await browser_manager.browser.close()
            except asyncio.CancelledError:
                pass  # Ignore cancellation errors during cleanup
            print("Resubmission finished.")


async def main():
    parser = argparse.ArgumentParser(description="Hack-a-Prompt 2.0 Automation Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'run' command
    run_parser = subparsers.add_parser(
        "run", help="Run the full challenge automation loop."
    )
    run_parser.add_argument(
        "challenge",
        nargs="?",
        default="getting_started",
        help="The name of the challenge to run.",
    )
    run_parser.add_argument(
        "--launch-browser",
        action="store_true",
        help="Launch a new browser instance.",
    )

    # 'judge' command
    judge_parser = subparsers.add_parser(
        "judge", help="Run the judging loop repeatedly."
    )
    judge_parser.add_argument(
        "challenge",
        nargs="?",
        default="getting_started",
        help="The name of the challenge context to use.",
    )
    judge_parser.add_argument(
        "--launch-browser",
        action="store_true",
        help="Launch a new browser instance.",
    )

    # 'resubmit' command
    resubmit_parser = subparsers.add_parser(
        "resubmit", help="Resubmit a previous attempt."
    )
    resubmit_parser.add_argument(
        "submission_id", help="The ID of the submission to resubmit."
    )
    resubmit_parser.add_argument(
        "--launch-browser",
        action="store_true",
        help="Launch a new browser instance.",
    )

    args = parser.parse_args()

    if args.command == "run":
        connect_to_existing = not args.launch_browser
        await run_challenge_automation(args.challenge, connect_to_existing)

    elif args.command == "judge":
        connect_to_existing = not args.launch_browser
        await run_judging_loop_automation(args.challenge, connect_to_existing)

    elif args.command == "resubmit":
        connect_to_existing = not args.launch_browser
        await run_resubmission_automation(args.submission_id, connect_to_existing)


if __name__ == "__main__":
    # This allows running the script directly from the command line, e.g., python -m src.app
    # The project root should be in PYTHONPATH.
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s, loop)))

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
