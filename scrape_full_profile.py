import asyncio
from playwright.async_api import async_playwright

async def scrape_full_profile():
    async with async_playwright() as p:
        # Load the saved session state
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state="linkedin_state.json")
        page = await context.new_page()

        print("🕵️ Going to your main LinkedIn profile to read your Bio, Experience, and Connections...")
        # Going to your main profile page
        await page.goto("https://www.linkedin.com/in/me/")
        await page.wait_for_timeout(5000)
        
        # Scroll to load all sections (Experience, Education, etc.)
        await page.evaluate("window.scrollBy(0, 1000)")
        await page.wait_for_timeout(2000)
        await page.evaluate("window.scrollBy(0, 1000)")
        await page.wait_for_timeout(2000)

        print("✅ Extracting profile data...")
        
        try:
            # Grab all the text from the main profile container
            main_content = await page.locator("main").inner_text()
            
            # Save it to a text file
            with open("my_profile_data.txt", "w", encoding="utf-8") as f:
                f.write("=== MY MAIN PROFILE (BIO, ABOUT, EXPERIENCE) ===\n")
                f.write(main_content)
                f.write("\n\n")
        except Exception as e:
            print("Could not scrape main profile:", e)

        print("🕵️ Going to your recent activity to analyze your posts...")
        await page.goto("https://www.linkedin.com/in/me/recent-activity/shares/")
        await page.wait_for_timeout(5000)
        await page.evaluate("window.scrollBy(0, 2000)")
        await page.wait_for_timeout(3000)

        try:
            posts = await page.query_selector_all('.profile-creator-shared-feed-update__container')
            
            with open("my_profile_data.txt", "a", encoding="utf-8") as f:
                f.write("=== MY RECENT POSTS & ENGAGEMENT ===\n")
                if not posts:
                    f.write("No posts found.\n")
                
                for i, post in enumerate(posts[:5]):
                    text_element = await post.query_selector('.break-words')
                    text = await text_element.inner_text() if text_element else "No text"
                    
                    social_element = await post.query_selector('.social-details-social-counts')
                    social_stats = await social_element.inner_text() if social_element else "No stats"
                    
                    f.write(f"\nPOST {i+1}:\n")
                    f.write(f"CONTENT: {text[:500]}...\n") # Grabbing up to 500 characters of the post
                    f.write(f"ENGAGEMENT: {social_stats.replace(chr(10), ' ')}\n")
                    f.write("-" * 50)
            print("✅ Posts extracted!")
            
            print("\n🎉 DONE! I have saved your entire profile to a file.")
            print("Look for 'my_profile_data.txt' in your folder.")

        except Exception as e:
            print("Could not scrape posts:", e)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_full_profile())