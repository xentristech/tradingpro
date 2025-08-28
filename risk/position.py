def should_move_to_breakeven(rvol: float, rvol_thresh: float = 0.9) -> bool:
    """
    Mover a BE si el volumen relativo cae por debajo de un umbral
    (ej. sesión pierde impulso).
    """
    try:
        return float(rvol) <= float(rvol_thresh)
    except Exception:
        return False
