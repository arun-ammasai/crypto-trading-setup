from fastapi import FastAPI, Query
from typing import List, Dict
from ohlcv import fetch_ohlcv, analyze_ta, BulkRequest
import ccxt
import pandas as pd
from datetime import datetime

app = FastAPI(title="Crypto Trading Backend")

@app.get("/health")
def health() -> dict:
	return {"status": "ok"}

@app.get("/ping")
def ping() -> dict:
	return {"message": "pong"}

@app.get("/ohlcv")
def get_ohlcv(
	symbol: str = Query("BTC/USDT"),
	timeframe: str = Query("1h"),
	limit: int = Query(100, ge=1, le=1000),
) -> List[Dict]:
	return fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)


@app.get("/analyze")
def analyze_coin(
    coin_id: str = Query(...), 
    symbol: str = Query(...), 
    timeframe: str = "1h", 
    limit: int = 100
):
    try:
        pair = f"{symbol.upper()}/USDT"
        #exchange = ccxt.binance()
        exchange = ccxt.okx()
        # Fetch OHLCV
        ohlcv = exchange.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=["timestamp","open","high","low","close","volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        # ✅ Use renamed function
        ta_result = analyze_ta(df)

        return {
            "coin_id": coin_id,
            "symbol": symbol.upper(),
            "pair": pair,
            "date_utc": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            **ta_result
        }
    except Exception as e:
        return {"error": str(e), "coin_id": coin_id, "symbol": symbol}

@app.post("/analyze_bulk")
def analyze_bulk(request: BulkRequest):
    results = []
    exchange = ccxt.binance()
    print("Total Items : ",len(request.coins))
    for coin in request.coins:
        try:
            pair = f"{coin.symbol.upper()}/USDT"
            ohlcv = exchange.fetch_ohlcv(pair, timeframe=request.timeframe, limit=request.limit)
            df = pd.DataFrame(ohlcv, columns=["timestamp","open","high","low","close","volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

            ta_result = analyze_ta(df)

            results.append({
                "coin_id": coin.coin_id,
                "symbol": coin.symbol.upper(),
                "pair": pair,
                "date_utc": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                **ta_result
            })
        except Exception as e:
            results.append({
                "coin_id": coin.coin_id,
                "symbol": coin.symbol,
                "error": str(e)
            })
    return {"results": results}
