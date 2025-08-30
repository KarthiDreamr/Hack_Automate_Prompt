# Hack-a-Prompt Automation Framework

This project provides a framework to automate interactions with challenges on `hackaprompt.com`. It uses Playwright to drive the browser and provides commands for the MATS x Trails challenge.

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

### MATS x Trails Challenge — Agent Track Submit

This command fills the intent textarea and clicks the **Submit Template** button once. Provide your own text via `--text`.

```bash
python -m src.app agent-track-submit --text "Hello from agent"
```

Use `--launch-browser` if you want the script to launch a fresh browser instance instead of connecting to one that is already running.

### Agent Track Submit with Retry

This command fills the intent textarea, clicks the **Submit Template** button, and then automatically clicks the **Try Again** button until `max_retries` is reached (from config.yaml). Provide your own text via `--text`.

```bash
python -m src.app agent-track-submit-retry --text "Hello from agent"
```

Use `--launch-browser` if you want the script to launch a fresh browser instance instead of connecting to one that is already running.

### Browser Options

```bash
brave-browser-beta --remote-debugging-port=9222
```

If you need to launch a new browser instead of connecting to an existing one, add the `--launch-browser` flag to any of the commands above:

```bash
python -m src.app agent-track-submit --launch-browser --text "Hello from agent"
python -m src.app agent-track-submit-retry --launch-browser --text "Hello from agent"
```

## Documentation

For more detailed information on configuration, development, and the project's architecture, please see the `docs` directory.

For older challenge functions (run, judge, run-intent), see the `src/challenge_executor/core/cbrne/README.md` file.
