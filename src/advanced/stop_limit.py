from typing import Dict, Any
from ..client import BinanceFuturesREST
from ..logger import get_logger
from ..validators import extract_filters, validate_qty, validate_price

log = get_logger("StopLimit")

def place_stop_limit(client: BinanceFuturesREST, symbol: str, side: str, qty: float, stop_price: float, limit_price: float, tif="GTC") -> Dict[str, Any]:
    """
    Futures STOP (stop-limit): order type 'STOP' with stopPrice + price
    When stopPrice is hit, a LIMIT order is placed at limit_price.
    Docs: POST /fapi/v1/order
    """
    client.sync_time()
    info = client.exchange_info(symbol=symbol)
    sym = next((s for s in info["symbols"] if s["symbol"] == symbol), None)
    if not sym:
        raise ValueError(f"Symbol {symbol} not found")

    fil = extract_filters(sym)
    qty = validate_qty(qty, fil)
    stop_price = validate_price(stop_price, fil)
    limit_price = validate_price(limit_price, fil)

    payload = dict(
        symbol=symbol, side=side.upper(), type="STOP",
        timeInForce=tif, quantity=str(qty),
        stopPrice=str(stop_price), price=str(limit_price),
        workingType="MARK_PRICE"  # safer triggers on mark price
    )
    log.info(f"Placing STOP-LIMIT {side} {symbol} qty={qty} stop={stop_price} limit={limit_price}")
    return client.new_order(**payload)
