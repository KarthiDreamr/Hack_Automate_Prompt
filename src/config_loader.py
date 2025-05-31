import yaml

def load_config(config_path="config.yaml"):
    """Loads the YAML configuration file."""
    try:
        with open(config_path, 'r') as f:
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

def get_challenge_config(config, challenge_name):
    """Extracts the configuration for a specific challenge."""
    if not config:
        return None
    base_url = config.get("base_url")
    if not base_url:
        print("Error: base_url not found in the main config.")
        # Depending on strictness, you might raise an error or return None

    challenge_conf = config.get("challenge_specific_configs", {}).get(challenge_name)
    if not challenge_conf:
        print(f"Error: Config for challenge '{challenge_name}' not found.")
        return None
    
    # Ensure base_url is part of the returned challenge config for convenience
    challenge_conf['base_url'] = base_url
    return challenge_conf 