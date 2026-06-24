---
title: "LoneStarOracle Plugin"
description: "39 AI data services for crypto intelligence, equity analysis, federal contracts, and real-world market signals — x402 micropayments on Base."
tags: [data, intelligence, crypto, equities, government, sentiment, options, onchain]
name: lonestaroracle
version: 0.1.0
integration: http-api
chains: [base]
requires:
  shell: none
  allowlist: [token.lonestaroracle.xyz, wallet.lonestaroracle.xyz, contract.lonestaroracle.xyz, news.lonestaroracle.xyz, equity.lonestaroracle.xyz, options.lonestaroracle.xyz, portfolio.lonestaroracle.xyz, macro.lonestaroracle.xyz, earnings.lonestaroracle.xyz, insider.lonestaroracle.xyz, floyd.lonestaroracle.xyz, chainscout.lonestaroracle.xyz, content.lonestaroracle.xyz, crownblock.lonestaroracle.xyz, realestate.lonestaroracle.xyz, agri.lonestaroracle.xyz, grid.lonestaroracle.xyz, rattler.lonestaroracle.xyz, cottonmouth.lonestaroracle.xyz, copperhead.lonestaroracle.xyz, ta.lonestaroracle.xyz, compute.lonestaroracle.xyz, metals.lonestaroracle.xyz, supply.lonestaroracle.xyz, latam.lonestaroracle.xyz, govedge.lonestaroracle.xyz, lease.lonestaroracle.xyz, stake.lonestaroracle.xyz, doc.lonestaroracle.xyz, aero.lonestaroracle.xyz, stable.lonestaroracle.xyz, launches.lonestaroracle.xyz, defi.lonestaroracle.xyz, whale.lonestaroracle.xyz, geo.lonestaroracle.xyz, cascade.lonestaroracle.xyz, wealth.lonestaroracle.xyz, bundle.lonestaroracle.xyz, weather.lonestaroracle.xyz]
  externalMcp: null
  cliPackage: null
auth: none
risk: []
---

# LoneStarOracle Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before calling any LoneStarOracle endpoint. The user's wallet address is needed to execute x402 payments via `send_calls`.

## Overview

LoneStarOracle (LSO) is an AI data oracle with 39 pay-per-query services covering crypto intelligence, equity research, federal contract procurement, on-chain analytics, and real-world market signals. All endpoints run on Base mainnet and accept x402 micropayments in USDC ($0.02–$2.00 per query). No API keys required.

**Payment wallet:** `0x52Ab53912D37759B2ad364f22dD06B16714b6C06`  
**USDC on Base:** `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`

---

## Surface Routing

| Capability | Where it runs |
|---|---|
| **All GET endpoints** — data reads across all 39 services | Every surface. Use Base MCP `web_request` in chat apps; harness HTTP tool in CLI environments. |
| **POST endpoints** — RattlerAI, CottonmouthAI, CopperheadAI audits; ContentForge; DocEdge; Floyd agent | CLI harnesses only (Claude Code, Cursor terminal). In chat-only surfaces, direct the user to the relevant subdomain (e.g. `rattler.lonestaroracle.xyz`) to submit via their browser. |

Do not submit payments or invoke POST operations without explicit user confirmation.

---

## x402 Payment Pattern

All LSO endpoints are gated by x402 micropayments. When an endpoint returns HTTP 402:

1. Parse the `X-Payment-Required` response header for:
   - `maxAmountRequired` — price in USDC atomic units (6 decimals, e.g. `50000` = $0.05)
   - `payTo` — always `0x52Ab53912D37759B2ad364f22dD06B16714b6C06`

2. Build USDC `transfer(address,uint256)` calldata:
   ```
   to:    0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
   value: 0x0
   data:  0xa9059cbb
          + 000000000000000000000000 + 52Ab53912D37759B2ad364f22dD06B16714b6C06
          + <maxAmountRequired as 32-byte hex, zero-padded to 32 bytes>
   ```

3. Execute via `send_calls`:
   ```json
   {
     "chain": "base",
     "calls": [{
       "to": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
       "value": "0x0",
       "data": "<transfer calldata>"
     }]
   }
   ```

4. Retry the original endpoint with header `X-Payment-Txhash: <confirmed_tx_hash>`.

Do not submit payment without explicit user confirmation of the price shown in the 402 response.

---

## Crypto Intelligence

### TokenScope — $0.15
Token due diligence: GoPlus risk score 0–10, honeypot detection, buy/sell tax, liquidity depth, holder concentration, ownership status, Claude AI verdict.

```
GET https://token.lonestaroracle.xyz/report
  ?address=<ERC-20 contract address>
  &chain=<eth|base|bsc|arb|poly>  (default: eth)
```

### BundleScope — $0.10
Token launch bundle and sniper detection. Scans first 3 blocks after launch for coordinated buys. Returns risk score, bundle wallets, and dump status.

```
GET https://bundle.lonestaroracle.xyz/scan
  ?address=<token contract address on Base>
```

### ChainScout — $0.05
On-chain analytics: whale movements, trending tokens, TVL shifts, narrative detection across Base and EVM chains.

```
GET https://chainscout.lonestaroracle.xyz/report
GET https://chainscout.lonestaroracle.xyz/whales
GET https://chainscout.lonestaroracle.xyz/trending
GET https://chainscout.lonestaroracle.xyz/tvl
GET https://chainscout.lonestaroracle.xyz/narrative
```

### WhaleAlert — $0.05
Real-time large wallet movement alerts and on-chain flow analysis.

```
GET https://whale.lonestaroracle.xyz/whales
```

### TokenLaunches — $0.05
New token launch scanner — recent deployments, deployer info, status.

```
GET https://launches.lonestaroracle.xyz/scan
```

### StablePulse — $0.05
Stablecoin health monitor: peg deviation, collateral ratios, depeg risk signals.

```
GET https://stable.lonestaroracle.xyz/pulse
GET https://stable.lonestaroracle.xyz/symbol/<SYMBOL>
GET https://stable.lonestaroracle.xyz/risk-summary
```

### DeFiRisk — $0.10
DeFi protocol risk assessment: smart contract exposure, liquidity concentration, protocol health.

```
GET https://defi.lonestaroracle.xyz/risk
  ?protocol=<protocol name or contract>
```

### StakeEdge — $0.05
DeFi staking yields, validator performance, and liquid staking signals.

```
GET https://stake.lonestaroracle.xyz/report
```

### AeroCheck — $0.05
Aerodrome and Base DeFi liquidity pool health checks.

```
GET https://aero.lonestaroracle.xyz/pool
  ?pair=<token pair>
```

### CascadeWatch — $0.10
Cross-protocol liquidation cascade risk monitor.

```
GET https://cascade.lonestaroracle.xyz/risk
GET https://cascade.lonestaroracle.xyz/cascade
GET https://cascade.lonestaroracle.xyz/report
```

---

## Wallet & Portfolio Risk

### WalletIntel — $0.15
Wallet risk scoring: GoPlus flags, sanction screening, interaction history, risk score 0–100.

```
GET https://wallet.lonestaroracle.xyz/score
  ?address=<wallet address>
```

### WealthPulse — $0.25
Cross-asset portfolio risk analyzer. Auto-fetches Base on-chain holdings (ERC-20 + ETH), values each position, calculates stablecoin % and concentration. Also accepts stock tickers and token contracts. Returns unified risk score 1–10 + AI narrative.

```
GET https://wealth.lonestaroracle.xyz/analyze
  ?wallet=<wallet address>
  &tickers=<comma-separated stock tickers, optional>
  &contracts=<comma-separated token contracts, optional>
```

### PortfolioRisk — $0.10
Equity/ETF portfolio concentration, volatility, and correlation analysis.

```
GET https://portfolio.lonestaroracle.xyz/analyze
  ?tickers=<comma-separated tickers, e.g. AAPL,MSFT,NVDA>
```

### ContractCheck — $0.05
Smart contract verification: source code status, proxy patterns, admin keys, upgrade risk.

```
GET https://contract.lonestaroracle.xyz/verify
  ?address=<contract address>
  &chain=<eth|base|bsc|arb|poly>
```

---

## Equity & Options Markets

### EquityScope — $0.05
Stock intelligence: buy/hold/sell signal, upside % to analyst target, P/E, EPS, health flags. AI analysis cached 30 min.

```
GET https://equity.lonestaroracle.xyz/equity
  ?ticker=<US stock ticker, e.g. NVDA>
```

### OptionsFlow — $0.05
Options flow for stocks AND crypto (BTC/ETH/SOL/AVAX via Deribit). Signal-first: bullish/bearish/neutral, conviction trade with USD premium, put/call ratio. Crypto under 1s, stocks cached 5 min.

```
GET https://options.lonestaroracle.xyz/flow
  ?ticker=<stock ticker or BTC|ETH|SOL|AVAX>
```

### TechAnalysis — $0.05
18 indicators + AI signal across 4 timeframes (15m/1h/4h/1d). Cached 5 min.

```
GET https://ta.lonestaroracle.xyz/analyze
  ?symbol=<ticker>
  &timeframe=<15m|1h|4h|1d>

GET https://ta.lonestaroracle.xyz/scan
  ?symbol=<ticker>
```

`/scan` returns all 4 timeframes with confluence score (strong_buy → strong_sell).

### InsiderFlow — $0.03
SEC Form 4 insider trading data — executive buy/sell transactions.

```
GET https://insider.lonestaroracle.xyz/trades
  ?ticker=<stock ticker>
```

### EarningsCalendar — $0.03
Earnings dates, consensus estimates, and beat/miss history. Last 4 quarters: EPS actual/estimate, surprise %, day-after price reaction, consecutive beats. Configurable `days_soon` window (default 7, max 90).

```
GET https://earnings.lonestaroracle.xyz/calendar
  ?tickers=<comma-separated tickers>
  &days_soon=<1-90>
```

### MacroPulse — $0.05
Macro indicators: Fed funds rate, GDP, inflation, yield curve, DXY.

```
GET https://macro.lonestaroracle.xyz/macro
```

---

## News & Sentiment

### NewsSentiment — $0.05
News sentiment for stocks and crypto. Crypto tickers (BTC/ETH/SOL/AVAX etc.) auto-detect and pull CoinDesk + CoinTelegraph. Returns bullish/bearish/neutral signal, headline analysis, and `aggregate_score` (−1.0 to +1.0).

```
GET https://news.lonestaroracle.xyz/news
  ?query=<ticker, token name, company, or topic>
```

---

## Federal Contracts & Government

### GovEdge — $0.20
Federal contract intelligence. `/report`: USASpending.gov awards $10M+, winning vendor stock ticker cross-reference, AI narrative. `/opportunities`: live SAM.gov solicitations by keyword, NAICS code, set-aside type — urgency flags for deadlines ≤14 days + AI BD briefing.

```
GET https://govedge.lonestaroracle.xyz/report
  ?min_amount=<USD, default 10000000>
  &days_back=<1-90, default 7>
  &agency=<agency name, optional>

GET https://govedge.lonestaroracle.xyz/opportunities
  ?keyword=<search term, optional>
  &naics=<NAICS code, optional>
  &set_aside=<SBA|8A|WOSB|HUBZone|VOSB|SDVOSB, optional>
  &days_back=<1-90, default 7>
```

---

## Energy, Commodities & Infrastructure

### CrownBlock — $1.00
Oil & gas and refined products intelligence: WTI, Brent, Henry Hub, refinery utilization, pipeline data, AI price outlook.

```
GET https://crownblock.lonestaroracle.xyz/report
```

### GridPulse — $0.03
US electricity grid demand, generation mix, and stress signals.

```
GET https://grid.lonestaroracle.xyz/report
```

### AgriPulse — $0.03
Agricultural commodity prices, USDA report triggers, crop condition indices.

```
GET https://agri.lonestaroracle.xyz/report
```

### IndustrialMetals — $0.03
Copper, aluminum, nickel, zinc, steel — prices and supply chain signals.

```
GET https://metals.lonestaroracle.xyz/report
```

### ComputePulse — $0.03
AI compute capacity, GPU availability, cloud pricing signals.

```
GET https://compute.lonestaroracle.xyz/report
```

### SupplyChainPulse — $0.03
Global supply chain disruption monitoring — shipping, port congestion, lead times.

```
GET https://supply.lonestaroracle.xyz/report
```

---

## Real Estate & Regional

### RealEstatePulse — $0.03
US mortgage rates, housing inventory, price trends, Fed impact signals.

```
GET https://realestate.lonestaroracle.xyz/report
```

### LeaseEdge — $0.15
Commercial real estate lease comps and market rate intelligence.

```
GET https://lease.lonestaroracle.xyz/report
```

### LatAmPulse — $0.03
Latin America economic intelligence — BRL, ARS, COP, MXN currencies, Argentina parallel rate.

```
GET https://latam.lonestaroracle.xyz/report
```

### GeoPulse — $0.07
Geopolitical risk by region: conflict zones, sanctions, political instability scores, commodity impact.

```
GET https://geo.lonestaroracle.xyz/risk
  ?region=<region name, optional>
```

---

## Weather

### WeatherOracle — $0.02
7-model ensemble weather forecast (GFS, ECMWF, ICON, GEM, HRRR, NAM, NBM) + 80-member probabilistic ensemble. Returns signal (YES/NO/PASS) and probability for temperature thresholds. Station-aligned to NWS ASOS used by Kalshi and Polymarket for settlement.

```
GET https://weather.lonestaroracle.xyz/forecast
  ?city=<Chicago|New York|Miami|Houston|Phoenix|Seattle|Denver|Atlanta|Boston|Los Angeles>
  &date=<YYYY-MM-DD>
  &threshold=<temperature in °F, optional>
  &direction=<greater|less, default: greater>
```

---

## Smart Contract Security Audits

> [!NOTE]
> Audit endpoints require POST and are available in CLI harnesses only. On chat-only surfaces, direct the user to the service subdomain.

### RattlerAI — $2.00
Smart contract security audit: Claude Opus + Slither static analysis. Returns vulnerabilities, severity ratings, attack surface summary.

```
POST https://rattler.lonestaroracle.xyz/audit
  body: { "contract": "<Solidity source or contract address>" }
```

### CottonmouthAI — $2.00
Smart contract audit with focus on DeFi protocol attack vectors and reentrancy.

```
POST https://cottonmouth.lonestaroracle.xyz/audit
  body: { "contract": "<Solidity source or contract address>" }
```

### CopperheadAI — $2.00
Smart contract audit with focus on access control, ownership, and privilege escalation.

```
POST https://copperhead.lonestaroracle.xyz/audit
  body: { "contract": "<Solidity source or contract address>" }
```

---

## Content & Documents

> [!NOTE]
> ContentForge and DocEdge require POST and are available in CLI harnesses only.

### ContentForge — $0.15
URL → LinkedIn post, tweets, newsletter, SEO content.

```
POST https://content.lonestaroracle.xyz/repurpose
  body: { "url": "<article or page URL>", "format": "linkedin|twitter|newsletter|seo" }
```

### DocEdge — $0.05
Document conversion and extraction — PDFs, contracts, financial filings.

```
POST https://doc.lonestaroracle.xyz/convert
  body: { "url": "<document URL>" }
```

---

## Autonomous Agent

> [!NOTE]
> Floyd requires POST and is available in CLI harnesses only.

### Floyd — $0.50
Hire Floyd autonomous coding agent. Floyd writes code and opens pull requests on GitHub.

```
POST https://floyd.lonestaroracle.xyz/task
  body: { "task": "<description>", "repo": "<owner/repo, optional>", "context": "<optional>" }
```

---

## Service Summary

| Category | Services | Price Range |
|---|---|---|
| Smart contract audits | RattlerAI, CottonmouthAI, CopperheadAI | $2.00 |
| Agent | Floyd | $0.50 |
| Token due diligence | TokenScope | $0.15 |
| Portfolio risk | WalletIntel, WealthPulse, DeFiRisk, PortfolioRisk | $0.10–$0.25 |
| Market intelligence | EquityScope, OptionsFlow, TechAnalysis, NewsSentiment | $0.05 |
| On-chain analytics | ChainScout, BundleScope, WhaleAlert, StablePulse, StakeEdge, AeroCheck, CascadeWatch | $0.05–$0.10 |
| Government | GovEdge | $0.20 |
| Earnings & macro | EarningsCalendar, MacroPulse, InsiderFlow | $0.03–$0.05 |
| Commodities & energy | CrownBlock, GridPulse, AgriPulse, IndustrialMetals, ComputePulse, SupplyChainPulse | $0.03–$1.00 |
| Real estate & regional | RealEstatePulse, LeaseEdge, LatAmPulse, GeoPulse | $0.03–$0.15 |
| Weather | WeatherOracle | $0.02 |
| Content & docs | ContentForge, DocEdge | $0.05–$0.15 |

All prices in USDC on Base mainnet. No subscriptions or API keys required.
