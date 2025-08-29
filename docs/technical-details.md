# Technical Details

This document provides a more in-depth explanation of the project's architecture, file structure, and advanced usage.

## How it Works (High-Level)

1.  **Entry Point (`src/app.py`)**:
    *   This script is the main entry point for the application and uses `argparse` to handle different commands (`run`, `judge`, `resubmit`).
    *   It initializes Playwright and the `BrowserManager`.

2.  **Browser Management (`src/browser.py`)**:
    *   The `BrowserManager` class is responsible for the entire browser lifecycle.
    *   It can launch a new browser process with remote debugging enabled or connect to an existing one using the configured WebSocket endpoint.
    *   It provides a Playwright `Page` object for the automation scripts to use.

3.  **Configuration (`src/config_loader.py` and `config.yaml`)**:
    *   `config.yaml` stores all the configuration for the application, including browser settings, challenge URLs, and CSS selectors.
    *   `config_loader.py` provides functions to load and parse this configuration.

4.  **Challenge Execution (`src/challenge_executor.py`)**:
    *   The `ChallengeExecutor` class contains the core logic for interacting with the challenge pages.
    *   It has different methods for the different automation modes (`run`, `run_judging_loop`, `run_resubmission_loop`).
    *   It handles filling prompts, clicking buttons, checking for success or failure, and taking screenshots on error.

## File Structure

```
prompt_automate/
├── .venv/                  # Virtual environment directory
├── docs/
│   └── technical_details.md # This file
├── src/
│   ├── app.py              # Main entry point with command-line interface
│   ├── browser.py          # Unified browser process and connection manager
│   ├── challenge_executor.py # Core logic for all challenge interaction modes
│   └── config_loader.py    # Loads and parses config.yaml
├── tests/                  # Pytest tests
├── screenshots/            # Stores screenshots taken on error
├── .flake8                 # Configuration for flake8
├── .gitignore              # Git ignore file
├── config.yaml             # Main configuration file
├── template.config.yaml    # Template for configuration
├── pytest.ini              # Configuration for pytest
├── requirements.in         # Base dependencies for pip-tools
├── requirements.txt        # Pinned dependencies
└── README.md               # Simplified main README
```

## Troubleshooting & Notes

*   **Browser Issues**:
    *   Ensure your browser is fully closed before launching with a remote debugging port, especially if you get errors about the port already being in use.
    *   If the script fails to start the browser, try running the command manually in your terminal to see more detailed error messages (e.g., `brave-browser --remote-debugging-port=9222`).
*   **Selector Changes**: Websites can change their structure, causing selectors in `config.yaml` to become outdated. If the script fails to find elements, you will need to update the selectors using your browser's developer tools.
*   **Error Screenshots**: If the script encounters errors during page interactions, it will save a screenshot in the `screenshots/` directory. These are named with the error type and challenge name.
*   **Playwright on Linux**: Ensure all necessary shared library dependencies are installed. Running `playwright install --with-deps` is recommended. 