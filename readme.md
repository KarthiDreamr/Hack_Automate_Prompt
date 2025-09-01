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

## Browser Setup

### Download Brave Beta Browser

Download Brave Beta from the official website: https://brave.com/download-beta/

### Browser Launch Command

```bash
brave-browser-beta --remote-debugging-port=9222
```

## Commands

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

## Configuration

### Creating Your Config File

**Important**: Real configuration files containing your specific settings are not committed to git for security reasons. You must create your own config file from the provided templates.

1. **Main Configuration**: Copy the template to create your main config:
   ```bash
   cp template.config.yaml config.yaml
   ```

2. **Challenge-Specific Configs**: Copy challenge-specific templates as needed:
   ```bash
   # For MATS x Trails challenge
   cp src/challenge_executor/core/mats_x_trails/template.config.yaml src/challenge_executor/core/mats_x_trails/config.yaml
   
   # For CBRNE challenge
   cp src/challenge_executor/core/cbrne/template.config.yaml src/challenge_executor/core/cbrne/config.yaml
   ```

3. **Edit Your Config**: Modify the copied config files with your specific:
   - Challenge URLs
   - CSS selectors
   - Timeout values
   - Browser settings
   - Custom prompts

### Template Files vs Real Configs

- **Template files** (committed to git): `template.config.yaml` in each directory
- **Real config files** (gitignored): `config.yaml` in each directory

Each directory containing a config file has its own `.gitignore` file that excludes the real `config.yaml` while allowing the `template.config.yaml` to be committed. This ensures that:
- Sensitive configuration data is never accidentally committed
- Templates provide examples and starting points
- Users can customize their setup without affecting others
- Each challenge module manages its own configuration independently
