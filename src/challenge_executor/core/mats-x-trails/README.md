# MATS x Trails Challenge Special — Agent Track Submit

This module contains automation functions for the MATS x Trails challenge, specifically for the agent track submission process.

## Files

- `agent_track_submit.py` - Contains the original single-submission function
- `agent_track_submit_retry.py` - Contains the enhanced retry functionality

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
- Continues looping until `max_retries` is reached (from config.yaml)
- Respects delay settings (min/max delay, random delay option)
- Includes proper error handling and logging

## Configuration

The functions use settings from `config.yaml`:
- `max_retries`: Maximum number of attempts (default: 1000)
- `delay_min_sec`: Minimum delay between attempts (default: 4)
- `delay_max_sec`: Maximum delay between attempts (default: 12)
- `random_delay`: Whether to use random delays (default: false)

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

## Selectors

The functions use the following page selectors:
- Intent textarea: `textarea[placeholder^="Write your injection intent directly"]`
- Submit Template button: `button:has-text("Submit Template")`
- Try Again button: `button:has-text("Try Again")`
