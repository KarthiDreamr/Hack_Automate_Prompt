from playwright.async_api import Page, Locator
import os # Added for os.path.join and os.makedirs

async def execute_interaction_test(page: Page, challenge_config: dict):
    """Executes the defined interaction test sequence for a challenge."""
    if not page or not challenge_config:
        print("Error: Page object or challenge_config missing for execute_interaction_test.")
        return

    base_url = challenge_config.get("base_url")
    prompt_textarea_selector = challenge_config.get("prompt_textarea")
    submit_prompt_button_selector = challenge_config.get("submit_prompt_button")
    submit_for_judging_button_selector = challenge_config.get("submit_for_judging_button")
    new_attempt_button_selector = challenge_config.get("new_attempt_button")
    challenge_name = challenge_config.get("challenge_name", "unknown_challenge") # Get challenge name for screenshots

    # Get automation settings from the main config
    automation_settings = challenge_config.get('automation_settings', {})
    loop_on_failure = automation_settings.get('loop_on_failure', True) # Default to True if not specified

    # Define screenshots directory relative to the script location or project root
    # Assuming run_automation.py is in project root, and this script is in src/
    # So, ../screenshots from this file's perspective if main.py is run from src/
    # Or just screenshots if run_automation.py sets PYTHONPATH correctly and main.py is run via python -m src.main
    # For simplicity and robustness with run_automation.py, we'll assume current working dir is project root.
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True) # Ensure directory exists

    if not all([base_url, prompt_textarea_selector, submit_prompt_button_selector, 
                submit_for_judging_button_selector, new_attempt_button_selector]):
        print("Error: Missing one or more essential selectors/config in challenge_config.")
        return

    try:
        current_url = page.url
        if base_url not in current_url:
             print(f"Page is not on {base_url}, navigating...")
             await page.goto(base_url)
        else:
            print(f"Page is already on or started with {base_url}")
        
        print(f"Current page URL for challenge '{challenge_name}': {page.url}")
        await page.wait_for_timeout(2000)

        test_prompt_text = "Test prompt to trigger LLM response and button state changes."
        prompts_config = challenge_config.get("prompts")
        if prompts_config and len(prompts_config) > 0:
            test_prompt_text = prompts_config[0].get("text", test_prompt_text)
        
        print(f"\n--- Running Interaction Test for '{challenge_name}' ---")

        # Start of the indefinite loop
        while True:
            print(f"1. Filling text area ('{prompt_textarea_selector}') with: '{test_prompt_text}'")
            prompt_area = page.locator(prompt_textarea_selector)
            await prompt_area.wait_for(state="visible", timeout=10000)
            await prompt_area.fill(test_prompt_text)
            print("   Filled text area.")
            await page.wait_for_timeout(500)

            submit_prompt_button: Locator = page.locator(submit_prompt_button_selector)

            print(f"2. Clicking submit prompt button ('{submit_prompt_button_selector}')")
            if await submit_prompt_button.is_disabled():
                print("   Submit prompt button is initially disabled. This is unexpected after typing.")
            await submit_prompt_button.click(timeout=5000)
            print("   Clicked submit prompt button.")

            # Add a static wait as requested, to allow the UI to begin processing.
            await page.wait_for_timeout(2000)
            
            # Wait for the 'Submit for Judging' button to be enabled
            submit_judging_button: Locator = page.locator(submit_for_judging_button_selector)
            print(f"   Waiting for '{submit_for_judging_button_selector}' to become enabled...")
            
            try:
                # wait_for, when called on a Locator, defaults to waiting for the element to be visible and enabled.
                await submit_judging_button.wait_for(timeout=180000) # Wait up to 180s (3 minutes)
                print("   'Submit for Judging' button is now enabled.")
            except Exception as e:
                print(f"   Timeout or error waiting for 'Submit for Judging' button to be enabled: {e}")
                # Decide if you want to proceed or raise an error. For now, we'll try to proceed.
            
            # --- Step 3: Submit for Judging --- 
            print(f"3. Attempting to click 'Submit for Judging' button ('{submit_for_judging_button_selector}')...")
            judging_button_successfully_clicked = False
            challenge_failed_and_restarted = False # Flag to track if "Restart Challenge" was clicked

            try:
                await submit_judging_button.click(timeout=180000)
                print("   Successfully attempted click on 'Submit for Judging' button.")
                judging_button_successfully_clicked = True
                
                await page.wait_for_timeout(3000) # Pause for potential modal

                # Check for "Challenge Conquered!" popup
                success_selector = 'h2:has-text("Challenge Conquered! 🎉")'
                success_element = page.locator(success_selector)

                if await success_element.is_visible(timeout=5000):
                    print("BREAK SUCCESS!")
                    return # Stop execution for this challenge

                # Check for "Not Quite There Yet" popup / "Restart Challenge" button
                restart_challenge_button_selector = "button:has-text('Restart Challenge')"
                restart_challenge_button = page.locator(restart_challenge_button_selector)
                
                if await restart_challenge_button.is_visible(timeout=5000): # Check if failure popup is visible
                    print("   'Not Quite There Yet' popup detected. Clicking 'Restart Challenge'.")
                    await restart_challenge_button.click(timeout=5000)
                    print("   Clicked 'Restart Challenge' button.")
                    challenge_failed_and_restarted = True
                    await page.wait_for_timeout(2000) # Wait for UI to update after restart
                else:
                    print("   'Restart Challenge' button not found, assuming submission was successful or led to a different state.")
                    judging_button_successfully_clicked = False # Not a failure, but not a restart condition

            except Exception as e:
                print(f"   Error during 'Submit for Judging' or 'Restart Challenge' check: {e}")
                screenshot_path = os.path.join(screenshots_dir, f"error_submit_judging_or_restart_{challenge_name}.png")
                await page.screenshot(path=screenshot_path)
                print(f"   Screenshot saved to {screenshot_path}")
                judging_button_successfully_clicked = False # Ensure this is false if an error occurs here

            # Loop control logic
            if challenge_failed_and_restarted and loop_on_failure:
                print("   Submission failed. Looping to try again...")
                continue # Continue to the next iteration of the while loop
            else:
                # Break the loop if not configured to loop, or if the challenge was not restarted
                if not loop_on_failure:
                    print("   Looping disabled. Stopping after one attempt.")
                break # Exit the while loop

        if challenge_failed_and_restarted:
            print("   Challenge failed and was restarted. Skipping 'Start a New Attempt'.")
        elif not judging_button_successfully_clicked:
            print("   Skipping 'Start a New Attempt' because 'Submit for Judging' was not successful or not attempted.")
        else:
            # --- Step 4: Start a New Attempt --- 
            print(f"4. Attempting to click 'Start a New Attempt' button ('{new_attempt_button_selector}')...")
            new_attempt_button: Locator = page.locator(new_attempt_button_selector)
            try:
                if await new_attempt_button.is_disabled(timeout=1000):
                     print("   'Start a New Attempt' button is disabled. Attempting click anyway if visible.")
                
                if await new_attempt_button.is_visible(timeout=10000): # Increased timeout for visibility
                    await new_attempt_button.click(timeout=10000)
                    print("   Successfully attempted click on 'Start a New Attempt' button.")
                else:
                    print("   'Start a New Attempt' button is not visible.")
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"   Error clicking 'Start a New Attempt' button: {e}")
                screenshot_path = os.path.join(screenshots_dir, f"error_new_attempt_button_{challenge_name}.png")
                await page.screenshot(path=screenshot_path)
                print(f"   Screenshot saved to {screenshot_path}")

        print("\nInteraction test sequence processing completed.")

    except Exception as e:
        print(f"General error during interaction test for '{challenge_name}': {e}")
        try:
            screenshot_path = os.path.join(screenshots_dir, f"error_general_interaction_test_{challenge_name}.png")
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
        except Exception as se:
            print(f"Could not take screenshot: {se}") 