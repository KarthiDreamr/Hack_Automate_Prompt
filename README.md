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
        brave-browser-beta --remote-debugging-port=9222
        ```
    *   Run one of the commands below.

## Commands

### Run the Full Automation Loop

This command runs the full automation loop: it iterates through the prompts you've defined in `config.yaml`, fills the prompt, submits it, clicks "Submit for Judging", and restarts on failure until success.

```bash
python -m src.app run
```

### Run the Judging Loop

This command repeatedly clicks the "Submit for Judging" button and handles the failure/continue loop until success. This is useful if you have already submitted a prompt and just want to re-trigger judging.

```bash
python -m src.app judge
```

### Run the Intent Loop

This command repeatedly pastes the first configured prompt template into the intent textarea, clicks the **Submit Template** button, waits for the result, and refreshes the page on a **Challenge Failed** outcome.  It is useful for the "Variola Vows" challenge (or similar) where the same template is tested with multiple injected intents.

```bash
python -m src.app run-intent
```

Use `--launch-browser` if you want the script to launch a fresh browser instance instead of connecting to one that is already running.

### Browser Options

```bash
brave-browser-beta --remote-debugging-port=9222
```

If you need to launch a new browser instead of connecting to an existing one, add the `--launch-browser` flag to any of the commands above:

```bash
python -m src.app run --launch-browser
python -m src.app judge --launch-browser
python -m src.app run-intent --launch-browser
```

## Documentation

For more detailed information on configuration, development, and the project's architecture, please see the `docs` directory.
