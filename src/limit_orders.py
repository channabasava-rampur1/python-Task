from typing import Dict, Any
from .client import BinanceFuturesREST
from .logger import get_logger
from .validators import extract_filters, validate_qty, validate_price

log = get_logger("LimitOrder")

def place_limit(client: BinanceFuturesREST, symbol: str, side: str, qty: float, price: float, tif: str = "GTC") -> Dict[str, Any]:
    """
    Place a LIMIT order with timeInForce (GTC/IOC/FOK)
    """
    client.sync_time()
    info = client.exchange_info(symbol=symbol)
    sym = next((s for s in info["symbols"] if s["symbol"] == symbol), None)
    if not sym:
        raise ValueError(f"Symbol {symbol} not found on exchange")

    fil = extract_filters(sym)
    qty = validate_qty(qty, fil)
    price = validate_price(price, fil)

    payload = dict(symbol=symbol, side=side.upper(), type="LIMIT",
                   timeInForce=tif, quantity=str(qty), price=str(price))
    log.info(f"Placing LIMIT {side} {symbol} qty={qty} price={price} tif={tif}")
    return client.new_order(**payload)
