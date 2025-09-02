from ..utils import perform_delay
from .config import DEFAULT_DELAY_MIN, DEFAULT_DELAY_MAX


async def perform_step_delay(self):
    await perform_delay(
        self.automation_settings.get("random_delay", False),
        self.automation_settings.get("delay_min_sec", DEFAULT_DELAY_MIN),
        self.automation_settings.get("delay_max_sec", DEFAULT_DELAY_MAX),
        self.page,
    )



