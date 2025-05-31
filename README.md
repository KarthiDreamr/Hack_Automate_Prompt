# HackAPrompt Automation Framework

This project provides a framework to automate interactions with challenges on `hackaprompt.com` (and potentially other websites) using Playwright. It focuses on filling forms, clicking buttons, and handling dynamic responses, including connecting to an existing Brave browser instance.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
- [Configuration](#configuration)
  - [Launching Brave with Remote Debugging](#launching-brave-with-remote-debugging)
  - [`config.yaml`](#configyaml)
- [Running the Automation](#running-the-automation)
- [File Structure](#file-structure)
- [How it Works (High-Level)](#how-it-works-high-level)
- [Troubleshooting & Notes](#troubleshooting--notes)

## Prerequisites

1.  **Python 3.7+**: Ensure you have a compatible Python version installed.
2.  **Brave Browser**: This framework is configured to connect to an existing Brave browser instance. You can adapt it for other Chromium-based browsers.
3.  **pip**: Python package installer.

## Setup Instructions

1.  **Clone the Repository (if applicable)**
    ```bash
    # If you have this project in a git repository:
    # git clone <repository-url>
    # cd <project-directory>
    cd "/home/karthidreamr/AI Jailbreak/HackAPrompt 2.0/prompt_automate" # Your project path
    ```

2.  **Create a Virtual Environment (Recommended)**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install Python Dependencies**
    Install the required Python packages using the `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```
    This will install `playwright` and `pyyaml`.

4.  **Install Playwright Browser Binaries**
    Playwright needs browser binaries to operate. Install them by running:
    ```bash
    playwright install
    ```
    You might also need to install their dependencies, especially on Linux:
    ```bash
    playwright install --with-deps
    ```
    If you encounter issues on Linux (especially Fedora), you might need to manually install a list of dependencies. Refer to Playwright documentation or past error messages for specific package names (e.g., `libicu`, `libjpeg`, etc.).

## Configuration

### Launching Brave with Remote Debugging

Before running the main automation script, you need to launch Brave browser with a remote debugging port enabled. The `run_automation.py` script handles this automatically. However, if you wish to do it manually or understand the process:

Open your terminal and run:
```bash
brave-browser --remote-debugging-port=9222
```
- If `brave-browser` is not in your PATH, you'll need to use the full path to the executable.
- This will start Brave with the Chrome DevTools Protocol (CDP) active on port 9222. The automation script will connect to this instance.
- **Important**: Ensure no other Brave instance is using this port. Close all Brave instances before running this command if you face issues.

### `config.yaml`

This file is central to configuring the automation tasks.

```yaml
# Example config.yaml structure
cdp_endpoint: "http://localhost:9222"

challenges:
  getting_started:
    base_url: "https://hackaprompt.com/track/tutorial_competition/getting_started"
    # Selectors for various elements on the page
    prompt_textarea: "textarea[data-testid='multimodal-input']"
    submit_prompt_button: "button[data-testid='send-button']"
    submit_for_judging_button: "button:has-text('Submit Current Response For Judging')"
    new_attempt_button: "button:has-text('Start a New Attempt')"
    # You can add more selectors here if needed, e.g., for success/failure indicators
    prompts:
      - text: "Test prompt 1 for getting_started"
      - text: "Another test prompt for this challenge"
  
  another_challenge: # Example for a different challenge
    base_url: "https://examplesite.com/another-form"
    # ... other selectors and prompts
```

**Key sections:**

*   `cdp_endpoint`: The endpoint for Playwright to connect to your running Brave browser instance. This should match the port you used when launching Brave.
*   `challenges`: A dictionary where each key is a challenge name (e.g., `getting_started`).
    *   `base_url`: The URL for the specific challenge page.
    *   **Selectors**: CSS or Playwright selectors for the interactive elements.
        *   `prompt_textarea`: The input field for your text.
        *   `submit_prompt_button`: The initial button to send your prompt to the LLM.
        *   `submit_for_judging_button`: The button to submit the LLM's response for evaluation.
        *   `new_attempt_button`: The button to start a new attempt after a successful submission.
    *   `prompts`: A list of prompts to try for the challenge. Currently, the script uses the first prompt in this list.

**Finding Selectors:**
Use your browser's developer tools (right-click on an element -> Inspect) to find appropriate and robust CSS selectors. Playwright also supports other selector engines (e.g., text-based, XPath).

## Running the Automation

The primary way to run the automation is using the `run_automation.py` script located in the project root:

```bash
python run_automation.py
```

This script will:
1.  Attempt to start `brave-browser --remote-debugging-port=9222` in the background.
2.  Wait a few seconds for the browser to initialize.
3.  Execute the main automation logic in `src/main.py`.
4.  Attempt to close the Brave browser instance it started upon completion or error.

The `src/main.py` script is configured to run the "getting_started" challenge by default. You can modify this in `src/main.py` if needed:
```python
# In src/main.py
async def main():
    challenge_to_run = "getting_started"  # Change this to run a different configured challenge
    # ...
```

## File Structure

```
prompt_automate/
├── .venv/                  # Virtual environment directory (if created)
├── src/
│   ├── main.py             # Main orchestrator script
│   ├── browser_manager.py  # Handles browser connection (CDP)
│   ├── challenge_executor.py # Logic for interacting with challenge elements
│   └── config_loader.py    # Loads and parses config.yaml
├── screenshots/            # Stores screenshots taken on error
├── config.yaml             # Configuration for URLs, selectors, prompts
├── requirements.txt        # Python package dependencies
├── run_automation.py       # Script to auto-start Brave and run the main automation
└── README.md               # This file
```

## How it Works (High-Level)

1.  **`run_automation.py`**:
    *   Starts `brave-browser` with `--remote-debugging-port=9222`.
    *   Executes `src/main.py`.

2.  **`src/main.py`**:
    *   Loads configuration using `config_loader.py`.
    *   Initializes Playwright and connects to the existing Brave instance via CDP using `browser_manager.py`.
    *   Calls `challenge_executor.py` to perform the interactions for the specified challenge.
    *   Ensures the browser connection is closed gracefully.

3.  **`src/config_loader.py`**:
    *   Reads and parses `config.yaml`.
    *   Provides functions to access the main configuration and specific challenge configurations.

4.  **`src/browser_manager.py`**:
    *   Contains logic to connect Playwright to an existing browser instance over the Chrome DevTools Protocol (CDP) or launch a new one if specified.

5.  **`src/challenge_executor.py`**:
    *   Navigates to the challenge URL.
    *   Fills the prompt textarea with text from `config.yaml`.
    *   Clicks the initial submit button.
    *   Waits for a fixed duration (30 seconds) for the AI to respond.
    *   Attempts to click the "Submit Current Response For Judging" button.
    *   **Failure Handling**: If a "Restart Challenge" button appears after submitting for judging (indicating a failed attempt), it clicks this button and skips the "Start New Attempt" step.
    *   If submission for judging is presumed successful (no restart), it then attempts to click the "Start a New Attempt" button.
    *   Takes screenshots and saves them to the `screenshots/` directory if errors occur during these interactions.

## Troubleshooting & Notes

*   **Brave Browser Issues**:
    *   Ensure Brave is fully closed before running `run_automation.py` or manually starting Brave with the remote debugging port, especially if you get errors about the port already being in use.
    *   If `run_automation.py` fails to start Brave, try running `brave-browser --remote-debugging-port=9222` manually in your terminal to see more detailed error messages. Ensure `brave-browser` is in your system PATH.
*   **Selector Changes**: Websites can change their structure, causing selectors in `config.yaml` to become outdated. If the script fails to find elements, update the selectors using your browser's developer tools.
*   **Error Screenshots**: If the script encounters errors during page interactions (e.g., cannot find a button, timeout), it will save a screenshot in the `screenshots/` directory. These are named with the error type and challenge name (e.g., `screenshots/error_submit_judging_getting_started.png`).
*   **CDP Connection**: If `src/main.py` cannot connect to the browser, verify:
    *   Brave is running with `--remote-debugging-port=9222`.
    *   The `cdp_endpoint` in `config.yaml` is correct (`http://localhost:9222`).
    *   No firewall is blocking the connection to this port.
*   **Fixed Wait Time**: The script currently uses a fixed 30-second wait after submitting the initial prompt. This might be too short or too long depending on the LLM's response time. The previous logic attempted to dynamically wait for button states but was simplified.
*   **Linux Dependencies**: For Playwright on Linux, ensure all necessary shared library dependencies are installed. `playwright install --with-deps` helps, but some distributions might require manual installation of additional packages.

---

This README should provide a good starting point for understanding and using the project. 