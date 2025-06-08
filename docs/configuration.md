# Configuration (`config.yaml`)

The `config.yaml` file is the central place to configure all aspects of the automation.

## Main Configuration

| Key                       | Description                                                                                              |
| ------------------------- | -------------------------------------------------------------------------------------------------------- |
| `base_url`                | The base URL for the Hack-a-Prompt website.                                                              |
| `browser_ws_endpoint`     | The WebSocket endpoint for Playwright to connect to your running browser instance.                       |
| `automation_settings`     | A collection of settings that control the automation behavior.                                           |
| `challenge_specific_configs` | A dictionary where each key is a challenge name, containing the configuration for that challenge.          |

## Automation Settings

The `automation_settings` section controls the behavior of the automation scripts.

| Key                       | Description                                                                          | Default Value         |
| ------------------------- | ------------------------------------------------------------------------------------ | --------------------- |
| `browser_executable_path` | The path to the browser executable.                                                  | `brave-browser-beta`  |
| `user_data_dir`           | The directory where the browser stores user data.                                    | `/tmp/brave-automation`|
| `remote_debugging_port`   | The port to use for remote debugging.                                                | `9222`                |
| `navigate_to_base_url`    | Whether to automatically navigate to the challenge's `base_url`.                     | `true`                |
| `loop_on_failure`         | Whether to loop and retry when a challenge submission fails.                         | `true`                |
| `max_retries`             | The maximum number of times to retry a failed submission.                            | `3`                   |
| `random_delay`            | Whether to use random delays between actions to simulate human behavior.             | `false`               |
| `delay_min_sec`           | The minimum delay in seconds.                                                        | `5`                   |
| `delay_max_sec`           | The maximum delay in seconds.                                                        | `60`                  |

## Challenge-Specific Configuration

Each challenge you want to automate should have an entry in the `challenge_specific_configs` section.

```yaml
challenge_specific_configs:
  getting_started:
    prompt_textarea: "textarea[data-testid='multimodal-input']"
    submit_prompt_button: "button[data-testid='send-button']"
    submit_for_judging_button: "button:has-text('Submit Current Response For Judging')"
    prompts:
      - text: "This is a test prompt."
        file: "prompts/my_prompt.txt"
```

*   **Selectors**: You need to provide CSS selectors for the various elements on the page. You can find these using your browser's developer tools.
*   **Prompts**: A list of prompts to use for the challenge. You can provide the prompt text directly with the `text` key, or you can load it from a file using the `file` key. 