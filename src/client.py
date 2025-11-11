import requests
from typing import Dict, Any, List
from dateutil import tz
from .logger import get_logger
from . import config
from .utils import sign_params, now_ms

class BinanceFuturesREST:
    def __init__(self, api_key: str, api_secret: str, base_url: str = config.BASE_URL):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.sess = requests.Session()
        self.sess.headers.update({"X-MBX-APIKEY": self.api_key})
        self.log = get_logger("BinanceREST")
        self._time_offset_ms = 0

    # ----- Core HTTP helpers -----
    def _get(self, path: str, params: Dict[str, Any] = None, auth: bool = False):
        url = self.base_url + path
        params = params or {}
        if auth:
            params.setdefault("timestamp", now_ms() + self._time_offset_ms)
            params.setdefault("recvWindow", config.RECV_WINDOW_MS)
            q = sign_params(self.api_secret, params)
        else:
            q = requests.compat.urlencode(params)
        self.log.info(f"GET {path} params={params}")
        r = self.sess.get(url, params=q, timeout=config.TIMEOUT)
        self._log_response(r)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, params: Dict[str, Any] = None, auth: bool = False, json: Any = None):
        url = self.base_url + path
        params = params or {}
        data = None
        if auth:
            params.setdefault("timestamp", now_ms() + self._time_offset_ms)
            params.setdefault("recvWindow", config.RECV_WINDOW_MS)
            data = sign_params(self.api_secret, params)
        self.log.info(f"POST {path} params={params} json={json}")
        r = self.sess.post(url, params=data, json=json, timeout=config.TIMEOUT)
        self._log_response(r)
        r.raise_for_status()
        return r.json()

    def _delete(self, path: str, params: Dict[str, Any] = None, auth: bool = False):
        url = self.base_url + path
        params = params or {}
        if auth:
            params.setdefault("timestamp", now_ms() + self._time_offset_ms)
            params.setdefault("recvWindow", config.RECV_WINDOW_MS)
            q = sign_params(self.api_secret, params)
        else:
            q = requests.compat.urlencode(params)
        self.log.info(f"DELETE {path} params={params}")
        r = self.sess.delete(url, params=q, timeout=config.TIMEOUT)
        self._log_response(r)
        r.raise_for_status()
        return r.json()

    def _log_response(self, r: requests.Response):
        self.log.info(f"RESP {r.status_code} {r.text[:1000]}")

    # ----- Public / account helpers -----
    def ping(self):
        return self._get("/fapi/v1/ping")

    def server_time(self):
        return self._get("/fapi/v1/time")  # {'serverTime': ...}

    def sync_time(self):
        st = self.server_time()["serverTime"]
        local = now_ms()
        self._time_offset_ms = st - local
        self.log.info(f"Time sync offset_ms={self._time_offset_ms}")

    def exchange_info(self, symbol: str = None):
        params = {"symbol": symbol} if symbol else {}
        return self._get("/fapi/v1/exchangeInfo", params=params)

    def account_info(self):
        return self._get("/fapi/v2/account", auth=True)

    def positions(self):
        return self._get("/fapi/v2/positionRisk", auth=True)

    # ----- Trading -----
    def new_order(self, **params):
        return self._post("/fapi/v1/order", params=params, auth=True)

    def batch_orders(self, orders: List[dict]):
        # POST /fapi/v1/batchOrders with a JSON list under 'batchOrders'
        payload = {"batchOrders": orders, "timestamp": now_ms() + self._time_offset_ms, "recvWindow": config.RECV_WINDOW_MS}
        qs = sign_params(self.api_secret, {k: v for k, v in payload.items() if k != "batchOrders"})
        return self._post("/fapi/v1/batchOrders", auth=False, params=None, json={"batchOrders": orders, "signature": qs.split("=",1)[1]})

    def cancel_order(self, symbol: str, **params):
        params["symbol"] = symbol
        return self._delete("/fapi/v1/order", params=params, auth=True)

    def open_orders(self, symbol: str = None):
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._get("/fapi/v1/openOrders", params=params, auth=True)
    def mark_price(self, symbol: str):
        # GET /fapi/v1/premiumIndex returns markPrice among other fields
        return self._get("/fapi/v1/premiumIndex", params={"symbol": symbol})

    def position_info(self, symbol: str = None):
        # GET /fapi/v2/positionRisk (auth)
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._get("/fapi/v2/positionRisk", params=params, auth=True)

    def account_balance(self):
        # GET /fapi/v2/balance (auth)
        return self._get("/fapi/v2/balance", auth=True)
