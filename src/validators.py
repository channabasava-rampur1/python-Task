from typing import Tuple, Dict, Any
from .utils import round_step

def extract_filters(exchange_info_symbol: Dict[str, Any]) -> Dict[str, Any]:
    f = {"priceStep": None, "minPrice": None, "maxPrice": None, "qtyStep": None, "minQty": None, "maxQty": None}
    for fil in exchange_info_symbol.get("filters", []):
        if fil["filterType"] == "PRICE_FILTER":
            f["minPrice"] = float(fil["minPrice"])
            f["maxPrice"] = float(fil["maxPrice"])
            f["priceStep"] = float(fil["tickSize"])
        if fil["filterType"] == "LOT_SIZE":
            f["minQty"] = float(fil["minQty"])
            f["maxQty"] = float(fil["maxQty"])
            f["qtyStep"] = float(fil["stepSize"])
    return f

def adjust_price(price: float, price_step: float) -> float:
    return round_step(price, price_step)

def adjust_qty(qty: float, qty_step: float) -> float:
    return round_step(qty, qty_step)

def validate_price(p: float, f: Dict[str, float]) -> float:
    if f["priceStep"] is None:
        return p
    p2 = adjust_price(p, f["priceStep"])
    if f["minPrice"] and p2 < f["minPrice"]:
        raise ValueError(f"Price {p2} < minPrice {f['minPrice']}")
    if f["maxPrice"] and p2 > f["maxPrice"]:
        raise ValueError(f"Price {p2} > maxPrice {f['maxPrice']}")
    return p2

def validate_qty(q: float, f: Dict[str, float]) -> float:
    if f["qtyStep"] is None:
        return q
    q2 = adjust_qty(q, f["qtyStep"])
    if f["minQty"] and q2 < f["minQty"]:
        raise ValueError(f"Quantity {q2} < minQty {f['minQty']}")
    if f["maxQty"] and q2 > f["maxQty"]:
        raise ValueError(f"Quantity {q2} > maxQty {f['maxQty']}")
    return q2
