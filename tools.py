import time
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from tavily import TavilyClient
from config import TAVILY_API_KEY
from playwright.sync_api import sync_playwright

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

@tool
def search_web(query: str) -> str:
    """
    Searches the internet for AI news, Reddit discussions, and community reviews.
    Returns search results with URLs and summaries. Use this FIRST to find trends.
    """
    print(f"🔍 [TOOL] Executing Web Search: '{query}'")
    time.sleep(8) # Anti-rate-limit pause
    try:
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=5
        )
        return "\n\n".join([f"Source: {res['url']}\nSummary: {res['content']}" for res in response['results']])
    except Exception as e:
        return f"Search failed: {e}"

@tool
def read_webpage(url: str) -> str:
    """
    Reads the full text content of a specific webpage URL.
    Use this when you find a specific link (like a blog or GitHub repo) from search_web that you need to read deeply.
    """
    print(f"📄[TOOL] Reading link: '{url}'")
    time.sleep(5)
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        html = requests.get(url, headers=headers, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        clean_text = soup.get_text(separator=' ', strip=True)
        return clean_text[:8000] # Return up to 8,000 chars to avoid context overflow
    except Exception as e:
        return f"Failed to read webpage: {e}"

@tool
def get_linkedin_trends() -> str:
    """
    MANDATORY FIRST STEP. Scrapes your personal LinkedIn feed. 
    You MUST call this to identify what your network is talking about.
    """
    print("🕵️‍♂️ [TOOL] Step 1: Scraping LinkedIn Feed...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state="linkedin_state.json")
            page = context.new_page()
            page.goto("https://www.linkedin.com/feed/")
            page.wait_for_timeout(4000)
            page.evaluate("window.scrollBy(0, 1000)")
            posts = page.locator('.feed-shared-update-v2').all()
            
            ai_keywords = ["AI", "GENAI", "LLM", "MODEL", "GPT", "CLAUDE", "ANTHROPIC", "GEMMA", "LLAMA", "DEEPSEEK"]
            feed_data = []
            for post in posts[:10]:
                text = post.inner_text().replace('\n', ' ')
                if any(k in text.upper() for k in ai_keywords):
                    feed_data.append(text[:600])
            browser.close()
            
            if not feed_data:
                return "No specific AI news in feed. ACTION: Use `search_web` to find a new model release from the last 24h."
                
            # --- THE GATEKEEPER INSTRUCTION ---
            return (
                f"FILTERED AI FEED DATA:\n{chr(10).join(feed_data)}\n\n"
                "⚠️ MANDATORY PROTOCOL:\n"
                "1. Identify the most talked-about AI model/topic from the data above.\n"
                "2. You MUST now use `search_linkedin_posts` for that keyword to see global sentiment.\n"
                "3. You are FORBIDDEN from using `search_web` or `read_webpage` until Step 2 is complete."
            )
    except Exception as e:
        return f"Error: {e}"

@tool
def search_linkedin_posts(keyword: str) -> str:
    """
    Performs a global search on LinkedIn for a specific keyword to see what the whole platform is saying.
    Use this AFTER get_linkedin_trends to get precise, platform-wide sentiment.
    """
    print(f"🌐 [TOOL] Searching LinkedIn globally for: '{keyword}'")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state="linkedin_state.json")
            page = context.new_page()
            
            # Navigate to LinkedIn Content Search
            search_url = f"https://www.linkedin.com/search/results/content/?keywords={keyword.replace(' ', '%20')}"
            page.goto(search_url)
            page.wait_for_timeout(5000)
            
            # Extract top search results
            posts = page.locator('.search-results-container .entity-result__content').all()
            results = [p.inner_text().replace('\n', ' ')[:500] for p in posts[:5]]
            browser.close()
            
            return f"GLOBAL LINKEDIN SEARCH RESULTS FOR '{keyword}':\n\n" + "\n".join(results)
    except Exception as e:
        return f"LinkedIn search failed: {e}"

agent_tools = [search_web, read_webpage, get_linkedin_trends, search_linkedin_posts]