#!/usr/bin/env python3
"""True dollar returns on African stock indices.

For each African stock index, compute the return over a window three ways:

  local            index close to close, in local currency
  usd_official     index divided by the official exchange rate at both ends
  usd_stablecoin   index divided by the USDT peer-to-peer rate at both ends

The gap between the last two is how much the official rate flatters (or
understates) what a dollar investor actually got.

Data: Mansa API (https://mansaapi.com/stablecoin-fx-api). A free key covers the
last 30 days of stablecoin fixings; Pro covers the full history from 15 Aug 2026.

    export MANSA_API_KEY=...
    python true_dollar_returns.py                 # last 30 days
    python true_dollar_returns.py --from 2026-08-15 --csv out.csv
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import date, timedelta

import requests

API = "https://mansaapi.com/api/v1"

# index slug -> currency. Every index here has a currency covered by the
# Stablecoin Premium Index.
INDICES = {
    "ngx-asi": "NGN",   # Nigeria
    "jse-asi": "ZAR",   # South Africa
    "egx-30": "EGP",    # Egypt
    "masi": "MAD",      # Morocco
    "nse-asi": "KES",   # Kenya
    "gse-ci": "GHS",    # Ghana
    "brvm-ci": "XOF",   # BRVM (8 WAEMU countries)
    "luse-asi": "ZMW",  # Zambia
    "dse-asi": "TZS",   # Tanzania
    "use-asi": "UGX",   # Uganda
    "rse-asi": "RWF",   # Rwanda
    "sem-asi": "MUR",   # Mauritius
    "bse-dci": "BWP",   # Botswana
}


def get(session: requests.Session, path: str, **params) -> dict:
    r = session.get(f"{API}{path}", params={k: v for k, v in params.items() if v}, timeout=30)
    body = r.json()
    if not body.get("success"):
        err = body.get("error", {})
        raise RuntimeError(f"{path}: {err.get('code')} {err.get('message')}")
    return body


def pct(a: float | None, b: float | None) -> float | None:
    if not a or not b or a <= 0 or b <= 0:
        return None
    return (b - a) / a * 100


def on_or_before(rows: list[dict], day: str, key: str) -> dict | None:
    """Latest row dated on or before `day` that has a value for `key`."""
    best = None
    for r in rows:
        if r["day"] <= day and r.get(key):
            best = r
    return best


def dollar_returns(index_points: list[dict], fixings: list[dict], start: str) -> dict | None:
    pts = [p for p in index_points if p["date"] >= start and p.get("close")]
    if len(pts) < 2 or not fixings:
        return None
    base, end = pts[0], pts[-1]
    # FX at the base: the fixing on or before the base date, else the first one after it.
    fx0_usdt = on_or_before(fixings, base["date"], "close") or next((f for f in fixings if f.get("close")), None)
    fx0_off = on_or_before(fixings, base["date"], "official") or next((f for f in fixings if f.get("official")), None)
    fx1_usdt = on_or_before(fixings, end["date"], "close")
    fx1_off = on_or_before(fixings, end["date"], "official")
    if not (fx0_usdt and fx0_off and fx1_usdt and fx1_off):
        return None
    local = pct(base["close"], end["close"])
    usd_off = pct(base["close"] / fx0_off["official"], end["close"] / fx1_off["official"])
    usd_usdt = pct(base["close"] / fx0_usdt["close"], end["close"] / fx1_usdt["close"])
    return {
        "from": base["date"],
        "to": end["date"],
        "local": local,
        "usd_official": usd_off,
        "usd_stablecoin": usd_usdt,
        "gap_pts": None if usd_off is None or usd_usdt is None else usd_off - usd_usdt,
    }


def fmt(v: float | None) -> str:
    return "—" if v is None else f"{v:+.1f}%"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="start", default=(date.today() - timedelta(days=30)).isoformat(),
                    help="start date YYYY-MM-DD (default: 30 days ago; earlier than that needs a Pro key)")
    ap.add_argument("--csv", help="also write results to this CSV file")
    args = ap.parse_args()

    key = os.environ.get("MANSA_API_KEY")
    if not key:
        print("Set MANSA_API_KEY (free key: https://mansaapi.com/docs#get-api-key)", file=sys.stderr)
        return 1

    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {key}"

    results = []
    for slug, ccy in INDICES.items():
        try:
            hist = get(s, f"/markets/indices/{slug}/history", **{"from": args.start})["data"]
            fx = get(s, f"/stablecoins/fixings/{ccy}", **{"from": args.start})
        except RuntimeError as e:
            print(f"skip {slug}: {e}", file=sys.stderr)
            continue
        note = fx["meta"].get("history_note")
        if note:
            print(f"note ({ccy}): {note}", file=sys.stderr)
        r = dollar_returns(hist["points"], fx["data"], args.start)
        if r:
            results.append({"index": hist["index_code"], "country": hist["country"], "currency": ccy, **r})

    results.sort(key=lambda r: r["usd_stablecoin"] if r["usd_stablecoin"] is not None else -1e9, reverse=True)

    print(f"\n{'Index':<10} {'Ccy':<4} {'Local':>8} {'USD off.':>9} {'USD USDT':>9} {'Gap':>8}  Period")
    for r in results:
        gap = "—" if r["gap_pts"] is None else f"{r['gap_pts']:+.1f}pt"
        print(f"{r['index']:<10} {r['currency']:<4} {fmt(r['local']):>8} {fmt(r['usd_official']):>9} "
              f"{fmt(r['usd_stablecoin']):>9} {gap:>8}  {r['from']} → {r['to']}")
    print("\nGap > 0: the official rate overstates the dollar return.")
    print("Source: Mansa Markets Stablecoin Premium Index, https://www.mansamarkets.com/stablecoins")

    if args.csv and results:
        with open(args.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            w.writeheader()
            w.writerows(results)
        print(f"wrote {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
