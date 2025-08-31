import os, requests
from dotenv import load_dotenv

# Cargar credenciales desde configs/.env
load_dotenv(os.path.join("configs", ".env"))

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT:
    raise RuntimeError("❌ Falta TELEGRAM_TOKEN o TELEGRAM_CHAT_ID en configs/.env")

print("[i] TOKEN y CHAT_ID cargados correctamente")

# Enviar un mensaje de prueba
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {
    "chat_id": CHAT,
    "text": "✅ Test Telegram OK desde bot",
}
try:
    r = requests.post(url, data=payload, timeout=10)
    print("status:", r.status_code, "body:", r.text)
except Exception as e:
    print("❌ Error al enviar mensaje:", e)
