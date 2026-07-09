import asyncio
from playwright.async_api import async_playwright

async def scrape_my_posts():
    async with async_playwright() as p:
        # Load the saved session state (NO LOGIN REQUIRED NOW!)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state="linkedin_state.json")
        page = await context.new_page()

        print("Going to your recent activity...")
        await page.goto("https://www.linkedin.com/in/me/recent-activity/shares/")
        
        # Wait for the posts to load on the page
        await page.wait_for_timeout(5000)
        
        # Scroll down to load a few posts
        await page.evaluate("window.scrollBy(0, 2000)")
        await page.wait_for_timeout(3000)

        print("\n--- EXTRACTING YOUR RECENT POSTS ---\n")
        
        # Find the post containers
        posts = await page.query_selector_all('.profile-creator-shared-feed-update__container')
        
        if not posts:
            print("No posts found. LinkedIn might have changed their layout. Let me know!")
            
        for i, post in enumerate(posts[:5]): # Get top 5 recent posts
            try:
                # Extract text
                text_element = await post.query_selector('.break-words')
                text = await text_element.inner_text() if text_element else "No text"
                
                # Extract Likes & Comments
                social_element = await post.query_selector('.social-details-social-counts')
                social_stats = await social_element.inner_text() if social_element else "No stats"
                
                print(f"POST {i+1}:")
                print(f"CONTENT: {text[:200]}...") # Print first 200 characters
                print(f"ENGAGEMENT: {social_stats.replace(chr(10), ' ')}")
                print("-" * 50)
            except Exception as e:
                print(f"Could not parse post {i+1}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_my_posts())