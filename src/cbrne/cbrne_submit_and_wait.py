from .steps import submit_for_judging


async def submit_and_wait_for_judging_outcome(self) -> str:
    judging_clicked = await submit_for_judging(
        self.page,
        self.config["selectors"]["submit_for_judging_button"],
        self.automation_settings.get("timeouts", {}),
    )
    if not judging_clicked:
        return "failure"

    await self._perform_step_delay()

    return await self._wait_for_judging_outcome()


