from signals.schemas import RuleDecision

def basic_rule_from_indicators(rsi: float, macd_hist: float, rvol: float) -> RuleDecision:
    """
    Sencilla combinación:
    - RSI < 35 y MACD hist subiendo -> sesgo BUY
    - RSI > 65 y MACD hist bajando -> sesgo SELL
    - Ajuste por rVOL: rvol>1.2 aumenta convicción, rvol<0.8 la reduce
    """
    bias = "NEUTRAL"
    strength = 0.0

    if rsi < 35 and macd_hist > -0.2:
        bias = "BUY"
        strength = (35 - rsi)/35 + max(0.0, macd_hist + 0.2)
    elif rsi > 65 and macd_hist < 0.2:
        bias = "SELL"
        strength = (rsi - 65)/35 + max(0.0, 0.2 - macd_hist)
    else:
        bias = "NEUTRAL"
        strength = 0.1

    if rvol > 1.2:
        strength *= 1.2
    elif rvol < 0.8:
        strength *= 0.7

    return RuleDecision(bias=bias, strength=float(round(strength, 3)))
