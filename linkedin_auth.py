import asyncio
from playwright.async_api import async_playwright

async def login_and_save_state():
    async with async_playwright() as p:
        # Launch browser in headed mode so you can see it
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("Navigating to LinkedIn...")
        await page.goto("https://www.linkedin.com/login")

        print("\n" + "="*50)
        print("*** MANUAL ACTION REQUIRED ***")
        print("1. Log into LinkedIn in the browser window.")
        print("2. Solve any CAPTCHAs if asked.")
        print("3. Once you see your LinkedIn Feed, come back to this terminal.")
        print("="*50 + "\n")
        
        # This will wait forever until you literally press ENTER in the terminal
        await asyncio.get_event_loop().run_in_executor(None, input, "Press ENTER right here in the terminal once you are logged in... ")

        # Save the cookies to a file
        state_file = "linkedin_state.json"
        await context.storage_state(path=state_file)
        
        print(f"\n✅ Session saved successfully to {state_file}!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(login_and_save_state())