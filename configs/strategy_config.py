"""
CONFIGURACIÓN DE ESTRATEGIAS DE GESTIÓN
Define las reglas personalizadas para cada símbolo y condición de mercado
"""

# === CONFIGURACIÓN POR SÍMBOLO ===
SYMBOL_CONFIGS = {
    "BTCUSDm": {
        "breakeven": {
            "trigger_points": 20,      # Activar BE cuando gane 20 puntos
            "buffer_points": 2,        # Dejar 2 puntos de ganancia
            "auto_enable": True
        },
        "trailing": {
            "start_points": 30,        # Iniciar después de 30 puntos
            "distance_points": 15,     # Mantener a 15 puntos
            "step_points": 5,          # Actualizar cada 5 puntos
            "auto_enable": True
        },
        "partials": {
            "tp1": {"points": 25, "percent": 0.5},     # 50% a 25 puntos
            "tp2": {"points": 50, "percent": 0.25},    # 25% a 50 puntos
            "tp3": {"points": 100, "percent": 0.15},   # 15% a 100 puntos
            "auto_enable": True
        },
        "protection": {
            "max_loss_percent": 2,     # Máx pérdida 2% de cuenta
            "daily_loss_limit": 100,   # Máx pérdida diaria $100
            "secure_profit_at": 40,    # Asegurar ganancias a 40 puntos
            "secure_profit_min": 20    # Mínimo a proteger 20 puntos
        },
        "time_management": {
            "max_hours": 24,           # Cerrar después de 24h
            "reduce_risk_hours": 12,   # Reducir riesgo a las 12h
            "news_protection": True    # Cerrar antes de noticias
        }
    },
    
    "EURUSD": {
        "breakeven": {
            "trigger_points": 15,
            "buffer_points": 1,
            "auto_enable": True
        },
        "trailing": {
            "start_points": 20,
            "distance_points": 10,
            "step_points": 3,
            "auto_enable": True
        },
        "partials": {
            "tp1": {"points": 20, "percent": 0.5},
            "tp2": {"points": 40, "percent": 0.3},
            "tp3": {"points": 80, "percent": 0.1},
            "auto_enable": True
        },
        "protection": {
            "max_loss_percent": 1,
            "daily_loss_limit": 50,
            "secure_profit_at": 30,
            "secure_profit_min": 15
        },
        "time_management": {
            "max_hours": 12,
            "reduce_risk_hours": 6,
            "news_protection": True
        }
    },
    
    "XAUUSD": {  # ORO
        "breakeven": {
            "trigger_points": 50,
            "buffer_points": 5,
            "auto_enable": True
        },
        "trailing": {
            "start_points": 100,
            "distance_points": 50,
            "step_points": 10,
            "auto_enable": True
        },
        "partials": {
            "tp1": {"points": 100, "percent": 0.4},
            "tp2": {"points": 200, "percent": 0.3},
            "tp3": {"points": 400, "percent": 0.2},
            "auto_enable": True
        },
        "protection": {
            "max_loss_percent": 1.5,
            "daily_loss_limit": 75,
            "secure_profit_at": 150,
            "secure_profit_min": 75
        },
        "time_management": {
            "max_hours": 48,
            "reduce_risk_hours": 24,
            "news_protection": True
        }
    },
    
    # Configuración DEFAULT para símbolos no especificados
    "DEFAULT": {
        "breakeven": {
            "trigger_points": 20,
            "buffer_points": 2,
            "auto_enable": True
        },
        "trailing": {
            "start_points": 30,
            "distance_points": 15,
            "step_points": 5,
            "auto_enable": True
        },
        "partials": {
            "tp1": {"points": 30, "percent": 0.5},
            "tp2": {"points": 60, "percent": 0.25},
            "auto_enable": True
        },
        "protection": {
            "max_loss_percent": 2,
            "daily_loss_limit": 100,
            "secure_profit_at": 50,
            "secure_profit_min": 25
        },
        "time_management": {
            "max_hours": 24,
            "reduce_risk_hours": 12,
            "news_protection": False
        }
    }
}

# === REGLAS BASADAS EN CONDICIONES DE MERCADO ===
MARKET_RULES = {
    "high_volatility": {
        # Ajustes cuando ATR > 1.5% del precio
        "multipliers": {
            "breakeven_trigger": 1.3,
            "trailing_distance": 1.5,
            "partial_points": 1.2
        },
        "overrides": {
            "use_wider_stops": True,
            "reduce_position_size": 0.7
        }
    },
    
    "low_volatility": {
        # Ajustes cuando ATR < 0.5% del precio
        "multipliers": {
            "breakeven_trigger": 0.8,
            "trailing_distance": 0.7,
            "partial_points": 0.8
        },
        "overrides": {
            "use_tighter_stops": True,
            "increase_position_size": 1.2
        }
    },
    
    "trending_strong": {
        # Cuando hay tendencia fuerte (MA cruce > 0.5%)
        "multipliers": {
            "trailing_distance": 1.5,
            "partial_points": 1.3
        },
        "overrides": {
            "let_profits_run": True,
            "delay_partials": True
        }
    },
    
    "ranging": {
        # Mercado lateral
        "multipliers": {
            "breakeven_trigger": 0.7,
            "partial_points": 0.7
        },
        "overrides": {
            "quick_profits": True,
            "aggressive_partials": True
        }
    },
    
    "news_time": {
        # 30 min antes y después de noticias importantes
        "multipliers": {
            "all": 0.5  # Reducir todo a la mitad
        },
        "overrides": {
            "close_all": False,
            "no_new_trades": True,
            "tighten_stops": True
        }
    }
}

# === HORARIOS DE TRADING ÓPTIMOS ===
TRADING_SESSIONS = {
    "LONDON": {
        "start": "08:00",
        "end": "17:00",
        "timezone": "Europe/London",
        "best_for": ["EURUSD", "GBPUSD", "XAUUSD"],
        "multiplier": 1.1  # 10% más agresivo
    },
    "NEWYORK": {
        "start": "13:00",
        "end": "22:00",
        "timezone": "America/New_York",
        "best_for": ["EURUSD", "XAUUSD", "US30", "US500"],
        "multiplier": 1.15
    },
    "TOKYO": {
        "start": "00:00",
        "end": "09:00",
        "timezone": "Asia/Tokyo",
        "best_for": ["USDJPY", "AUDUSD"],
        "multiplier": 1.0
    },
    "OVERLAP_LN_NY": {
        # Mejor momento del día
        "start": "13:00",
        "end": "17:00",
        "timezone": "Europe/London",
        "best_for": ["ALL"],
        "multiplier": 1.2  # 20% más agresivo
    }
}

# === NIVELES PSICOLÓGICOS ===
PSYCHOLOGICAL_LEVELS = {
    "BTCUSDm": [
        100000, 110000, 115000, 118000, 120000, 125000, 130000
    ],
    "EURUSD": [
        1.0000, 1.0500, 1.1000, 1.1500, 1.2000
    ],
    "XAUUSD": [
        2000, 2500, 2600, 2700, 2800, 3000
    ]
}

# === CONFIGURACIÓN DE NOTIFICACIONES ===
NOTIFICATIONS = {
    "telegram": {
        "on_breakeven": True,
        "on_trailing": True,
        "on_partial": True,
        "on_protection": True,
        "on_close": True,
        "summary_interval": 3600  # Cada hora
    },
    "sound_alerts": {
        "on_profit": True,
        "on_loss": True,
        "on_breakeven": True
    },
    "email": {
        "daily_report": True,
        "on_important_events": True
    }
}

# === GESTIÓN DE RIESGO GLOBAL ===
RISK_MANAGEMENT = {
    "max_positions": 3,
    "max_risk_per_trade": 1.0,  # 1% de la cuenta
    "max_daily_risk": 3.0,      # 3% máximo diario
    "max_weekly_risk": 5.0,     # 5% máximo semanal
    "max_monthly_risk": 10.0,   # 10% máximo mensual
    
    "correlation_limits": {
        # No abrir más de X posiciones correlacionadas
        "same_currency": 2,
        "same_direction": 3
    },
    
    "equity_protection": {
        "stop_trading_at_drawdown": 10,  # Detener si DD > 10%
        "reduce_size_at_drawdown": 5,    # Reducir tamaño si DD > 5%
        "increase_size_after_wins": 3    # Aumentar después de 3 wins
    }
}

# === OPTIMIZACIÓN POR MACHINE LEARNING ===
ML_OPTIMIZATION = {
    "enabled": True,
    "learn_from_history": True,
    "adjust_parameters": True,
    
    "optimization_targets": [
        "maximize_profit_factor",
        "minimize_drawdown",
        "maximize_win_rate"
    ],
    
    "backtesting": {
        "period_days": 365,
        "min_trades": 100,
        "confidence_level": 0.95
    }
}

# === INDICADORES PARA DECISIONES ===
INDICATORS_CONFIG = {
    "rsi": {
        "period": 14,
        "overbought": 70,
        "oversold": 30,
        "use_for_exits": True
    },
    "atr": {
        "period": 14,
        "multiplier_for_sl": 2.0,
        "multiplier_for_tp": 3.0
    },
    "moving_averages": {
        "fast": 20,
        "slow": 50,
        "trend": 200
    },
    "volume": {
        "use_volume_profile": True,
        "min_volume_ratio": 1.2
    }
}
