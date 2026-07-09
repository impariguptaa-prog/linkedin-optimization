import requests
from playwright.async_api import async_playwright
from config import TELEGRAM_TOKEN, CHAT_ID

async def post_to_linkedin(post_text: str):
    print("🌐 Activating Playwright to post on LinkedIn...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="linkedin_state.json")
        page = await context.new_page()

        print("Navigating to LinkedIn feed...")
        await page.goto("https://www.linkedin.com/feed/")
        await page.wait_for_timeout(5000)

        try:
            print("Clicking 'Start a post'...")
            start_post_btn = page.get_by_role("button", name="Start a post")
            await start_post_btn.click()
            await page.wait_for_timeout(3000)

            print("Typing out the post...")
            textbox = page.get_by_role("textbox", name="Text editor for creating")
            await textbox.click()
            await page.keyboard.insert_text(post_text)
            await page.wait_for_timeout(3000)

            print("Clicking 'Post'...")
            post_btn = page.get_by_role("button", name="Post", exact=True)
            await post_btn.click()
            
            print("🎉 SUCCESS! Your AI Agent just posted to LinkedIn.")
            await page.wait_for_timeout(5000)
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": "✅ Successfully posted to LinkedIn!"})
        except Exception as e:
            print(f"❌ Playwright encountered an error: {e}")
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": f"❌ Playwright failed to post: {e}"})
        finally:
            await browser.close()