from ..config_loader import load_config


_CFG = load_config() or {}
_AUTOMATION_SETTINGS = _CFG.get("automation_settings", {})
DEFAULT_TIMEOUTS = _AUTOMATION_SETTINGS.get("timeouts", {})
DEFAULT_DELAY_MIN = _AUTOMATION_SETTINGS.get("delay_min_sec", 1)
DEFAULT_DELAY_MAX = _AUTOMATION_SETTINGS.get("delay_max_sec", 2)


