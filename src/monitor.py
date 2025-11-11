# src/monitor.py
import time, curses, math
from typing import List, Dict, Any
from .client import BinanceFuturesREST
from .logger import get_logger

log = get_logger("Monitor")

def _fmt_float(x, d=4):
    try:
        return f"{float(x):.{d}f}"
    except:
        return str(x)

def _fetch_positions(client: BinanceFuturesREST, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Returns dict: { SYMBOL: { BOTH: {...}, LONG: {...}, SHORT: {...} } }
    In Hedge Mode, you'll have LONG/SHORT entries. In One-Way, use BOTH.
    """
    data = client.position_info()
    out: Dict[str, Dict[str, Any]] = {}
    symset = {s.upper() for s in symbols} if symbols else None
    for p in data:
        sym = p["symbol"]
        if symset and sym not in symset:
            continue
        d = out.setdefault(sym, {})
        d[p["positionSide"]] = p
    return out

def _fetch_mark_prices(client: BinanceFuturesREST, symbols: List[str]) -> Dict[str, float]:
    out = {}
    for s in symbols:
        mp = client.mark_price(s.upper())
        out[s.upper()] = float(mp["markPrice"])
    return out

def monitor(client: BinanceFuturesREST, symbols: List[str], interval: float = 1.0, hedge_mode: bool = True):
    """
    curses TUI showing live positions, mark price, size, entry, and PnL.
    Press 'q' to quit.
    """
    client.sync_time()
    symbols = [s.upper() for s in symbols] if symbols else []

    def draw(stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)
        row = 0
        title = "Futures Live Monitor (HEDGE MODE)" if hedge_mode else "Futures Live Monitor (ONE-WAY)"
        while True:
            stdscr.erase()
            maxy, maxx = stdscr.getmaxyx()
            stdscr.addstr(row, 0, title)
            stdscr.addstr(row+1, 0, "-" * min(maxx-1, len(title)+5))

            try:
                pos = _fetch_positions(client, symbols)
                marks = _fetch_mark_prices(client, symbols)
                r = row + 3
                header = f"{'SYMBOL':<10} {'SIDE':<6} {'SIZE':>10} {'ENTRY':>14} {'MARK':>14} {'UPnL':>14} {'RoE%':>8}"
                stdscr.addstr(r, 0, header)
                r += 1
                stdscr.addstr(r, 0, "-" * min(maxx-1, len(header)+20))
                r += 1

                for sym in (symbols if symbols else sorted(pos.keys())):
                    d = pos.get(sym, {})
                    sides = ["LONG","SHORT"] if hedge_mode else ["BOTH"]
                    for side in sides:
                        p = d.get(side)
                        if not p:
                            continue
                        size = float(p["positionAmt"])   # positive for long, negative for short on BOTH; LONG/SHORT are positive
                        if abs(size) < 1e-12:
                            continue
                        entry = float(p["entryPrice"])
                        mark = marks.get(sym, entry)
                        upnl = float(p.get("unRealizedProfit", 0.0))
                        # RoE%: unrealized pnl / (entry * abs(size) * 1/leverage)  -> simplified: use walletBalance? we use provided PnL and position notional
                        notional = abs(mark * size)
                        roe = (upnl / notional) * 100.0 if notional > 0 else 0.0
                        line = f"{sym:<10} {side:<6} {size:>10.6f} {entry:>14.2f} {mark:>14.2f} {upnl:>14.4f} {roe:>8.2f}"
                        stdscr.addstr(r, 0, line[:maxx-1])
                        r += 1

                stdscr.addstr(maxy-1, 0, "Press 'q' to quit | Refresh: {:.1f}s".format(interval))
                stdscr.refresh()
            except Exception as e:
                log.exception(f"monitor loop error: {e}")
                stdscr.addstr(row+3, 0, f"Error: {e}")
                stdscr.refresh()

            for _ in range(int(interval*10)):
                c = stdscr.getch()
                if c == ord('q'):
                    return
                time.sleep(0.1)

    curses.wrapper(draw)
