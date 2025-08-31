import os
import requests
import logging
from typing import Optional

TOKEN: Optional[str] = os.getenv("TELEGRAM_TOKEN")
CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")

def send_message(text: str, parse_mode: Optional[str] = "Markdown") -> bool:
    if not TOKEN or not CHAT_ID:
        logging.warning("Telegram: faltan TELEGRAM_TOKEN o TELEGRAM_CHAT_ID")
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text, "parse_mode": parse_mode},
            timeout=10,
        )
        if r.status_code != 200:
            logging.error("Telegram error %s: %s", r.status_code, r.text)
            return False
        return True
    except Exception as e:
        logging.exception("Telegram exception: %s", e)
        return False
