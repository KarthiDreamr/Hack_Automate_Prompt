# Development Guide

This guide provides instructions for setting up the development environment, running tests, and maintaining code quality.

## Setup

1.  **Create a Virtual Environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install Dependencies**:
    *   Install base dependencies with `pip-tools`:
        ```bash
        pip install pip-tools
        pip-compile requirements.in
        pip install -r requirements.txt
        ```
    *   Install Playwright browsers:
        ```bash
        playwright install --with-deps
        ```

## Testing

This project uses `pytest` for testing.

*   **Run All Tests**:
    ```bash
    pytest
    ```

*   **Run a Specific Test File**:
    ```bash
    pytest tests/test_challenge_executor.py
    ```

## Code Quality

This project uses `black` for code formatting and `flake8` for linting.

*   **Format Code**:
    ```bash
    black .
    ```

*   **Check for Linting Issues**:
    ```bash
    flake8 .
    ``` 