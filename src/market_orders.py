from typing import Dict, Any
from .client import BinanceFuturesREST
from .logger import get_logger
from .validators import extract_filters, validate_qty

log = get_logger("MarketOrder")

def place_market(client: BinanceFuturesREST, symbol: str, side: str, qty: float) -> Dict[str, Any]:
    """
    Place a MARKET order on USDT-M Futures.
    side: BUY or SELL
    """
    client.sync_time()
    info = client.exchange_info(symbol=symbol)
    sym = next((s for s in info["symbols"] if s["symbol"] == symbol), None)
    if not sym:
        raise ValueError(f"Symbol {symbol} not found on exchange")

    fil = extract_filters(sym)
    qty = validate_qty(qty, fil)

    payload = dict(symbol=symbol, side=side.upper(), type="MARKET", quantity=str(qty))
    log.info(f"Placing MARKET {side} {symbol} qty={qty}")
    return client.new_order(**payload)
