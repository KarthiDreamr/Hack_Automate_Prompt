# CBRNE (Challenge-Based Response and Navigation Engine)

This directory contains task-specific automation modules for different challenge types.

## Configuration Structure

Each task-specific module has its own configuration file to avoid hardcoding values in the scripts. This makes the code more maintainable and allows for easy customization without code changes.

### Agent Track Submit Configuration

The `agent_track_submit_config.yaml` file contains all configuration settings for the agent track submit functionality:

#### Retry Settings
- `max_retries`: Maximum number of retry attempts (default: 1000)
- `delay_min_sec`: Minimum delay between attempts in seconds (default: 4)
- `delay_max_sec`: Maximum delay between attempts in seconds (default: 12)
- `random_delay`: Whether to use random delays between attempts (default: false)

#### Timeout Settings
- `prompt_visible_ms`: Timeout for waiting for prompt textarea to be visible (default: 10000ms)
- `submit_prompt_click_ms`: Timeout for clicking the submit button (default: 5000ms)
- `submit_template_enable_ms`: Timeout for waiting for submit button to enable (default: 30000ms)
- `try_again_button_visible_ms`: Timeout for waiting for "Try Again" button to appear (default: 90000ms)
- `try_again_button_click_ms`: Timeout for clicking the "Try Again" button (default: 10000ms)
- `polling_interval_ms`: Interval for checking button state (default: 200ms)

#### CSS Selectors
- `textarea`: Selector for the intent textarea
- `submit_button`: Selector for the submit template button
- `try_again_button`: Selector for the try again button

#### Logging Messages
All logging messages are configurable to allow for localization or customization.

## Usage

The configuration is automatically loaded by the scripts. To modify behavior:

1. Edit the appropriate task-specific config file
2. Restart the automation

No code changes are required for configuration updates.

## Adding New Task Configurations

To add a new task configuration:

1. Create a new `{task_name}_config.yaml` file in this directory
2. Define the configuration structure with appropriate sections
3. Update the main `config.yaml` to reference the new task config
4. Modify the corresponding script to load and use the configuration

## Benefits

- **Maintainability**: Configuration changes don't require code modifications
- **Flexibility**: Easy to adjust timeouts, selectors, and behavior
- **Testability**: Different configurations can be used for testing
- **Documentation**: Configuration files serve as documentation for expected behavior
