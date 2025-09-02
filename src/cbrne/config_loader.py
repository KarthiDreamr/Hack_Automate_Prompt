import yaml
import os
from typing import Any, Dict


def load_config(config_path: str = "src/cbrne/config.yaml") -> Dict[str, Any] | None:
    """Loads the YAML configuration file for cbrne package."""
    env_path = os.getenv("HAP_CBRNE_CONFIG_PATH")
    if env_path and (config_path == "src/cbrne/config.yaml" or not config_path):
        config_path = env_path
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            if not config:
                print(f"Warning: {config_path} is empty or invalid.")
                return None
            return config
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML in '{config_path}': {e}")
        return None


def get_challenge_config(main_config: Dict[str, Any], challenge_name: str) -> Dict[str, Any] | None:
    if not main_config:
        return None
    base_cfg = {k: v for k, v in main_config.items() if k != "challenge_specific_configs"}
    specific = (
        main_config.get("challenge_specific_configs", {}).get(challenge_name, {})
        or {}
    )
    merged = {**base_cfg, **specific}
    return merged


