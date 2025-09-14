from fastapi import FastAPI, Query, HTTPException
from typing import List, Dict
from ohlcv import fetch_ohlcv, analyze_ta, BulkRequest
import ccxt
import pandas as pd
from datetime import datetime
import httpx

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
        exchange = ccxt.binance()
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

@app.get("/coingecko/markets")
async def get_markets(
    vs_currency: str = "usd",
    order: str = "market_cap_desc",
    per_page: int = 100,
    page: int = 1,
    sparkline: bool = False
):
    params = {
        "vs_currency": vs_currency,
        "order": order,
        "per_page": per_page,
        "page": page,
        "sparkline": str(sparkline).lower()
    }

    try:
        COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
        async with httpx.AsyncClient() as client:
            response = await client.get(COINGECKO_URL, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/binance/usdt_markets")
async def get_usdt_markets(
    vs_currency: str = "usd",
    per_page: int = 100,
    page: int = 1
):
    try:
        # 1. Fetch top coins from CoinGecko
        params = {
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": page,
            "sparkline": "false"
        }
        COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"

        async with httpx.AsyncClient() as client:
            cg_resp = await client.get(COINGECKO_URL, params=params)
            cg_resp.raise_for_status()
            top_coins = cg_resp.json()

        # 2. Load Binance markets
        exchange = ccxt.binance()
        markets = exchange.load_markets()

        # 3. Filter coins that have USDT pairs in Binance
        filtered = []
        for coin in top_coins:
            symbol = coin["symbol"].upper()
            pair = f"{symbol}/USDT"
            if pair in markets:
                filtered.append(coin)  # keep the original CoinGecko coin data

        # 4. Return only CoinGecko-like response but filtered
        return filtered

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/coingecko/rank/{coin_id}")
async def get_coin_rank(coin_id: str, vs_currency: str = "usd"):
    """
    Fetch the market cap rank of a specific coin from CoinGecko
    Example: /coingecko/rank/bitcoin or /coingecko/rank/ethereum
    """
    params = {
        "vs_currency": vs_currency,
        "ids": coin_id.lower()
    }
    COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"


    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(COINGECKO_URL, params=params)
            response.raise_for_status()
            data = response.json()

        if not data:
            raise HTTPException(status_code=404, detail=f"Coin '{coin_id}' not found")

        coin = data[0]

        return {
            "id": coin["id"],
            "symbol": coin["symbol"],
            "name": coin["name"],
            "rank": coin.get("market_cap_rank")
        }

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))        
