import time
import requests
from config import TELEGRAM_TOKEN, CHAT_ID

def get_last_telegram_update_id():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        response = requests.get(url).json()
        if response.get("ok") and response["result"]:
            return response["result"][-1]["update_id"]
    except Exception as e:
        print(f"⚠️ Error getting Telegram updates: {e}")
    return 0

def ask_for_approval(post_text: str) -> bool:
    print("📲 [TELEGRAM] Processing draft for delivery...")
    
    if not post_text:
        print("❌ Error: Draft is empty!")
        return False

    last_update_id = get_last_telegram_update_id()
    
    # 1. Prepare the full content
    header = "🤖 NEXUS AGENT DRAFT READY\n==========================\n\n"
    footer = "\n\n==========================\n👉 Reply 'YES' to post. (Any other reply to cancel)."
    full_content = header + post_text + footer

    # 2. Chunking Logic (Telegram limit is 4096, we use 3800 for safety)
    MAX_LENGTH = 3800
    chunks = [full_content[i:i+MAX_LENGTH] for i in range(0, len(full_content), MAX_LENGTH)]
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    try:
        for i, chunk in enumerate(chunks):
            # If there are multiple chunks, add a page marker
            current_text = chunk
            if len(chunks) > 1:
                current_text = f"[PART {i+1}/{len(chunks)}]\n" + chunk

            response = requests.post(url, json={"chat_id": CHAT_ID, "text": current_text})
            
            if response.status_code != 200:
                print(f"❌ [TELEGRAM] API Error {response.status_code}: {response.text}")
                return False
            
            # Small delay to keep messages in order
            time.sleep(1)

        print(f"✅ [TELEGRAM] Draft delivered in {len(chunks)} message(s).")
        
    except Exception as e:
        print(f"❌ [TELEGRAM] Connection Error: {e}")
        return False
        
    print("⏳ Waiting for your reply 'YES' on Telegram...")
    
    # 3. Polling for Approval
    while True:
        time.sleep(3)
        poll_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_update_id + 1}"
        try:
            update_response = requests.get(poll_url).json()
            if update_response.get("ok") and update_response["result"]:
                for update in update_response["result"]:
                    last_update_id = update["update_id"]
                    if "message" in update and "text" in update["message"]:
                        user_reply = update["message"]["text"].strip().upper()
                        
                        if user_reply == "YES":
                            print("✅ [TELEGRAM] Received Approval!")
                            return True
                        else:
                            print("❌ [TELEGRAM] Received Cancellation.")
                            requests.post(url, json={"chat_id": CHAT_ID, "text": "🛑 Post cancelled by user."})
                            return False
        except Exception as e:
            print(f"⚠️ Polling error: {e}")
            time.sleep(5)