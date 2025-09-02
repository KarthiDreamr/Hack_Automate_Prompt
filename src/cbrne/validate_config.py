import logging


def validate_config(self, required_keys: list[str]) -> bool:
    for key in required_keys:
        if key not in self.config:
            logging.error(f"Missing required key in config: '{key}'")
            return False
    if "selectors" in required_keys:
        for selector in [
            "prompt_textarea",
            "submit_prompt_button",
            "submit_for_judging_button",
        ]:
            if selector not in self.config.get("selectors", {}):
                logging.error(f"Missing required selector in config: '{selector}'")
                return False
    return True



