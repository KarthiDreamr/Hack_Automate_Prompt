from playwright.async_api import Playwright, Browser, Page

CDP_ENDPOINT = "http://localhost:9222" # Make sure this matches the port you launched Brave with

async def get_browser_page(playwright: Playwright, connect_to_existing: bool = True) -> tuple[Browser | None, Page | None]:
    """Connects to an existing browser or launches a new one, and returns a page object."""
    browser = None
    page = None
    try:
        if connect_to_existing:
            print(f"Attempting to connect to browser over CDP: {CDP_ENDPOINT}")
            browser = await playwright.chromium.connect_over_cdp(CDP_ENDPOINT)
            if browser.contexts:
                context = browser.contexts[0]
                if context.pages:
                    page = context.pages[0]
                    print("Using the first existing page in the first context.")
                else:
                    page = await context.new_page()
                    print("No existing pages found in the first context, created a new one.")
            else:
                print("No existing contexts found. Attempting to create a new context and page.")
                context = await browser.new_context() # Should ideally not happen with connect_over_cdp to a running browser
                page = await context.new_page()
            print("Successfully connected to existing browser and obtained a page.")
        else:
            print("Launching a new browser instance.")
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            print("Successfully launched new browser and obtained a page.")
        return browser, page
    except Exception as e:
        print(f"Error in browser_manager.get_browser_page: {e}")
        if connect_to_existing:
             print("Please ensure Browser is running and launched with --remote-debugging-port=9222 (or your chosen port).")
        if browser and browser.is_connected(): # Clean up if partial connection occurred
            await browser.close()
        return None, None 