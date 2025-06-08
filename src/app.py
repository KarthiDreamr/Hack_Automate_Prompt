import asyncio
import argparse
from playwright.async_api import async_playwright

from .config_loader import load_config, get_challenge_config
from .browser import BrowserManager
from .challenge_executor import ChallengeExecutor


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
        page = await browser_manager.get_page(
            connect_to_existing=connect_to_existing_browser
        )

        if not page:
            print("Failed to initialize browser or page. Exiting.")
            return

        try:
            executor = ChallengeExecutor(page, challenge_config, automation_settings)
            await executor.run()
        except Exception as e:
            print(f"An unexpected error occurred in run_challenge_automation: {e}")
        finally:
            if browser_manager.browser and browser_manager.browser.is_connected():
                print("Closing browser connection...")
                await browser_manager.browser.close()
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
        page = await browser_manager.get_page(
            connect_to_existing=connect_to_existing_browser
        )

        if not page:
            print("Failed to initialize browser or page. Exiting.")
            return

        try:
            executor = ChallengeExecutor(page, challenge_config, automation_settings)
            await executor.run_judging_loop()
        except Exception as e:
            print(f"An unexpected error occurred in judging loop automation: {e}")
        finally:
            if browser_manager.browser and browser_manager.browser.is_connected():
                print("Closing browser connection...")
                await browser_manager.browser.close()
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
        page = await browser_manager.get_page(
            connect_to_existing=connect_to_existing_browser
        )

        if not page:
            print("Failed to initialize browser or page. Exiting.")
            return

        try:
            executor = ChallengeExecutor(page, challenge_config, automation_settings)
            await executor.run_resubmission_loop(submission_id)
        except Exception as e:
            print(f"An unexpected error occurred in resubmission automation: {e}")
        finally:
            if browser_manager.browser and browser_manager.browser.is_connected():
                print("Closing browser connection...")
                await browser_manager.browser.close()
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
        try:
            await run_challenge_automation(args.challenge, connect_to_existing)
        except Exception as e:
            print(f"An error occurred during the automation: {e}")
        finally:
            print("Application finished.")
    elif args.command == "judge":
        connect_to_existing = not args.launch_browser
        try:
            await run_judging_loop_automation(args.challenge, connect_to_existing)
        except Exception as e:
            print(f"An error occurred during the judging loop: {e}")
        finally:
            print("Application finished.")
    elif args.command == "resubmit":
        connect_to_existing = not args.launch_browser
        try:
            await run_resubmission_automation(
                args.submission_id, connect_to_existing
            )
        except Exception as e:
            print(f"An error occurred during the resubmission: {e}")
        finally:
            print("Application finished.")


if __name__ == "__main__":
    # This allows running the script directly from the command line, e.g., python -m src.app
    # The project root should be in PYTHONPATH.
    asyncio.run(main())
