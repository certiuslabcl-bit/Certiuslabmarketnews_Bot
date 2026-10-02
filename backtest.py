"""
Backtest signals.csv: for each past signal, replay daily bars after the signal and
check whether Stop, T1 or T2 was hit first (stop assumed first if same bar = conservative).
Prints hit rate, average R, and results by category/confidence bucket.
Usage: python backtest.py [max_holding_days]
"""
import sys, pandas as pd, yfinance as yf

HOLD = int(sys.argv[1]) if len(sys.argv) > 1 else 10
df = pd.read_csv("signals.csv")
df = df[df["status"].isin(["TRADE_IDEA", "WAIT_FOR_PULLBACK"])].copy()
rows = []
for _, s in df.iterrows():
    ts = pd.to_datetime(s["ts_utc"], utc=True)
    h = yf.Ticker(s["ticker"]).history(start=ts.date(), auto_adjust=False)
    h = h[h.index >= ts.normalize()].head(HOLD)
    if h.empty:
        continue
    long = s["side"] == "LONG"
    entry, stop, t1, t2 = s["entry"], s["stop"], s["t1"], s["t2"]
    risk = abs(entry - stop)
    outcome, r = "TIME_EXIT", None
    for _, bar in h.iterrows():
        hit_stop = bar["Low"] <= stop if long else bar["High"] >= stop
        hit_t1 = bar["High"] >= t1 if long else bar["Low"] <= t1
        if hit_stop:
            outcome, r = "STOP", -1.0; break
        if hit_t1:
            outcome, r = "T1", 1.5; break
    if r is None:
        last = h["Close"].iloc[-1]
        r = ((last - entry) if long else (entry - last)) / risk
    rows.append({**s.to_dict(), "outcome": outcome, "R": round(r, 2)})

res = pd.DataFrame(rows)
if res.empty:
    print("No evaluable signals yet. Let the bot run a few weeks.")
else:
    print(res[["ts_utc", "ticker", "side", "outcome", "R"]].to_string(index=False))
    print(f"\nTrades: {len(res)} | Win rate: {(res.R > 0).mean():.0%} | Avg R: {res.R.mean():.2f} | Total R: {res.R.sum():.1f}")
    print("\nBy category:\n", res.groupby("category").R.agg(["count", "mean"]).round(2))
    res["conf_bucket"] = pd.cut(res["confidence"], [0, .6, .7, .8, 1.0])
    print("\nBy confidence:\n", res.groupby("conf_bucket", observed=True).R.agg(["count", "mean"]).round(2))
