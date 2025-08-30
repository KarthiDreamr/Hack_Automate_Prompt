import yaml
import os
from typing import Any, Dict


def load_config(config_path: str = "src/challenge_executor/core/mats_x_trails/config.yaml") -> Dict[str, Any] | None:
    """Loads the YAML configuration file."""
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
    """
    Returns a merged challenge-specific configuration.
    - Starts from `main_config` base values (e.g., base_url)
    - Overlays values from `challenge_specific_configs[challenge_name]` if present
    """
    if not main_config:
        return None

    base_cfg = {k: v for k, v in main_config.items() if k != "challenge_specific_configs"}
    specific = (
        main_config.get("challenge_specific_configs", {}).get(challenge_name, {})
        or {}
    )

    merged = {**base_cfg, **specific}
    return merged


