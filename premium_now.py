#!/usr/bin/env python3
"""Print today's stablecoin premium for every covered African currency.

Premium = how far the USDT peer-to-peer mid rate sits above the official rate.

    export MANSA_API_KEY=...
    python premium_now.py
"""
import os
import sys

import requests

key = os.environ.get("MANSA_API_KEY")
if not key:
    sys.exit("Set MANSA_API_KEY (free key: https://mansaapi.com/docs#get-api-key)")

r = requests.get(
    "https://mansaapi.com/api/v1/stablecoins/rates",
    headers={"Authorization": f"Bearer {key}"},
    timeout=30,
).json()
if not r.get("success"):
    sys.exit(r.get("error"))

rows = [x for x in r["data"] if x.get("premium_pct") is not None and not x.get("crossed")]
rows.sort(key=lambda x: x["premium_pct"], reverse=True)

print(f"{'Ccy':<4} {'USDT mid':>12} {'Official':>12} {'Premium':>8} {'Depth $':>9}")
for x in rows:
    print(f"{x['currency']:<4} {x['mid']:>12,.2f} {x['official']:>12,.2f} "
          f"{x['premium_pct']:>+7.1f}% {x['depth_usd']:>9,.0f}")

no_rate = [x["currency"] for x in r["data"] if x.get("mid") is None]
if no_rate:
    print(f"\nNo rate this hour (offers did not agree): {', '.join(no_rate)}")
print("\nSource: Mansa Markets Stablecoin Premium Index, https://www.mansamarkets.com/stablecoins")
