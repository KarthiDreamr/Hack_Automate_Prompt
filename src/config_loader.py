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
    """
    Extracts and processes the configuration for a specific challenge.
    If a prompt has a 'file' key, it reads the content of the file
    and populates the 'text' key.
    """
    if not config:
        return None
    base_url = config.get("base_url")
    if not base_url:
        print("Error: base_url not found in the main config.")
        return None

    challenge_conf = config.get("challenge_specific_configs", {}).get(challenge_name)
    if not challenge_conf:
        print(f"Error: Config for challenge '{challenge_name}' not found.")
        return None
    
    # Process prompts to load from files if specified
    if 'prompts' in challenge_conf and isinstance(challenge_conf['prompts'], list):
        for i, prompt in enumerate(challenge_conf['prompts']):
            if 'file' in prompt and 'text' not in prompt:
                try:
                    with open(prompt['file'], 'r', encoding='utf-8') as f:
                        prompt['text'] = f.read()
                    print(f"   ...loaded prompt '{prompt.get('id', i)}' from file: {prompt['file']}")
                except FileNotFoundError:
                    print(f"Error: Prompt file not found: {prompt['file']}. Skipping prompt.")
                    prompt['text'] = f"ERROR: Could not load prompt from {prompt['file']}"
                except Exception as e:
                    print(f"Error reading prompt file {prompt['file']}: {e}. Skipping prompt.")
                    prompt['text'] = f"ERROR: Could not read prompt from {prompt['file']}"

    # Ensure base_url is part of the returned challenge config for convenience
    challenge_conf['base_url'] = base_url
    return challenge_conf 