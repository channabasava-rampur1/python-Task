# src/account.py
from typing import Dict, Any
from .client import BinanceFuturesREST
from .logger import get_logger

log = get_logger("Account")

def set_position_mode(client: BinanceFuturesREST, hedge: bool = True) -> Dict[str, Any]:
    """
    Set position mode:
      hedge=True  -> dualSidePosition = true (Hedge Mode)
      hedge=False -> dualSidePosition = false (One-Way)
    POST /fapi/v1/positionSide/dual
    """
    client.sync_time()
    payload = {
        "dualSidePosition": "true" if hedge else "false",
    }
    log.info(f"Setting position mode hedge={hedge}")
    return client._post("/fapi/v1/positionSide/dual", params=payload, auth=True)

def set_leverage(client: BinanceFuturesREST, symbol: str, leverage: int) -> Dict[str, Any]:
    """
    Set leverage for a specific symbol.
    POST /fapi/v1/leverage
    """
    client.sync_time()
    leverage = max(1, min(int(leverage), 125))  # Binance limit
    payload = {
        "symbol": symbol.upper(),
        "leverage": leverage,
    }
    log.info(f"Setting leverage symbol={symbol} leverage={leverage}")
    return client._post("/fapi/v1/leverage", params=payload, auth=True)

def auto_setup(client: BinanceFuturesREST, symbol: str, hedge: bool, leverage: int) -> Dict[str, Any]:
    """
    Convenience: ensure position mode + leverage before trading this symbol.
    """
    r1 = set_position_mode(client, hedge=hedge)
    r2 = set_leverage(client, symbol=symbol, leverage=leverage)
    return {"position_mode": r1, "leverage": r2}
