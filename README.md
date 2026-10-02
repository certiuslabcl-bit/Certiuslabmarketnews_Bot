# QuantNews: Telegram Market News Impact Bot

Free-tier bot. RSS news -> keyword filter -> dedupe -> LLM impact analysis (geopolitics, macro,
semiconductors, weather, investor flows) -> real prices -> entry/stop/targets computed in code -> Telegram.

**Research signals only. Not financial advice. Paper trade first.**

## Setup (about 10 minutes)

1. **Telegram bot**: message `@BotFather` -> `/newbot` -> copy the token.
   Send any message to your new bot, then open
   `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy `"chat":{"id": ...}`.
2. **LLM** (pick one, put in `.env`):
   - Azure OpenAI with free credits: deploy `gpt-4o-mini`, fill the `AZURE_*` vars, `LLM_MODEL` = deployment name.
   - Or free tiers: GitHub Models, Groq, Gemini (OpenAI-compatible URLs are in `.env.example`).
3. **Visual Studio / VS Code**: open this folder, then in the terminal:
   ```
   python -m venv .venv
   .venv\Scripts\activate          (Windows)   |   source .venv/bin/activate (Mac/Linux)
   pip install -r requirements.txt
   copy .env.example .env          (then edit .env)
   python bot.py --test            # you should get a Telegram message
   python bot.py --once            # one full cycle
   python bot.py                   # run continuously
   ```

## How trade levels work (all in code, not LLM)
- Price, ATR14, and 20d swing high/low come from `yfinance` (real data).
- Entry zone = last price +/- 0.25 ATR. If price already moved > 1.5 ATR today -> "wait for pullback".
- Stop = wider of 20d swing level or 1.5 ATR. T1 = 1.5R, T2 = 2.5R. Stops wider than 4 ATR are rejected.
- A trade idea only appears if LLM confidence >= 0.5, magnitude >= 3, priced-in probability <= 0.7.

## Tuning
- `ALERT_THRESHOLD` (default 0.55): raise to get fewer, stronger alerts.
- `MAX_LLM_CALLS_PER_CYCLE`: cap cost/free-tier usage.
- Edit `WATCHLIST`, `FEEDS`, `KEYWORDS` in `bot.py`.
- Edit `prompt.txt` to change analyst behavior.

## Backtest (do this before using real money)
Every alert is logged to `signals.csv`. After 4-8 weeks:
```
python backtest.py 10      # max holding days
```
You get win rate, average R, and results by category and confidence. Only trust a category if
it shows positive average R over a meaningful sample (30+ trades).

## Run 24/7 for free (no laptop needed): GitHub Actions
1. Create a GitHub account and a **new public repo** (public = unlimited free minutes; no secrets live in code).
2. Upload all files from this folder, including the hidden `.github/workflows/bot.yml`.
3. Repo -> **Settings -> Secrets and variables -> Actions -> New repository secret**. Add:
   `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, and your LLM secrets (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`
   or the `AZURE_OPENAI_*` ones). Unused ones can be left out.
4. **Actions tab -> QuantNews -> Run workflow** to test. After that it runs by itself every 15 min on weekdays and hourly on weekends.
5. Signals: open any run -> Artifacts -> `signals`, download `signals.csv`, then run `python backtest.py` on your laptop whenever you like.

Notes: GitHub cron can be delayed by a few minutes at busy times. State (seen news, signal log) is kept in the Actions cache between runs.
If you prefer a private repo, the free quota is 2,000 min/month, so change the cron to about every 30 min and weekdays only.

## Other hosting

- Easiest: run on your PC.
- Azure: Functions (Timer trigger, every 10 min) calling `python bot.py --once`. Note SQLite
  state is lost on stateless hosts, so use a mounted Azure Files share or switch `seen` to Table Storage.
- Always keep keys in `.env` or Azure Key Vault. Never commit `.env`.

## Known limits
- RSS has delay; this is not a low-latency system. Do not use it for scalping.
- yfinance is unofficial and can break or rate-limit; swap in Finnhub/Alpha Vantage if needed.
- Consensus data (CPI etc.) isn't fetched; the LLM only uses figures that appear in the article.
- Gaps can jump past stops. Size positions so a stop-out costs an amount you can afford to lose.
