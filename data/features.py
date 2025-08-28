from typing import List
import numpy as np

def rvol_from_series(volumes: List[float], window: int = 20) -> float:
    if not volumes or len(volumes) < 2:
        return 1.0
    arr = np.array(volumes[-window:], dtype=float)
    cur = arr[-1]
    avg = arr.mean() if arr.size else 1.0
    return float(cur / avg if avg else 1.0)
