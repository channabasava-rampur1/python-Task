import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Required env vars; keep secrets out of code
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "").strip()
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "").strip()

# Testnet base URL (USDT-M Futures)
BASE_URL = os.getenv("BINANCE_FAPI_BASE_URL", "https://testnet.binancefuture.com").strip()

# Request settings
RECV_WINDOW_MS = int(os.getenv("RECV_WINDOW_MS", "5000"))
TIME_DRIFT_ALLOW_MS = int(os.getenv("TIME_DRIFT_ALLOW_MS", "1000"))  # sync clock tolerance
TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "15"))  # seconds

# Default leverage & position mode
DEFAULT_LEVERAGE = int(os.getenv("DEFAULT_LEVERAGE", "5"))
HEDGE_MODE = bool(int(os.getenv("HEDGE_MODE", "0")))  # 0: one-way mode, 1: hedge mode
