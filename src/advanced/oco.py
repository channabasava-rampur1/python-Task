import time
from typing import Dict, Any, Tuple
from ..client import BinanceFuturesREST
from ..logger import get_logger
from ..validators import extract_filters, validate_qty, validate_price

log = get_logger("OCO")

def place_oco(client: BinanceFuturesREST, symbol: str, side: str, qty: float,
              take_profit_price: float, stop_price: float, poll_sec: float = 1.0) -> Dict[str, Any]:
    """
    Synthetic OCO for futures:
    - If side == SELL: You likely hold a long; we place TP (TAKE_PROFIT) and SL (STOP_MARKET) reduce-only sells.
    - If side == BUY: You likely hold a short; place corresponding reduce-only buys.
    Cancels the other when one is filled or canceled.
    """
    client.sync_time()
    info = client.exchange_info(symbol=symbol)
    sym = next((s for s in info["symbols"] if s["symbol"] == symbol), None)
    if not sym:
        raise ValueError(f"Symbol {symbol} not found")

    fil = extract_filters(sym)
    qty = validate_qty(qty, fil)
    tp = validate_price(take_profit_price, fil)
    sp = validate_price(stop_price, fil)

    taker_side = side.upper()
    # Place TP limit (or TAKE_PROFIT_MARKET preferred? we use TAKE_PROFIT with price for determinism)
    tp_order = client.new_order(
        symbol=symbol, side=taker_side, type="TAKE_PROFIT",
        timeInForce="GTC", quantity=str(qty), price=str(tp), stopPrice=str(tp),
        reduceOnly="true", workingType="MARK_PRICE"
    )
    # Place SL market (stop market)
    sl_order = client.new_order(
        symbol=symbol, side=taker_side, type="STOP_MARKET",
        stopPrice=str(sp), closePosition="false",
        quantity=str(qty), reduceOnly="true", workingType="MARK_PRICE"
    )

    tp_id = tp_order.get("orderId")
    sl_id = sl_order.get("orderId")
    log.info(f"OCO placed TP id={tp_id}, SL id={sl_id}")

    # Poll until one is filled/canceled, then cancel the other
    while True:
        time.sleep(poll_sec)
        open_os = client.open_orders(symbol=symbol)
        open_ids = {o["orderId"] for o in open_os}
        tp_open = tp_id in open_ids
        sl_open = sl_id in open_ids
        if tp_open and sl_open:
            continue
        # One got removed => cancel the other if still open
        if tp_open and not sl_open:
            log.info("SL triggered/canceled; canceling TP")
            client.cancel_order(symbol, orderId=tp_id)
            break
        if sl_open and not tp_open:
            log.info("TP triggered/canceled; canceling SL")
            client.cancel_order(symbol, orderId=sl_id)
            break
        if not tp_open and not sl_open:
            log.info("Both TP and SL are gone (filled/canceled).")
            break

    return {"tp_order": tp_order, "sl_order": sl_order}
