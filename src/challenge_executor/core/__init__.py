from playwright.async_api import Page


class ChallengeExecutor:
    def __init__(self, page: Page, config: dict, automation_settings: dict):
        self.page = page
        self.config = config
        self.automation_settings = automation_settings

    async def run(self):
        from .cbrne.run import run
        return await run(self)

    async def run_judging_loop(self):
        from .cbrne.run_judging_loop import run_judging_loop
        return await run_judging_loop(self)

    async def _submit_and_wait_for_judging_outcome(self) -> str:
        from .cbrne.submit_and_wait import submit_and_wait_for_judging_outcome
        return await submit_and_wait_for_judging_outcome(self)

    async def _wait_for_judging_outcome(self) -> str:
        from .cbrne.wait_for_judging_outcome import wait_for_judging_outcome
        return await wait_for_judging_outcome(self)

    def _validate_config(self, required_keys: list[str]) -> bool:
        from .validate_config import validate_config
        return validate_config(self, required_keys)

    def _get_prompts(self) -> list[dict]:
        from .get_prompts import get_prompts
        return get_prompts(self)

    async def _perform_step_delay(self):
        from .perform_step_delay import perform_step_delay
        return await perform_step_delay(self)

    def _get_timeout(self, key: str, default: int) -> int:
        from .get_timeout import get_timeout
        return get_timeout(self, key, default)

    async def run_intent_loop(self):
        from .cbrne.run_intent_loop import run_intent_loop
        return await run_intent_loop(self)

    async def _wait_for_intent_outcome(self) -> str:
        from .cbrne.wait_for_intent_outcome import wait_for_intent_outcome
        return await wait_for_intent_outcome(self)

    async def run_intent_loop_2(self):
        from .cbrne.run_intent_loop_2 import run_intent_loop_2
        return await run_intent_loop_2(self)

    async def agent_track_submit_retry(self, text: str, timeouts: dict | None = None):
        from .mats_x_trails import agent_track_submit_with_retry
        return await agent_track_submit_with_retry(self, text, timeouts)


