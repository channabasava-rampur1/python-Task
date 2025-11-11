import hmac, hashlib, time, urllib.parse as up
from typing import Dict, Any

def sign_params(secret: str, params: Dict[str, Any]) -> str:
    qs = up.urlencode({k: v for k, v in params.items() if v is not None}, doseq=True)
    sig = hmac.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    return qs + "&signature=" + sig

def now_ms() -> int:
    return int(time.time() * 1000)

def round_step(value: float, step: float) -> float:
    # robust rounding to tick/lot steps
    import math
    precision = max(0, -int(round(math.log10(step))))
    rounded = (int(round(value / step)) * step)
    return round(rounded, precision)
