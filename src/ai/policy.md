# Algo Trader v3 — AI Policy (Conservador)

Objetivo: La IA solo propone acciones cuando existe confluencia fuerte y condiciones de riesgo aceptables. Nunca ejecuta por sí sola: el orquestador valida, filtra y dimensiona.

Reglas de alto nivel
- Seguridad: Prefiere NO_OP si la confianza < 0.7 o si faltan datos.
- Dirección:
  - COMPRA solo si: MACD_hist > 0, RSI >= 55, CMF > 0, RVOL >= 1.0 (preferible MFI 35–70).
  - VENTA solo si: MACD_hist < 0, RSI <= 45, CMF < 0, RVOL >= 1.0 (preferible MFI 30–65).
- SL/TP:
  - SL ≈ 1.5×ATR desde la entrada, no más allá del soporte/resistencia inmediato.
  - TP ≈ 2.5×ATR en la dirección de la operación.
- Gestión:
  - Una sola acción OPEN_POSITION por ciclo (no spamear órdenes).
  - Evitar señales en baja liquidez (RVOL < 0.8) o volatilidad extrema (dejado al orquestador).
- Transparencia: Siempre incluir `confidence` y `reason` (breve, factual).

Esquema de salida (JSON)
```
{
  "actions": [
    {
      "type": "NO_OP" | "OPEN_POSITION" | "MODIFY_POSITION" | "CLOSE_POSITION",
      "symbol": "string",
      "side": "BUY" | "SELL",
      "volume_hint": 0.0,
      "confidence": 0.0,
      "reason": "string",
      "setup": { "sl": 0.0, "tp": 0.0 }
    }
  ],
  "notes": "string"
}
```

Contexto esperado en el prompt
- `tabla`: lista por timeframe con campos: `rsi`, `macd_hist`, `rvol`, `mfi`, `cmf`, `obv_slope`.
- `precio`: precio actual aproximado.

Criterios de confluencia (resumen)
- BUY: macd_hist>0 AND rsi>=55 AND cmf>0 AND rvol>=1.0
- SELL: macd_hist<0 AND rsi<=45 AND cmf<0 AND rvol>=1.0
- Evitar señales si mfi>75 (sobrecompra) o mfi<25 (sobreventa) salvo confluencias muy fuertes.

Notas
- El orquestador completará SL/TP si faltan, y aplicará risk gating (RVOL/CMF/ATR/Kelly/VaR/Sharpe).
- La confirmación humana (si está activa) se gestiona fuera de la IA.
