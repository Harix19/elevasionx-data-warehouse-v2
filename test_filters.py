#!/usr/bin/env python3
"""
Test script for Apollo-style filtering system
Tests: login, filter sidebar, filter application, URL persistence
"""
import asyncio
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:3000"
LOGIN_EMAIL = "sales@example.com"
LOGIN_PASSWORD = "salespass123"

async def test_companies_filter():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1400, 'height': 900})
        page = await context.new_page()
        
        print("🚀 Starting filter system tests...")
        
        # Step 1: Login
        print("\n[1/6] Testing login...")
        await page.goto(f"{BASE_URL}/login")
        await page.fill('input[name="email"]', LOGIN_EMAIL)
        await page.fill('input[name="password"]', LOGIN_PASSWORD)
        await page.click('button[type="submit"]')
        # Wait for redirect (login redirects to root "/")
        await page.wait_for_load_state('networkidle')
        current_url = page.url
        print(f"   Redirected to: {current_url}")
        if '/login' not in current_url:
            print("✅ Login successful")
        else:
            print("⚠️ Still on login page - checking for errors...")
            error_elem = await page.query_selector('[class*="destructive"]')
            if error_elem:
                error_text = await error_elem.text_content()
                print(f"   Error: {error_text}")
        
        # Step 2: Navigate to companies page
        print("\n[2/6] Testing companies page...")
        await page.goto(f"{BASE_URL}/companies")
        await page.wait_for_load_state('networkidle')
        
        # Take screenshot of companies page
        await page.screenshot(path="test_results/01_companies_page.png", full_page=True)
        print("✅ Companies page loaded - screenshot saved")
        
        # Step 3: Check filter sidebar
        print("\n[3/6] Testing filter sidebar...")
        sidebar = await page.query_selector('[class*="filter-sidebar"]')
        if sidebar:
            print("✅ Filter sidebar found")
            # Check for filter groups
            industry_filter = await page.query_selector('text=Industry')
            country_filter = await page.query_selector('text=Country')
            revenue_filter = await page.query_selector('text=Revenue')
            
            if industry_filter and country_filter and revenue_filter:
                print("✅ All filter types present (Industry, Country, Revenue)")
            else:
                print("⚠️ Some filter types missing")
                print(f"   Industry: {bool(industry_filter)}, Country: {bool(country_filter)}, Revenue: {bool(revenue_filter)}")
        else:
            print("❌ Filter sidebar NOT found")
        
        # Step 4: Test applying filters
        print("\n[4/6] Testing filter application...")
        
        # Try to expand Industry filter and select an option
        try:
            industry_header = await page.query_selector('text=Industry')
            if industry_header:
                await industry_header.click()
                await asyncio.sleep(0.5)
                
                # Look for checkbox options
                checkboxes = await page.query_selector_all('input[type="checkbox"]')
                if checkboxes:
                    print(f"✅ Found {len(checkboxes)} filter checkboxes")
                    # Click first checkbox
                    await checkboxes[0].click()
                    await asyncio.sleep(1)
                    
                    # Check for active filter pill
                    active_filters = await page.query_selector('[class*="active-filters"]')
                    if active_filters:
                        print("✅ Active filters bar appeared")
                        await page.screenshot(path="test_results/02_filters_applied.png", full_page=True)
                    else:
                        print("⚠️ Active filters bar not found")
                else:
                    print("⚠️ No filter checkboxes found")
        except Exception as e:
            print(f"⚠️ Error testing filters: {e}")
        
        # Step 5: Test URL persistence
        print("\n[5/6] Testing URL persistence...")
        current_url = page.url
        if 'industry' in current_url or 'country' in current_url or 'revenue' in current_url:
            print(f"✅ URL contains filter params: {current_url}")
        else:
            print(f"⚠️ URL doesn't show filter params yet: {current_url}")
        
        # Step 6: Test contacts page
        print("\n[6/6] Testing contacts page...")
        await page.goto(f"{BASE_URL}/contacts")
        await page.wait_for_load_state('networkidle')
        
        await page.screenshot(path="test_results/03_contacts_page.png", full_page=True)
        
        sidebar = await page.query_selector('[class*="filter-sidebar"]')
        if sidebar:
            print("✅ Contacts page filter sidebar found")
        else:
            print("⚠️ Contacts page filter sidebar not found")
        
        print("\n✨ All tests completed!")
        print("📸 Screenshots saved in test_results/")
        
        await browser.close()

if __name__ == "__main__":
    import os
    os.makedirs("test_results", exist_ok=True)
    asyncio.run(test_companies_filter())
