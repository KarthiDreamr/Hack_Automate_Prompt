#!/usr/bin/env python3
"""
Simple test script for model selection from dropdown.
This script connects to your existing browser instance to test model selection.
"""

import asyncio
import logging
from playwright.async_api import async_playwright

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_model_selection():
    """Test the model selection functionality by connecting to existing browser."""
    
    # Model to test
    model_name = "fair river"
    
    async with async_playwright() as playwright:
        # Connect to existing browser
        print("Connecting to existing browser at http://localhost:9222...")
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
        
        # Get the first page (or you can specify which one)
        pages = browser.contexts[0].pages
        if pages:
            page = pages[0]  # Use the first page
            print(f"✅ Connected to existing page with URL: {page.url}")
        else:
            print("❌ No pages found in existing browser")
            return
        
        print(f"Testing model selection for: {model_name}")
        
        # Strategy 1: Look for button with specific class and aria attributes
        print("\n🔍 Strategy 1: Looking for button with specific class and aria attributes...")
        dropdown_button = page.locator('button[aria-haspopup="menu"][data-state="closed"]:not([data-testid="user-menu-trigger"])')
        if await dropdown_button.count() > 0:
            print(f"✅ Found {await dropdown_button.count()} dropdown button(s) with aria-haspopup='menu' and data-state='closed' (excluding user menu)")
            button = dropdown_button.first
            button_text = await button.text_content()
            print(f"Button text: {button_text[:50]}...")
            
            # Click to open dropdown
            print("Clicking dropdown button...")
            await button.click()
            await asyncio.sleep(1)
            
            # Check if dropdown opened
            if await page.locator('div[role="menu"]').count() > 0:
                print("✅ Dropdown opened successfully!")
                await test_model_selection_in_dropdown(page, model_name)
            else:
                print("❌ Dropdown did not open")
        else:
            print("❌ Strategy 1 failed")
            
            # Strategy 2: Look for button with specific styling classes
            print("\n🔍 Strategy 2: Looking for button with specific styling...")
            dropdown_button = page.locator('button.z-20[aria-haspopup="menu"]:not([data-testid="user-menu-trigger"])')
            if await dropdown_button.count() > 0:
                print(f"✅ Found {await dropdown_button.count()} dropdown button(s) with z-20 class and aria-haspopup='menu' (excluding user menu)")
                button = dropdown_button.first
                button_text = await button.text_content()
                print(f"Button text: {button_text[:50]}...")
                
                # Click to open dropdown
                print("Clicking dropdown button...")
                await button.click()
                await asyncio.sleep(1)
                
                # Check if dropdown opened
                if await page.locator('div[role="menu"]').count() > 0:
                    print("✅ Dropdown opened successfully!")
                    await test_model_selection_in_dropdown(page, model_name)
                else:
                    print("❌ Dropdown did not open")
            else:
                print("❌ Strategy 2 failed")
                
                # Strategy 3: Look for button containing bot icon and chevron
                print("\n🔍 Strategy 3: Looking for button with bot icon and chevron...")
                dropdown_button = page.locator('button:has(svg.lucide-bot):has(svg.lucide-chevron-down):not([data-testid="user-menu-trigger"])')
                if await dropdown_button.count() > 0:
                    print(f"✅ Found {await dropdown_button.count()} dropdown button(s) with bot icon and chevron (excluding user menu)")
                    button = dropdown_button.first
                    button_text = await button.text_content()
                    print(f"Button text: {button_text[:50]}...")
                    
                    # Click to open dropdown
                    print("Clicking dropdown button...")
                    await button.click()
                    await asyncio.sleep(1)
                    
                    # Check if dropdown opened
                    if await page.locator('div[role="menu"]').count() > 0:
                        print("✅ Dropdown opened successfully!")
                        await test_model_selection_in_dropdown(page, model_name)
                    else:
                        print("❌ Dropdown did not open")
                else:
                    print("❌ Strategy 3 failed")
                    
                    # Strategy 4: Look for any button with aria-haspopup="menu" and filter by content
                    print("\n🔍 Strategy 4: Looking for any aria-haspopup button and filtering...")
                    all_aria_buttons = page.locator('button[aria-haspopup="menu"]:not([data-testid="user-menu-trigger"])')
                    print(f"Found {await all_aria_buttons.count()} buttons with aria-haspopup='menu' (excluding user menu)")
                    
                    for i in range(await all_aria_buttons.count()):
                        button = all_aria_buttons.nth(i)
                        text = await button.text_content()
                        print(f"Button {i}: {text[:30]}...")
                        
                        # Check if this looks like a model dropdown (contains model-like text)
                        if any(word in text.lower() for word in ["fair", "river", "gentle", "window", "optimistic", "bird", "nice", "breeze", "dazzling", "stream", "happy", "echo", "yellow", "mountain"]):
                            print(f"✅ This looks like the model dropdown: {text[:30]}...")
                            
                            # Click to open dropdown
                            print("Clicking dropdown button...")
                            await button.click()
                            await asyncio.sleep(1)
                            
                            # Check if dropdown opened
                            if await page.locator('div[role="menu"]').count() > 0:
                                print("✅ Dropdown opened successfully!")
                                await test_model_selection_in_dropdown(page, model_name)
                                break
                            else:
                                print("❌ Dropdown did not open")
        
        # Wait a bit to see the result
        print("\n⏳ Waiting 3 seconds to see the result...")
        await asyncio.sleep(3)
        
        print("Test completed. Browser remains open.")

async def test_model_selection_in_dropdown(page, model_name):
    """Test selecting a model from the opened dropdown."""
    print(f"\n🎯 Testing model selection for: {model_name}")
    
    # Look for dropdown menu
    dropdown_menu = page.locator('div[role="menu"]')
    if await dropdown_menu.count() > 0:
        print(f"✅ Found dropdown menu")
        
        # Look for model items
        model_items = page.locator('div[role="menuitem"]')
        print(f"Found {await model_items.count()} menu items")
        
        # List available models (just the names, not full content)
        print("Available models:")
        for j in range(await model_items.count()):
            item = model_items.nth(j)
            text = await item.text_content()
            # Extract just the model name (first line or first meaningful text)
            model_name_clean = text.split('\n')[0].strip()[:30]  # First line, max 30 chars
            print(f"  - {model_name_clean}")
        
        # Try to find specific model
        target_model = page.locator(f'div[role="menuitem"]:has-text("{model_name}")')
        if await target_model.count() > 0:
            print(f"✅ Found target model: {model_name}")
            await target_model.click()
            print(f"✅ Clicked on model: {model_name}")
        else:
            print(f"❌ Could not find model: {model_name}")
    else:
        print("❌ Dropdown menu not found")

if __name__ == "__main__":
    print("Starting model selection test...")
    asyncio.run(test_model_selection())
    print("Test completed.")


