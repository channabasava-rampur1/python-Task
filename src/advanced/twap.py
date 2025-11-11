import math, time
from typing import Dict, Any
from ..client import BinanceFuturesREST
from ..logger import get_logger
from ..validators import extract_filters, validate_qty

log = get_logger("TWAP")

def place_twap(client: BinanceFuturesREST, symbol: str, side: str, total_qty: float,
               slices: int = 5, interval_sec: float = 5.0) -> Dict[str, Any]:
    """
    Simple TWAP using MARKET orders split evenly across time.
    """
    client.sync_time()
    info = client.exchange_info(symbol=symbol)
    sym = next((s for s in info["symbols"] if s["symbol"] == symbol), None)
    if not sym:
        raise ValueError(f"Symbol {symbol} not found")
    fil = extract_filters(sym)

    # Evenly split qty
    slice_qty = total_qty / max(1, slices)
    slice_qty = validate_qty(slice_qty, fil)
    results = []
    for i in range(slices):
        res = client.new_order(symbol=symbol, side=side.upper(), type="MARKET", quantity=str(slice_qty))
        log.info(f"TWAP slice {i+1}/{slices}: {res}")
        results.append(res)
        if i < slices - 1:
            time.sleep(interval_sec)
    return {"slices": slices, "slice_qty": slice_qty, "orders": results}
