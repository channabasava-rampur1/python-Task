import argparse, json, sys
from .client import BinanceFuturesREST
from . import config
from .logger import get_logger

from .market_orders import place_market
from .limit_orders import place_limit
from .advanced.stop_limit import place_stop_limit
from .advanced.oco import place_oco
from .advanced.twap import place_twap

# NEW imports
from .account import auto_setup
from .monitor import monitor as run_monitor
from .bracket import place_bracket_market
from .gui import run_gui

log = get_logger("CLI")
def ensure_keys():
    if not config.BINANCE_API_KEY or not config.BINANCE_API_SECRET:
        log.error("API key/secret missing. Set BINANCE_API_KEY and BINANCE_API_SECRET (.env or env).")
        sys.exit(2)

def main():
    p = argparse.ArgumentParser(description="Binance USDT-M Futures Testnet Bot (CLI)")
    sub = p.add_subparsers(dest="cmd", required=True)
    gui = sub.add_parser("gui", help="Launch visual trading panel")

    # Market
    m = sub.add_parser("market", help="Place a MARKET order")
    m.add_argument("symbol")
    m.add_argument("side", choices=["BUY", "SELL"])
    m.add_argument("qty", type=float)

    # Limit
    l = sub.add_parser("limit", help="Place a LIMIT order")
    l.add_argument("symbol")
    l.add_argument("side", choices=["BUY", "SELL"])
    l.add_argument("qty", type=float)
    l.add_argument("price", type=float)
    l.add_argument("--tif", default="GTC", choices=["GTC","IOC","FOK"])

    # Stop-Limit
    s = sub.add_parser("stop-limit", help="Place a STOP-LIMIT order")
    s.add_argument("symbol")
    s.add_argument("side", choices=["BUY", "SELL"])
    s.add_argument("qty", type=float)
    s.add_argument("stop_price", type=float)
    s.add_argument("limit_price", type=float)
    s.add_argument("--tif", default="GTC", choices=["GTC","IOC","FOK"])

    # OCO (synthetic)
    o = sub.add_parser("oco", help="Place synthetic OCO (TP + SL reduce-only)")
    o.add_argument("symbol")
    o.add_argument("side", choices=["BUY","SELL"])
    o.add_argument("qty", type=float)
    o.add_argument("take_profit_price", type=float)
    o.add_argument("stop_price", type=float)
    o.add_argument("--poll", type=float, default=1.0, help="poll seconds")

    # TWAP
    t = sub.add_parser("twap", help="TWAP with MARKET slices")
    t.add_argument("symbol")
    t.add_argument("side", choices=["BUY","SELL"])
    t.add_argument("total_qty", type=float)
    t.add_argument("--slices", type=int, default=5)
    t.add_argument("--interval", type=float, default=5.0)

    # NEW: Setup leverage & position mode
    setup = sub.add_parser("setup", help="Set position mode (hedge/one-way) and leverage for a symbol")
    setup.add_argument("symbol")
    setup.add_argument("--hedge", type=int, default=1, help="1 = Hedge Mode, 0 = One-Way")
    setup.add_argument("--leverage", type=int, default=5)

    # NEW: Live monitor
    mon = sub.add_parser("monitor", help="Live position & PnL monitor (TUI)")
    mon.add_argument("symbols", nargs="+", help="Symbols to watch, e.g., BTCUSDT ETHUSDT")
    mon.add_argument("--interval", type=float, default=1.0)
    mon.add_argument("--hedge", type=int, default=1, help="1 = Hedge Mode (LONG/SHORT panels), 0 = One-Way")

    # NEW: Bracket
    b = sub.add_parser("bracket", help="Bracket entry: MARKET + TP + SL (reduce-only)")
    b.add_argument("symbol")
    b.add_argument("side", choices=["BUY","SELL"])
    b.add_argument("qty", type=float)
    b.add_argument("--tp", required=True, type=float)
    b.add_argument("--sl", required=True, type=float)

    args = p.parse_args()
    ensure_keys()
    client = BinanceFuturesREST(config.BINANCE_API_KEY, config.BINANCE_API_SECRET, config.BASE_URL)

    try:
        if args.cmd == "market":
            res = place_market(client, args.symbol.upper(), args.side, args.qty)
        elif args.cmd == "limit":
            res = place_limit(client, args.symbol.upper(), args.side, args.qty, args.price, args.tif)
        elif args.cmd == "stop-limit":
            res = place_stop_limit(client, args.symbol.upper(), args.side, args.qty, args.stop_price, args.limit_price, args.tif)
        elif args.cmd == "oco":
            res = place_oco(client, args.symbol.upper(), args.side, args.qty, args.take_profit_price, args.stop_price, args.poll)
        elif args.cmd == "twap":
            res = place_twap(client, args.symbol.upper(), args.side, args.total_qty, args.slices, args.interval)
        elif args.cmd == "setup":
            res = auto_setup(client, args.symbol.upper(), hedge=bool(args.hedge), leverage=args.leverage)
        elif args.cmd == "monitor":
            run_monitor(client, [s.upper() for s in args.symbols], interval=args.interval, hedge_mode=bool(args.hedge))
            res = {"status": "monitor-exited"}
        elif args.cmd == "bracket":
            res = place_bracket_market(client, args.symbol.upper(), args.side, args.qty, args.tp, args.sl)
        elif args.cmd == "gui":
            from .gui import run_gui
            run_gui()
            res = {"status": "gui-exited"}
        else:
            raise ValueError("Unknown command")

        print(json.dumps(res, indent=2))
        log.info(f"SUCCESS {args.cmd} -> {res}")
    except Exception as e:
        log.exception(f"ERROR running {args.cmd}: {e}")
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
