import os
import logging
from playwright.async_api import Page


async def take_screenshot(page: Page, stage: str):
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    screenshot_path = os.path.join(screenshots_dir, f"error_{stage}.png")
    try:
        await page.screenshot(path=screenshot_path)
        logging.info(f"Screenshot saved to {screenshot_path}")
    except Exception as e:
        logging.error(f"Could not take screenshot: {e}")


async def perform_delay(should_delay: bool, min_sec: float, max_sec: float, page: Page):
    if not should_delay:
        return
    import random
    delay = random.uniform(min_sec, max_sec)
    logging.info(f"   ...waiting for {delay:.2f} seconds...")
    await page.wait_for_timeout(delay * 1000)


def load_prompt_from_file(prompt_config: dict, config_dir: str) -> dict:
    prompt_file_path = os.path.join(config_dir, prompt_config["file"])
    if not os.path.exists(prompt_file_path):
        print(f"Warning: Prompt file not found: {prompt_file_path}")
        prompt_config["text"] = ""
        return prompt_config

    with open(prompt_file_path, "r") as f:
        prompt_config["text"] = f.read().strip()
    return prompt_config


__all__ = [
    "take_screenshot",
    "perform_delay",
    "load_prompt_from_file",
]


