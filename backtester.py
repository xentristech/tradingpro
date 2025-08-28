import os, math, json
from dotenv import load_dotenv
from signals.rules import basic_rule_from_indicators

def main():
    load_dotenv(os.path.join("configs",".env"))
    # Placeholder: aquí cargarías velas históricas y aplicarías la regla
    # Dejamos un ejemplo sintético:
    samples = [
        {"rsi":30, "macd_hist":-0.5, "rvol":1.2},
        {"rsi":55, "macd_hist":0.1,  "rvol":0.9},
        {"rsi":75, "macd_hist":0.7,  "rvol":1.5},
    ]
    results = []
    for s in samples:
        rd = basic_rule_from_indicators(s["rsi"], s["macd_hist"], s["rvol"])
        results.append({"in": s, "rule": rd.dict()})
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
