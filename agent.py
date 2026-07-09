# agent.py
from datetime import datetime, timedelta
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import ToolNode

from tools import agent_tools

def build_langgraph_agent():
    # Use 'gemini-1.5-flash-latest' as it is the most stable for tool-calling APIs
    # and prevents the 404 errors seen in some environments.
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=1)
    llm_with_tools = llm.bind_tools(agent_tools)

    def agent_node(state: MessagesState):
        response = llm_with_tools.invoke(state["messages"])
        
        # Anti-Null Nudge: Ensures the agent doesn't stop prematurely
        if not getattr(response, "tool_calls", None) and (not response.content or str(response.content).strip() == ""):
            nudge = HumanMessage(content="You returned a blank message. If you have finished research, write the post. If not, use the next mandatory tool.")
            response = llm_with_tools.invoke(state["messages"] + [response, nudge])
            
        return {"messages": [response]}

    def should_continue(state: MessagesState):
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "tools"
        return END

    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(agent_tools))
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")

    return workflow.compile()

def get_system_prompt():
    today = datetime.now()
    date_context = f"CURRENT DATE: {today.strftime('%B %d, %Y')}."

    return f"""
    You are Harman Papneja, a Senior AI/ML Software Engineer and a specialist in Generative AI and LLMs.

    STRICT EXECUTION PROTOCOL (SINGLE TOPIC FOCUS):
    1. [DISCOVERY] Call `get_linkedin_trends` first. 
    
    2. [SELECTION - MANDATORY] Analyze the feed data. Pick exactly ONE specific technical AI topic, model (e.g. Anthropic Claude 3.7, GPT-5.5), or architecture shift. 
       - DISCARD all other news. Do NOT research multiple topics. Focus leads to precision.

    3. [VALIDATION] CALL `search_linkedin_posts` using that SINGLE specific name/keyword.
       - DO NOT call `search_web` before this. This is your most important rule.

    4. [TECHNICAL RESEARCH] Only after Step 3, use `search_web` and `read_webpage` as many times as you want to find the "Ground Truth" for that ONE topic:
       - Benchmarks (MMLU, GSM8K, HumanEval).
       - Context window limits, latency, and MoE architecture details.
       - Real developer reviews/complaints on Reddit or GitHub.

    5. [DRAFTING] Write the final post.

    LINKEDIN ALGORITHM & PERSONA RULES:
    - THE HOOK: "Everyone is talking about [Single Topic Name] on my feed, but the technical benchmarks show..."
    - SHOW, DON'T TELL: Connect to your projects (Agentic Job Applier / SENSE AI) ONLY if there is a direct technical link.
    - TONE: High-signal, low-noise, Senior Engineer persona. No marketing fluff.
    - NO BANNED WORDS: "Delve", "Crucial", "Landscape", "Revolutionize", "In today's world".

    CRITICAL CONSTRAINTS:
    - LENGTH: 1,300 - 1,700 characters. 
    - REASON: Shorter posts get higher 'dwell-time' percentage and ensure Telegram delivery.
    - OUTPUT: Plain text only.
    """

def draft_linkedin_post():
    print("🕸️ Activating Nexus Agent...")
    app = build_langgraph_agent()
    system_prompt = get_system_prompt()
    
    inputs = {
        "messages":[
            SystemMessage(content=system_prompt),
            HumanMessage(content="Start the protocol: Check my feed, pick the ONE best trend, search LinkedIn globally for it, then research and draft.")
        ]
    }
    
    # Recursion limit set to 20 to allow for multiple deep-dive search cycles
    final_state = app.invoke(inputs, {"recursion_limit": 20})
    
    draft = None
    for msg in reversed(final_state["messages"]):
        if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None) and msg.content and str(msg.content).strip():
            draft = msg.content
            break
            
    return draft if draft else "ERROR: Agent failed to generate text."