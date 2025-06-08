import pytest
from unittest.mock import AsyncMock, MagicMock
from src.challenge_executor import ChallengeExecutor


@pytest.fixture
def mock_page():
    """Fixture to create a mock Playwright Page object."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.locator.return_value.wait_for = AsyncMock()
    page.locator.return_value.fill = AsyncMock()
    page.locator.return_value.click = AsyncMock()
    page.locator.return_value.is_visible = AsyncMock(return_value=False)
    page.screenshot = AsyncMock()
    return page


@pytest.mark.asyncio
async def test_challenge_executor_run_happy_path(mock_page):
    """
    Tests the happy path of the ChallengeExecutor where the challenge is solved
    on the first attempt.
    """
    challenge_config = {
        "base_url": "http://example.com",
        "prompt_textarea": "textarea",
        "submit_prompt_button": "button#submit",
        "submit_for_judging_button": "button#judge",
        "challenge_name": "test_challenge",
        "prompts": [{"text": "test prompt"}],
    }
    automation_settings = {
        "navigate_to_base_url": True,
        "max_retries": 1,
        "loop_on_failure": False,
        "random_delay": False,
    }

    # Simulate success
    mock_page.locator.return_value.is_visible.side_effect = [
        True,  # For the 'Challenge Conquered' popup
    ]

    executor = ChallengeExecutor(mock_page, challenge_config, automation_settings)
    await executor.run()

    # Assertions
    mock_page.goto.assert_called_once_with("http://example.com")
    mock_page.locator.assert_any_call("textarea")
    mock_page.locator().fill.assert_called_once_with("test prompt")
    mock_page.locator().click.assert_called()
    assert mock_page.locator.call_count > 1  # more than just the prompt
    mock_page.locator().is_visible.assert_called()
    mock_page.screenshot.assert_not_called()
