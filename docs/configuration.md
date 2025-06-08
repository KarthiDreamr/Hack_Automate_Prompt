# Configuration (`config.yaml`)

The `config.yaml` file is the central place to configure all aspects of the automation.

## Main Configuration

| Key                   | Description                                                                 |
| --------------------- | --------------------------------------------------------------------------- |
| `base_url`            | The base URL for the Hack-a-Prompt challenge page.                          |
| `automation_settings` | A collection of settings that control the automation behavior.              |
| `selectors`           | CSS selectors for the elements the script needs to interact with.           |
| `prompts`             | A list of prompts to be attempted by the script.                            |

## Automation Settings

| Key                       | Description                                                                          | Default Value         |
| ------------------------- | ------------------------------------------------------------------------------------ | --------------------- |
| `browser_executable_path` | Path to the browser executable (e.g., `google-chrome`, `brave-browser`).             | `brave-browser-beta`  |
| `user_data_dir`           | The directory for the browser's user data.                                           | `/tmp/brave-automation`|
| `remote_debugging_port`   | The port for remote debugging.                                                       | `9222`                |
| `browser_ws_endpoint`     | The WebSocket endpoint for Playwright to connect to your running browser.            | `http://localhost:9222`|
| `navigate_to_base_url`    | Whether to automatically navigate to the `base_url` at the start.                    | `true`                |
| `loop_on_failure`         | Whether to loop and retry when a prompt submission fails.                            | `true`                |
| `max_retries`             | The maximum number of times to retry a failed submission.                            | `3`                   |
| `random_delay`            | Whether to use random delays between actions to simulate human behavior.             | `false`               |
| `delay_min_sec`           | The minimum delay in seconds.                                                        | `5`                   |
| `delay_max_sec`           | The maximum delay in seconds.                                                        | `60`                  |

## Selectors

You need to provide CSS selectors for the various elements on the page. You can find these using your browser's developer tools.

```yaml
selectors:
  prompt_textarea: "textarea[data-testid='multimodal-input']"
  submit_prompt_button: "button[data-testid='send-button']"
  submit_for_judging_button: "button:has-text('Submit Current Response For Judging')"
  new_attempt_button: "button:has-text('Start a New Attempt')"
```

## Prompts

This is a list of prompts to use for the challenge. You can provide the prompt text directly with the `text` key, or you can load it from a file using the `file` key. The script will iterate through them.

```yaml
prompts:
  - text: "This is a test prompt directly in the YAML."
  - file: "prompts/my_prompt.txt"
``` 