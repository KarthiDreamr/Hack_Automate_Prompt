import asyncio
from playwright.async_api import async_playwright, Playwright
import pathlib

async def run(playwright: Playwright):
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()

    form_path = pathlib.Path("test_form.html").resolve()
    test_url = f"file://{form_path}?test=true"

    async def test_form_scenario(input_value: str, expect_submission: bool):
        print(f"\n--- Testing with input: '{input_value}' (Expecting submission: {expect_submission}) ---")
        await page.goto(test_url)

        # Listen for dialogs (alerts)
        alert_text = None
        def handle_dialog(dialog):
            nonlocal alert_text
            alert_text = dialog.message
            print(f"Alert received: {dialog.message}")
            dialog.accept()

        page.on("dialog", handle_dialog)

        # Fill the form
        await page.locator('input[name="message"]').fill(input_value)
        print(f"Filled form with: {input_value}")

        # Click the submit button
        await page.locator('input[type="submit"][name="submitbutton"]').click()
        print("Submit button clicked.")

        # Wait a moment for the alert to be processed by Playwright
        await page.wait_for_timeout(500)

        # Remove the dialog listener to avoid interference in other tests/runs
        page.remove_listener("dialog", handle_dialog)

        if expect_submission:
            if alert_text == "✅ Success!":
                print("'✅ Success!' alert received as expected.")
                # Ensure we are still on the form page (or it hasn't navigated away)
                if "results.html" not in page.url:
                    print("SUCCESS: '✅ Success!' alert received and stayed on form page as expected.")
                    return True
                else:
                    print(f"FAILURE: '✅ Success!' alert received, but unexpectedly navigated to {page.url}")
                    return False
            else:
                print(f"FAILURE: Expected '✅ Success!' alert, but got '{alert_text}' or no alert.")
                return False
        else: # Expecting no submission (due to 'wrong_input')
            if alert_text == "❌ Failure!":
                print("SUCCESS: '❌ Failure!' alert received as expected, form not submitted.")
                # Ensure we are still on the form page (or it hasn't navigated away)
                if "results.html" not in page.url:
                    print("Stayed on form page as expected.")
                    return True
                else:
                    print(f"FAILURE: '❌ Failure!' alert received, but navigated to {page.url}")
                    return False
            else:
                print(f"FAILURE: Expected '❌ Failure!' alert for '{input_value}', but got '{alert_text}' or no alert.")
                return False

    # Scenario 1: Input "wrong_input" (expect failure alert, no submission)
    test_1_success = await test_form_scenario(input_value="wrong_input", expect_submission=False)
    print(f"Test 1 Result (wrong_input): {'Passed' if test_1_success else 'Failed'}")

    # Scenario 2: Input valid data (expect success alert, submission)
    test_2_success = await test_form_scenario(input_value="correct_input", expect_submission=True)
    print(f"Test 2 Result (correct_input): {'Passed' if test_2_success else 'Failed'}")

    print("\nAll scenarios tested. Closing browser.")
    await browser.close()

async def main():
    async with async_playwright() as playwright:
        await run(playwright)

if __name__ == "__main__":
    asyncio.run(main()) 