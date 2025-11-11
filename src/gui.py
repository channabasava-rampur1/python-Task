import tkinter as tk
from tkinter import messagebox
from threading import Thread
import time

from .client import BinanceFuturesREST
from . import config
from .account import auto_setup
from .logger import get_logger
from .validators import extract_filters, validate_qty, validate_price
from .bracket import place_bracket_market

log = get_logger("GUI")

class TradingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Binance Futures Trading Panel (Testnet)")
        self.root.geometry("460x500")
        self.root.resizable(False, False)

        # Connect client
        self.client = BinanceFuturesREST(config.BINANCE_API_KEY, config.BINANCE_API_SECRET, config.BASE_URL)
        self.client.sync_time()

        # UI Variables
        self.symbol_var = tk.StringVar(value="BTCUSDT")
        self.qty_var = tk.StringVar(value="0.01")
        self.price_var = tk.StringVar(value="")
        self.tp_var = tk.StringVar(value="")
        self.sl_var = tk.StringVar(value="")
        self.hedge_var = tk.IntVar(value=1)
        self.leverage_var = tk.IntVar(value=7)

        # UI Layout
        tk.Label(root, text="Symbol:").pack()
        tk.Entry(root, textvariable=self.symbol_var).pack()

        tk.Label(root, text="Quantity:").pack()
        tk.Entry(root, textvariable=self.qty_var).pack()

        tk.Label(root, text="(Optional) Limit Price:").pack()
        tk.Entry(root, textvariable=self.price_var).pack()

        tk.Label(root, text="Take Profit Price:").pack()
        tk.Entry(root, textvariable=self.tp_var).pack()

        tk.Label(root, text="Stop Loss Price:").pack()
        tk.Entry(root, textvariable=self.sl_var).pack()

        tk.Label(root, text="Leverage:").pack()
        tk.Entry(root, textvariable=self.leverage_var).pack()

        tk.Checkbutton(root, text="Hedge Mode", variable=self.hedge_var).pack(pady=4)

        tk.Button(root, text="Apply Mode & Leverage", command=self.apply_setup).pack(pady=5)

        tk.Button(root, text="BUY (Market)", command=lambda: self.send_order("BUY", market=True)).pack(pady=5)
        tk.Button(root, text="SELL (Market)", command=lambda: self.send_order("SELL", market=True)).pack(pady=5)

        tk.Button(root, text="BUY (Limit)", command=lambda: self.send_order("BUY", market=False)).pack(pady=5)
        tk.Button(root, text="SELL (Limit)", command=lambda: self.send_order("SELL", market=False)).pack(pady=5)

        tk.Button(root, text="BRACKET ORDER", command=self.place_bracket).pack(pady=10)

        self.pnl_label = tk.Label(root, text="PnL: Loading...", font=("Arial", 14), fg="blue")
        self.pnl_label.pack(pady=15)

        Thread(target=self.update_pnl_loop, daemon=True).start()

    # --- Commands ---

    def apply_setup(self):
        try:
            sym = self.symbol_var.get().upper()
            auto_setup(self.client, sym, hedge=bool(self.hedge_var.get()), leverage=self.leverage_var.get())
            messagebox.showinfo("Success", f"Hedge Mode + Leverage Applied to {sym}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def send_order(self, side, market=True):
        try:
            sym = self.symbol_var.get().upper()
            qty = float(self.qty_var.get())

            info = self.client.exchange_info(symbol=sym)
            sym_info = next((s for s in info["symbols"] if s["symbol"] == sym), None)
            fil = extract_filters(sym_info)
            qty = validate_qty(qty, fil)

            if market:
                order = self.client.new_order(symbol=sym, side=side, type="MARKET", quantity=str(qty))
            else:
                price = validate_price(float(self.price_var.get()), fil)
                order = self.client.new_order(symbol=sym, side=side, type="LIMIT",
                                              timeInForce="GTC", quantity=str(qty), price=str(price))
            messagebox.showinfo("Order Sent", str(order))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def place_bracket(self):
        try:
            sym = self.symbol_var.get().upper()
            qty = float(self.qty_var.get())
            tp = float(self.tp_var.get())
            sl = float(self.sl_var.get())
            result = place_bracket_market(self.client, sym, "BUY", qty, tp, sl)
            messagebox.showinfo("Bracket Placed", str(result))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # --- Live P&L Monitor ---

    def update_pnl_loop(self):
        while True:
            try:
                sym = self.symbol_var.get().upper()
                pos = self.client.position_info(sym)
                p_long = next((p for p in pos if p["positionSide"] == "LONG"), None)
                p_short = next((p for p in pos if p["positionSide"] == "SHORT"), None)

                pnl_long = float(p_long["unRealizedProfit"]) if p_long and float(p_long["positionAmt"]) != 0 else 0
                pnl_short = float(p_short["unRealizedProfit"]) if p_short and float(p_short["positionAmt"]) != 0 else 0
                pnl = pnl_long + pnl_short

                self.pnl_label.config(text=f"PnL: {pnl:.4f} USDT")
            except:
                pass

            time.sleep(1)

def run_gui():
    root = tk.Tk()
    TradingGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()
