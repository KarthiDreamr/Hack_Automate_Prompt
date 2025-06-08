# Hack-a-Prompt Automation Framework

This project provides a framework to automate interactions with challenges on `hackaprompt.com`. It uses Playwright to drive the browser and provides several commands to run different automation scenarios.

## Quick Start

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    playwright install --with-deps
    ```

2.  **Configure**:
    *   Copy `template.config.yaml` to `config.yaml`.
    *   Edit `config.yaml` to set your desired challenge URL and selectors.

3.  **Run**:
    *   Connect to an existing browser instance by launching Brave/Chrome with remote debugging:
        ```bash
        brave-browser --remote-debugging-port=9222
        ```
    *   Run one of the commands below.

## Commands

### Run the Full Challenge Loop

This command runs the full automation loop: fills the prompt, submits it, clicks "Submit for Judging", and restarts on failure.

```bash
python -m src.app run [challenge_name]
```
*   `challenge_name`: The name of the challenge defined in your `config.yaml` (defaults to `getting_started`).

### Run the Judging Loop

This command repeatedly clicks the "Submit for Judging" button. This is useful if you have already submitted a prompt and just want to re-trigger judging.

```bash
python -m src.app judge [challenge_name]
```

### Resubmit a Previous Attempt

This command navigates to a specific submission and re-triggers the judging process.

```bash
python -m src.app resubmit <submission_id>
```

## Documentation

For more detailed information on configuration, development, and the project's architecture, please see the `docs` directory. 