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

### Browser Options

By default, the script will connect to a running browser instance. If you need to launch a new one, you can use the `--launch-browser` flag with either command:

```bash
python -m src.app run --launch-browser
python -m src.app judge --launch-browser
```

## Documentation

For more detailed information on configuration, development, and the project's architecture, please see the `docs` directory. 