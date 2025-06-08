import yaml
import os


def load_config(config_path="config.yaml"):
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


def get_challenge_config(main_config: dict, challenge_name: str) -> dict | None:
    """
    Retrieves a challenge-specific configuration and merges it with the base_url.
    """
    if "base_url" not in main_config:
        print("Error: base_url not found in the main config.")
        return None

    challenge_configs = main_config.get("challenge_specific_configs", {})
    challenge_config = challenge_configs.get(challenge_name)

    if not challenge_config:
        print(f"Error: Config for challenge '{challenge_name}' not found.")
        return None

    # Merge the base_url into the specific challenge config
    challenge_config["base_url"] = main_config["base_url"]
    return challenge_config


def _load_prompt_from_file(prompt_config: dict, config_dir: str) -> dict:
    """
    Loads prompt text from a file specified in the prompt's configuration.
    """
    prompt_file_path = os.path.join(config_dir, "..", prompt_config["file"])
    if not os.path.exists(prompt_file_path):
        print(f"Warning: Prompt file not found: {prompt_file_path}")
        prompt_config["text"] = ""
        return prompt_config

    with open(prompt_file_path, "r") as f:
        prompt_config["text"] = f.read().strip()
    return prompt_config
