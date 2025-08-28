import os, json
from dotenv import load_dotenv

def main():
    load_dotenv(os.path.join("configs",".env"))
    checks = {}

    # MT5
    from broker import mt5
    ok = mt5.init()
    checks["mt5_init"] = ok
    checks["mt5_last_error"] = mt5.last_error()
    mt5.shutdown()

    # TwelveData
    from data.twelvedata import price
    sym = os.getenv("TWELVEDATA_SYMBOL") or os.getenv("SYMBOL","BTCUSD")
    checks["twelvedata_price"] = price(sym)

    # Telegram
    import requests
    tok = os.getenv("TELEGRAM_TOKEN"); chat = os.getenv("TELEGRAM_CHAT_ID")
    if tok and chat:
        try:
            r = requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                              data={"chat_id":chat,"text":" verify_system OK"}, timeout=10)
            checks["telegram_status"] = r.status_code
        except Exception as e:
            checks["telegram_status"] = f"err: {e}"
    else:
        checks["telegram_status"] = "no_token_or_chat"

    print(json.dumps(checks, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
