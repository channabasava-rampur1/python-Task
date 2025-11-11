# python-Task
# Binance USDT-M Futures Testnet Bot (CLI)

A clean, testnet-only trading bot for **Binance USDT-M Futures** with:
- **Market & Limit** orders (mandatory)
- **Stop-Limit**, **synthetic OCO**, and **TWAP** (bonus)
- Strong **validation** against exchange filters
- **Structured logging** of requests/responses/errors to `bot.log`
- Clear **CLI** UX

> **Testnet base URL**: `https://testnet.binancefuture.com` (verified).  
> Endpoints used: `POST /fapi/v1/order`, `GET /fapi/v1/exchangeInfo`, `GET /fapi/v1/openOrders`, `POST /fapi/v1/batchOrders`.  
> Sources: Binance Dev Docs. 

## 1) Setup

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1 ; macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
