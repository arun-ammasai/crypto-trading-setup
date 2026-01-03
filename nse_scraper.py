import httpx
from fastapi import HTTPException
import json

async def get_nse_fii_dii():
    # NSE requires a user-agent and session cookies. 
    # Valid headers are critical.
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": "https://www.nseindia.com/reports/fii-dii",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
        # Removed explicit Accept-Encoding to let httpx handle it
    }
    
    base_url = "https://www.nseindia.com"
    api_url = "https://www.nseindia.com/api/fiidiiTradeReact"

    try:
        async with httpx.AsyncClient(headers=headers, timeout=20.0, follow_redirects=True) as client:
            # 1. Visit homepage to get cookies
            print(f"Visiting {base_url}...")
            await client.get(base_url)
            
            # 2. Call the API
            print(f"Fetching {api_url}...")
            response = await client.get(api_url)
            
            print(f"Status Code: {response.status_code}")
            # print(f"Headers: {response.headers}")
            
            response.raise_for_status()
            
            try:
                data = response.json()
            except json.JSONDecodeError as je:
                print(f"JSON Decode Error. Content preview: {response.content[:100]}")
                raise je
            
            fii_data = {}
            dii_data = {}
            trade_date = ""

            for item in data:
                category = item.get("category", "")
                
                def parse_float(val):
                    if isinstance(val, (int, float)):
                        return float(val)
                    if isinstance(val, str):
                        # Remove commas and handle spaces
                        val = val.replace(",", "").strip()
                        return float(val) if val else 0.0
                    return 0.0

                current_vals = {
                    "buy": parse_float(item.get("buyValue")),
                    "sell": parse_float(item.get("sellValue")),
                    "net": parse_float(item.get("netValue"))
                }
                
                if "FII" in category or "FPI" in category:
                    fii_data = current_vals
                    trade_date = item.get("date")
                elif "DII" in category:
                    dii_data = current_vals
                    trade_date = item.get("date")

            if not fii_data and not dii_data:
                 print("Data parsed but no FII/DII found:", data)
                 raise HTTPException(status_code=404, detail="FII/DII data not found or format changed")

            result = {
                "date": trade_date,
                "FII": fii_data,
                "DII": dii_data
            }
            return result

    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"NSE API Error: {str(e)}")
    except Exception as e:
        print(f"General Error: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping Error: {str(e)}")
