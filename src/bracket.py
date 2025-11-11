# src/bracket.py
from typing import Dict, Any
from .client import BinanceFuturesREST
from .logger import get_logger
from .validators import extract_filters, validate_qty, validate_price

log = get_logger("Bracket")

def place_bracket_market(client: BinanceFuturesREST, symbol: str, side: str, qty: float,
                         tp: float, sl: float, working_type: str = "MARK_PRICE") -> Dict[str, Any]:
    """
    1) Entry: MARKET (opens LONG if BUY, SHORT if SELL, in hedge mode choose positionSide via your API key's default or leave BOTH)
    2) Exit OCO (synthetic): TP (TAKE_PROFIT) + SL (STOP_MARKET) as reduceOnly
    """
    client.sync_time()
    info = client.exchange_info(symbol=symbol)
    sym = next((s for s in info["symbols"] if s["symbol"] == symbol), None)
    if not sym:
        raise ValueError(f"Symbol {symbol} not found")
    fil = extract_filters(sym)
    qty = validate_qty(qty, fil)
    tp = validate_price(tp, fil)
    sl = validate_price(sl, fil)

    side = side.upper()

    # 1) Entry
    entry = client.new_order(symbol=symbol, side=side, type="MARKET", quantity=str(qty))
    log.info(f"Bracket entry MARKET {side} {symbol} qty={qty}: {entry}")

    # 2) Exit legs (reduce-only)
    exit_side = "SELL" if side == "BUY" else "BUY"

    tp_order = client.new_order(
        symbol=symbol, side=exit_side, type="TAKE_PROFIT",
        timeInForce="GTC", quantity=str(qty),
        price=str(tp), stopPrice=str(tp),
        reduceOnly="true", workingType=working_type
    )
    sl_order = client.new_order(
        symbol=symbol, side=exit_side, type="STOP_MARKET",
        stopPrice=str(sl), reduceOnly="true", workingType=working_type
    )
    return {"entry": entry, "tp": tp_order, "sl": sl_order}
