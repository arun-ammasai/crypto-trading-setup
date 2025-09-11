import ccxt
import pandas as pd
import pandas_ta as ta
from typing import List, Dict
from pydantic import BaseModel

# -----------------------
# Request Model
# -----------------------
class CoinRequest(BaseModel):
    coin_id: str
    symbol: str   # e.g. BTC, ETH, ADA

class BulkRequest(BaseModel):
    coins: List[CoinRequest]
    timeframe: str = "1h"
    limit: int = 100

# -----------------------
# Technical Analysis
# -----------------------

def analyze_ta(df: pd.DataFrame) -> Dict:
    df["ema20"] = ta.ema(df["close"], length=20)
    df["ema50"] = ta.ema(df["close"], length=50)
    df["rsi"] = ta.rsi(df["close"], length=14)
    macd = ta.macd(df["close"])
    df["macd_hist"] = macd["MACDh_12_26_9"]
    df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=14)

    score = 0
    if df["ema20"].iloc[-1] > df["ema50"].iloc[-1]:
        score += 3
    if 35 < df["rsi"].iloc[-1] < 65:
        score += 2
    if df["macd_hist"].iloc[-1] > 0:
        score += 2

    return {
        "ema20": round(df["ema20"].iloc[-1], 2),
        "ema50": round(df["ema50"].iloc[-1], 2),
        "rsi": round(df["rsi"].iloc[-1], 2),
        "macd_hist": round(df["macd_hist"].iloc[-1], 2),
        "atr": round(df["atr"].iloc[-1], 2),
        "ta_score": score,
    }

def fetch_ohlcv(symbol: str = "BTC/USDT", timeframe: str = "1h", limit: int = 100) -> List[Dict]:
	"""Fetch OHLCV data from Binance and return as list of dicts."""
	exchange = ccxt.bybit()
	ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
	df = pd.DataFrame(ohlcv, columns=["timestamp","open","high","low","close","volume"])
	df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
	return df.tail(limit).to_dict(orient="records")


# ✅ Technical Analysis function
def analyze_ta_old(df):
    df["ema20"] = ta.ema(df["close"], length=20)
    df["ema50"] = ta.ema(df["close"], length=50)
    df["rsi"] = ta.rsi(df["close"], length=14)
    macd = ta.macd(df["close"])
    df["macd_hist"] = macd["MACDh_12_26_9"]
    df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=14)

    score = 0
    if df["ema20"].iloc[-1] > df["ema50"].iloc[-1]:
        score += 3
    if 35 < df["rsi"].iloc[-1] < 65:
        score += 2
    if df["macd_hist"].iloc[-1] > 0:
        score += 2

    return {
        "ema20": round(df["ema20"].iloc[-1], 2),
        "ema50": round(df["ema50"].iloc[-1], 2),
        "rsi": round(df["rsi"].iloc[-1], 2),
        "macd_hist": round(df["macd_hist"].iloc[-1], 2),
        "atr": round(df["atr"].iloc[-1], 2),
        "ta_score": score
    }
