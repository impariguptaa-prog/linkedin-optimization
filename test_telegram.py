import requests

# Paste your Token and ID here
TELEGRAM_TOKEN = "8735988658:AAG0gEKeDMNnJz7eDDYqjLRLvdbx5lyUNwo"
CHAT_ID = "8725045791"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        print("✅ Message sent successfully to your Telegram!")
    else:
        print("❌ Error:", response.text)

if __name__ == "__main__":
    send_telegram_message("🤖 *Nexus Agent Online:* Hello Harman! The secure bridge is active. I am ready to start analyzing Gen AI news for your LinkedIn.")
