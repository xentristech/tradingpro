import os, requests
from dotenv import load_dotenv
load_dotenv(os.path.join("configs",".env"))

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT  = os.getenv("TELEGRAM_CHAT_ID")
assert TOKEN and CHAT, "Falta TELEGRAM_TOKEN o TELEGRAM_CHAT_ID"

r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                  data={"chat_id":CHAT,"text":" Test Telegram OK"}, timeout=10)
print("status:", r.status_code, "body:", r.text)
