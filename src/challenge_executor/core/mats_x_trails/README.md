# MATS x Trails Challenge Special — Agent Track Submit

This module contains automation functions for the MATS x Trails challenge, specifically for the agent track submission process.

## Files

- `agent_track_submit.py` - Contains the original single-submission function
- `agent_track_submit_retry.py` - Contains the enhanced retry functionality
- `config.yaml` - Main configuration file for the MATS x Trails challenge

## Functions

### `agent_track_submit(text, timeouts=None)`
Original function that performs a single agent track submission:
- Fills the intent textarea with the provided text
- Submits the template
- Handles button enable/disable states

### `agent_track_submit_with_retry(text, timeouts=None, config=None)`
Enhanced function that includes retry functionality:
- Performs the same submission as the original function
- Automatically clicks the "Try Again" button after each submission
- Continues looping until `max_retries` is reached (from task-specific config)
- Respects delay settings (min/max delay, random delay option)
- Includes proper error handling and logging
- **Extended timeout**: Waits up to 90 seconds for the "Try Again" button to appear

## Configuration Structure

### Main Configuration (`config.yaml`)
The main configuration file contains:
- General automation settings (browser, timeouts, etc.)
- Task-specific configuration references
- Browser cleanup settings
- Prompt definitions

### Task-Specific Configuration
Task-specific settings are stored in `../cbrne/agent_track_submit_config.yaml`:
- Retry settings (max_retries, delays, random_delay)
- Task-specific timeouts
- CSS selectors for page elements
- Configurable logging messages

## Usage

```python
from challenge_executor.core.mats_x_trails import agent_track_submit, agent_track_submit_with_retry

# Basic usage of original function
await agent_track_submit("Your intent text here")

# Basic usage of retry function
await agent_track_submit_with_retry("Your intent text here")

# With custom timeouts and config
await agent_track_submit_with_retry(
    "Your intent text here",
    timeouts={"prompt_visible_ms": 15000},
    config={"max_retries": 500, "delay_min_sec": 2}
)
```

## Configuration Management

- **Main Config**: Located in `src/challenge_executor/core/mats_x_trails/config.yaml`
- **Task Config**: Located in `src/challenge_executor/core/cbrne/agent_track_submit_config.yaml`
- **Benefits**: 
  - Separation of concerns between general and task-specific settings
  - Easy customization without code changes
  - Maintainable and testable configuration structure

## Selectors

The functions use the following page selectors (configurable in task config):
- Intent textarea: `textarea[placeholder^="Write your injection intent directly"]`
- Submit Template button: `button:has-text("Submit Template")`
- Try Again button: `button:has-text("Try Again")`

## Important Notes

- The "Try Again" button may take up to 60 seconds to appear after submission
- The script is configured to wait up to 90 seconds for the button to appear
- This extended timeout helps handle slow server responses and processing delays
