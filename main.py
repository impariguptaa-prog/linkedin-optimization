import asyncio
from agent import draft_linkedin_post
from telegram_bot import ask_for_approval
from linkedin_poster import post_to_linkedin

def run_agent():
    print("🚀 Nexus Agent Initialization...")
    
    # 1. Agent drafts the post autonomously
    draft = draft_linkedin_post()
    
    # 2. Human in the loop approval
    approved = ask_for_approval(draft)
    
    # 3. Post to LinkedIn
    if approved:
        asyncio.run(post_to_linkedin(draft))

if __name__ == "__main__":
    run_agent()