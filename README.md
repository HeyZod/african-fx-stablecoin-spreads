# african-fx-stablecoin-spreads

**What did African stock markets actually return in dollars?**

Most dollar returns for African markets are computed at the official exchange rate. In many
countries that is not the rate a foreign investor can actually get out at. The USDT
peer-to-peer market is a live, observable alternative. This repo computes index returns three ways:

| | |
|---|---|
| **Local** | index close to close, local currency |
| **USD, official** | index ÷ official rate at both ends |
| **USD, stablecoin** | index ÷ USDT P2P mid rate at both ends |

The gap between the last two is how much the official rate flatters the dollar return.

## Results: 15 Aug → 23/24 Nov 2026

| Index | Market | Local | USD, official | USD, stablecoin | Gap |
|---|---|---:|---:|---:|---:|
| RSE ASI | Rwanda | +3.8% | +3.5% | +2.9% | +0.6 pts |
| DSE ASI | Tanzania | +3.3% | +2.4% | +1.5% | +1.0 pts |
| SEM ASI | Mauritius | +0.2% | +0.6% | +0.7% | −0.1 pts |
| USE ASI | Uganda | +11.8% | −0.7% | −2.0% | +1.2 pts |
| NGX ASI | Nigeria | +1.7% | −0.8% | −2.1% | +1.3 pts |
| NSE ASI | Kenya | −1.9% | −2.4% | −3.5% | +1.0 pts |
| BRVM-CI | WAEMU | −4.9% | −9.8% | −11.0% | +1.2 pts |
| GSE-CI | Ghana | −8.7% | −15.5% | −14.9% | −0.6 pts |
| JSE ASI | South Africa | −7.2% | −14.2% | −14.9% | +0.7 pts |
| LuSE ASI | Zambia | −7.5% | −15.5% | −16.4% | +0.9 pts |
| EGX 30 | Egypt | −8.9% | −15.7% | −16.6% | +0.9 pts |
| MASI | Morocco | −11.0% | −17.5% | −19.4% | +1.9 pts |

Botswana (BSE DCI) is left out of this table: the start of its window falls on a thin
order-book day where the USDT rate printed a 9% premium, which distorts the comparison.

Takeaways:

- **In 10 of 12 markets the official rate overstated the dollar return**, by 0.6 to 1.9
  percentage points in about 14 weeks.
- **Currency, not stocks, decided the outcome.** Uganda's index rose 11.8% in shillings and
  lost 2.0% in stablecoin dollars. Morocco fell 11.0% locally and 19.4% in stablecoin dollars.
- Write-up: https://mansaapi.com/blog/african-stocks-true-dollar-returns
- Live version of this table: https://www.mansamarkets.com/stablecoins

## Run it

```bash
pip install -r requirements.txt
export MANSA_API_KEY=...          # free key: https://mansaapi.com/docs#get-api-key
python true_dollar_returns.py     # last 30 days
python true_dollar_returns.py --from 2026-08-15 --csv returns.csv   # full history (Pro key)
python premium_now.py             # today's premium, every covered currency
```

A free key returns the last 30 days of stablecoin fixings. History from 15 Aug 2026 needs a
Pro key; the script tells you if your window was clipped.

## Where the rates come from

The **Mansa Markets Stablecoin Premium Index** samples live USDT offers on public
peer-to-peer marketplaces every hour for 24 African currencies (36 countries). Offers from
merchants with under 90% completion, fewer than 20 completed orders or under $200 available
are dropped. The rate is the volume-weighted mean of the tightest cluster of offers that agree
within 1.5%. If no cluster forms, no rate is published that hour.

- Methodology: https://www.mansamarkets.com/stablecoins/methodology
- API: https://mansaapi.com/stablecoin-fx-api

## Caveats

- History starts 15 Aug 2026, so windows are short.
- The stablecoin rate is a retail P2P rate, not an institutional FX quote. It is a better
  read of where dollars actually change hands in markets with a parallel rate, not a price
  you can trade size at.
- Index levels are price indices (no dividends).

## Licence

Code: MIT. Data: cite as "Mansa Markets Stablecoin Premium Index" with a link.
