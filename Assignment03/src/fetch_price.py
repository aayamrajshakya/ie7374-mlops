#!/usr/bin/env python3
import datetime
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
headers = {"Authorization": f"Bearer {API_KEY}"}


def fetch_price():
    response = requests.get(
        url="https://api.freecryptoapi.com/v1/getData?symbol=BTC",
        headers=headers,
        timeout=10,
    )
    response.raise_for_status()

    data = response.json()
    # print(f"Raw response: {response.text}")
    btc_data = data["symbols"][0]

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    return {
        "symbol": btc_data["symbol"],
        "price_usd": float(btc_data["last"]),
        "timestamp_utc": now_utc.isoformat(),
        "unix_timestamp": int(now_utc.timestamp()),
    }


if __name__ == "__main__":
    print(fetch_price())
