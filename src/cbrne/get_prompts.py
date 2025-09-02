import os
from ..utils import load_prompt_from_file


def get_prompts(self) -> list[dict]:
    prompts = self.config.get("prompts", [])
    loaded_prompts = []
    for prompt_config in prompts:
        if "file" in prompt_config:
            # Defaults to cbrne's local config directory as base for relative prompt files
            config_dir = os.path.dirname(os.path.abspath("src/cbrne/config.yaml"))
            loaded_prompts.append(load_prompt_from_file(prompt_config, config_dir))
        elif "text" in prompt_config:
            loaded_prompts.append(prompt_config)
    return loaded_prompts



