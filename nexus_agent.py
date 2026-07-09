import os
import time
import asyncio
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# LangChain & LangGraph Imports
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import ToolNode

from tavily import TavilyClient
from playwright.async_api import async_playwright


# ==========================================
# 🔐 CONFIGURATION & API KEYS (PASTE THESE)
# ==========================================
GROQ_API_KEY = "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"
TAVILY_API_KEY = "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"
TELEGRAM_TOKEN = "8735988658:AAG0gEKeDMNnJz7eDDYqjLRLvdbx5lyUNwo"
CHAT_ID = "8725045791"
GEMINI_API_KEY = "AIzaSyDGyKZOU9GiGmhMRx2cydb0DokGWfVAYZY"

os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# ==========================================
# 🛠️ LANGCHAIN TOOLS
# ==========================================
@tool
def search_web(query: str) -> str:
    """
    Searches the internet for AI news, Reddit discussions, and community reviews.
    Returns search results with URLs and summaries. Use this FIRST to find trends or Reddit discussions.
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
    print(f"📄 [TOOL] Reading link: '{url}'")
    time.sleep(5)
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        html = requests.get(url, headers=headers, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        clean_text = soup.get_text(separator=' ', strip=True)
        return clean_text[:8000] # Return up to 8,000 chars to avoid context overflow
    except Exception as e:
        return f"Failed to read webpage: {e}"

# ==========================================
# 🧠 LANGGRAPH AGENT ORCHESTRATION
# ==========================================
def build_langgraph_agent():
    # 1. Initialize the LLM and bind the tools
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
    tools = [search_web, read_webpage]
    llm_with_tools = llm.bind_tools(tools)

    # 2. Define the Agent Node
    def agent_node(state: MessagesState):
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    # 3. Define the Conditional Edge Logic
    def should_continue(state: MessagesState):
        messages = state["messages"]
        last_message = messages[-1]
        # If the LLM decided to call a tool, route to "tools"
        if last_message.tool_calls:
            return "tools"
        # Otherwise, the LLM has written the final post, route to END
        return END

    # 4. Construct the Graph
    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools)) # Built-in LangGraph node for executing tools
    
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent") # After tools run, go back to the agent

    return workflow.compile()

def draft_linkedin_post():
    print("🕸️ Activating LangGraph ReAct Agent...")
    
    app = build_langgraph_agent()
    
    today = datetime.now()
    last_week = today - timedelta(days=7)
    date_context = f"CURRENT DATE: {today.strftime('%B %d, %Y')}. Focus on news between {last_week.strftime('%B %d, %Y')} and today."

    system_prompt = f"""
    You are Harman Papneja, a Senior AI/ML Software Engineer building Agentic Workflows.
    
    {date_context}
    
    YOUR LANGGRAPH RE-ACT WORKFLOW:
    1. PHASE 1 (DISCOVERY): Call `search_web` to find the broadest AI/ML model releases from the past 7 days.
    2. PHASE 2 (DEEP READ): If you find a highly impactful URL in Phase 1, call `read_webpage` to extract exact benchmarks/specs.
    3. PHASE 3 (COMMUNITY CHECK): Call `search_web` AGAIN with "site:reddit.com" to find developer reactions/bugs to this specific release.
    4. PHASE 4 (SYNTHESIS): Draft the LinkedIn post using the data you collected.

    LINKEDIN ALGORITHM RULES (DO NOT IGNORE):
    1. THE HOOK: Start with the community reaction/benchmark flaw.
    2. SHOW, DON'T TELL: Relate the news to your own experience. Say: "I faced a similar issue while engineering the 'Agentic Job Applier'..." or "When building the SENSE AI backend at Altruist..."
    3. THE FIX: Provide a technical insight (context-caching, LCEL, RAG embeddings).
    4. TONE: Sound human, slightly casual but highly technical. Use "I", "my take", "honestly".
    5. BANNED WORDS: "Delve", "Crucial", "In today's rapidly evolving", "Excited to share", "Revolutionize".
    6. FORMAT: High whitespace. Maximum 1-2 sentences per paragraph. NO bolding excessive words.
    7. ENDING: End with a technical question for the community and exactly 4 hashtags.
    """

    print("⏳ LangGraph state machine initialized. Executing cyclic reasoning...")
    
    # We start the graph by passing the system message and user command into the state
    inputs = {
        "messages":[
            SystemMessage(content=system_prompt),
            HumanMessage(content="Execute your 4-Phase workflow. Search news, read docs if needed, check Reddit, and output the final LinkedIn draft.")
        ]
    }
    
    # Run the graph and get the final state
    final_state = app.invoke(inputs)
    
    # The final message in the state is the drafted post
    return final_state["messages"][-1].content

# ==========================================
# 📲 STEP 2: HUMAN-IN-THE-LOOP (TELEGRAM)
# ==========================================
def get_last_telegram_update_id():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    response = requests.get(url).json()
    if response.get("ok") and response["result"]:
        return response["result"][-1]["update_id"]
    return 0

def ask_for_approval(post_text):
    print("📲 Sending draft to Telegram for your approval...")
    last_update_id = get_last_telegram_update_id()
    
    message = f"🤖 Nexus Agent Draft Ready:\n\n{post_text}\n\n👉 Reply 'YES' to post to LinkedIn. (Reply anything else to cancel)."
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": message})
        
    print("⏳ Waiting for you to reply 'YES' on Telegram...")
    while True:
        time.sleep(3)
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_update_id + 1}"
        update_response = requests.get(url).json()
        
        if update_response.get("ok") and update_response["result"]:
            for update in update_response["result"]:
                last_update_id = update["update_id"]
                if "message" in update and "text" in update["message"]:
                    user_reply = update["message"]["text"].strip().upper()
                    if user_reply == "YES":
                        print("✅ You approved the post!")
                        return True
                    else:
                        print("❌ Post cancelled.")
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": "Draft cancelled."})
                        return False

# ==========================================
# 🚀 STEP 3: POSTING TO LINKEDIN (PLAYWRIGHT)
# ==========================================
async def post_to_linkedin(post_text):
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

# ==========================================
# ⚙️ MAIN AGENTIC LOOP
# ==========================================
def run_agent():
    draft = draft_linkedin_post()
    approved = ask_for_approval(draft)
    if approved:
        asyncio.run(post_to_linkedin(draft))

if __name__ == "__main__":
    run_agent()