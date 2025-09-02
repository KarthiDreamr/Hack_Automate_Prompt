def get_timeout(self, key: str, default: int) -> int:
    return self.automation_settings.get("timeouts", {}).get(
        key, self.automation_settings.get(key, default)
    )



