---
title: "ASCENT Plugin"
description: "Skill plugin reference for reading the live space-economy terminal from chat — sector index, equity quotes, rocket launches, AMPLITUDE oracle state, on-chain space tokens, news, and earnings."
---

# ASCENT Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before invoking any swap or stake action. This plugin's read endpoints (sector index, launches, news, etc.) are public and require no Base Account — but transactional helpers (buy / stake / claim / burn) route through Base MCP's `swap` and `send_calls` tools and need an authenticated session.

[ASCENT](https://ascent-production.up.railway.app) is a live terminal for the space economy. It tracks the eight publicly-traded space companies (RKLB, LUNR, ASTS, PL, RDW, IRDM, MNTS, SPIR) as a sector index (`ASCENT-8`), pushes that index level on-chain into the `OracleAmplifier` contract on Base, and derives a deterministic yield multiplier (`AMP`) for the `$ASCENT` token. The same backend also surfaces upcoming rocket launches across every major provider, filtered sector news, on-chain space-themed tokens, and earnings calendars.

This plugin gives the agent read access to everything the terminal renders, plus prepare endpoints for token actions on the `$ASCENT` ERC-20 (Base mainnet) once the token is live.

**Prerequisite:** `ascent-production.up.railway.app` must be on the Base MCP `web_request` allowlist. If requests are rejected, inform the user and fall back to the harness's HTTP/fetch tool if one is available.

**Chain:** Base mainnet (chainId `8453` / `0x2105`)

---

## API

Base URL: `https://ascent-production.up.railway.app`

All read endpoints are public, cached server-side (15–60s TTL depending on data source), and return JSON. No auth required.

### `GET /api/equities`

Real-time quotes + intraday sparklines for the eight ASCENT-8 constituents. Finnhub primary (quotes) + Yahoo Finance fallback (sparklines, volume, market state).

```json
{
  "ok": true,
  "ts": 1779778383510,
  "universe": ["RKLB", "LUNR", "ASTS", "PL", "RDW", "IRDM", "MNTS", "SPIR"],
  "rows": [
    {
      "sym": "RKLB",
      "name": "Rocket Lab USA",
      "kind": "launch",
      "price": 135.76,
      "prev": 132.51,
      "change": 3.25,
      "pct": 2.45,
      "open": 132.84,
      "high": 136.42,
      "low": 131.95,
      "volume": 32970699,
      "avgVolume": 32970699,
      "currency": "USD",
      "exchange": "NASDAQ",
      "marketState": "REGULAR",
      "sparkline": [132.84, 133.10, 133.45, /* … 79 5-minute candles … */ 135.76],
      "source": "finnhub"
    }
  ],
  "index": {
    "level": 107.89,
    "pct": 7.88,
    "constituents": 8,
    "weighting": "equal"
  },
  "primarySource": "finnhub",
  "sources": ["finnhub", "yahoo"]
}
```

Field notes:

- `kind` — one of `launch | lunar | satcom | earthobs | manuf | transport`. Use to group answers when a user asks "show me satcoms" or "show me launch companies".
- `pct` is percent (e.g. `2.45` = +2.45%), not a fraction.
- `marketState` — `PRE`, `REGULAR`, `AFTER`, `CLOSED`. Surface this when the user asks "are markets open?".
- `index.level` — the ASCENT-8 sector index. Baseline is `100.00` (equal-weighted average daily % change + 100).
- `sparkline` — typically 79 5-minute closes (one trading day). Use for ASCII charts or to answer "is RKLB trending up today?".

### `GET /api/launches`

Next rocket launches across every major provider (SpaceX, ULA, RocketLab, CASC, ISRO, etc.). Sourced from RocketLaunch.Live, cached 5 minutes.

```json
{
  "ok": true,
  "ts": 1779778202551,
  "count": 5,
  "next": {
    "provider": "SpaceX",
    "mission": "Starlink (17-37)",
    "netTs": 1779804000000,
    "netStr": "May 26",
    "precision": "day",
    "details": "A SpaceX Falcon 9 rocket will launch the Starlink (17-37) mission on Tuesday, May 26, 2026 at 2:00 PM (UTC).",
    "vehicle": "Falcon 9",
    "pad": "SLC-4E",
    "upcoming": true
  },
  "upcoming": [/* up to 12 items, same shape */]
}
```

Field notes:

- `netTs` — UTC milliseconds. Use to compute `T-minus` countdowns when the user asks "when's the next SpaceX launch?".
- `precision` — `hour` if a launch window is set, `day` if the date is still vehicle-day-precision. Reflect this in the answer ("on/around May 26" vs "May 26 at 2:00 PM UTC").
- `provider` — surfaces are SpaceX, ULA, Rocket Lab, CASC, ISRO, etc. Filter by this when the user asks for a specific provider.

### `GET /api/amplifier`

Live `OracleAmplifier` state — derived deterministically from the ASCENT-8 index. Same numbers the on-chain contract sees after the off-chain operator pushes the next index update.

```json
{
  "ok": true,
  "ts": 1779778383510,
  "indexLevel": 107.89,
  "indexLevelE2": 10789,
  "multiplier": 1,
  "multiplierE4": 10000,
  "multiplierStr": "1.00×",
  "regime": "normal regime",
  "regimeMode": "NORMAL",
  "flowDescription": "Sell-tax ETH → stakers (1:1) · reserve untouched",
  "amplified": false,
  "defense": false,
  "next": {
    "levelTarget": 110,
    "distance": 2.11,
    "multStrAtTarget": "1.25×",
    "label": "+10% sector move"
  },
  "source": "OracleAmplifier (off-chain mirror) · contract pending deploy"
}
```

Field notes:

- `regimeMode` — `NORMAL | AMPLIFIED | DEFENSE`. Drives different rhetoric in responses ("sector flat, stakers earn 1:1" vs "sector rip — stakers compounding 2×" vs "sector dump — protocol buying back $ASCENT").
- `multiplier` is a plain float (e.g. `1.5`); `multiplierE4` is the on-chain int representation (`15000`). Use the float for chat answers.
- `next.distance` — sector-points until the next threshold flip. Surface this when the user asks "how close are we to amplified mode?".
- `defense` boolean is `true` when the index drops ≥10% from its rolling baseline. Defense mode routes all sell-tax fees to buyback the token from the LP.

### `GET /api/tokens`

On-chain space-themed tokens currently tradeable on Base and Ethereum mainnet. Sourced from DexScreener, filtered to `liq ≥ $5k · vol24 ≥ $100 · MC ≥ $10k · age > 12h`, deduped by contract address.

```json
{
  "ok": true,
  "ts": 1779778500000,
  "count": 5,
  "base": [
    {
      "chain": "base",
      "pair": "0x...",
      "ca": "0x...",
      "symbol": "ORB",
      "name": "ORBIT",
      "priceUsd": 0.0000312,
      "change24h": 14.5,
      "change1h": 2.1,
      "vol24": 124574,
      "liq": 26985,
      "fdv": 312000,
      "mc": 312000,
      "pairCreated": 1779000000000
    }
  ],
  "eth":  [/* up to 12 items */],
  "movers": {
    "gainers": [/* top 8 by change24h */],
    "losers":  [/* bottom 8 by change24h */]
  }
}
```

Field notes:

- `ca` — the ERC-20 contract address. Pass verbatim to Base MCP's `swap` tool as `toAsset` to buy.
- `pair` — Uniswap V3/V4 pair address on the listed chain. Use for DexScreener links: `https://dexscreener.com/{chain}/{pair}`.
- Don't surface tokens with `liq < $10k` as "tradeable" without warning — the filter floor is permissive on purpose to show new launches.

### `GET /api/news`

Filtered sector news. Sources: Space.com, SpaceNews, NSF, Universe Today, Hacker News (Algolia). RSS-only, cached 10 minutes.

```json
{
  "ok": true,
  "ts": 1779778500000,
  "count": 30,
  "items": [
    {
      "id": "spacenews-12345",
      "title": "FAA clears Starbase for Starship Flight 14 window",
      "url": "https://spacenews.com/...",
      "source": "SPACENEWS",
      "ts": 1779770000000,
      "tickers": ["RKLB"],
      "sentiment": "BULL"
    }
  ],
  "sources": ["SPACE.COM", "SPACENEWS", "NSF", "UNIVERSE", "HN"]
}
```

Field notes:

- `tickers` — auto-tagged tickers mentioned in the headline (subset of the ASCENT-8 universe). Empty array if no constituent is mentioned.
- `sentiment` — `BULL | BEAR | NEUTRAL` from keyword scoring. Don't treat as financial advice; it's just a coarse heuristic.

### `GET /api/earnings`

Upcoming earnings calendar for the ASCENT-8 universe (next 90 days). Finnhub `/calendar/earnings`, cached 15 minutes.

```json
{
  "ok": true,
  "ts": 1779778500000,
  "rows": [
    {
      "sym": "RKLB",
      "date": "2026-08-12",
      "hour": "AMC",
      "quarter": 2,
      "year": 2026,
      "epsEstimate": -0.08,
      "epsActual": null,
      "revenueEstimate": 142000000,
      "revenueActual": null
    }
  ]
}
```

Field notes:

- `hour` — `BMO` (before market open) / `AMC` (after market close) / `DMH` (during market hours) / `null` if unknown.
- `null` values for `epsActual` / `revenueActual` mean the report hasn't happened yet. Don't surface them as zeros.

### `GET /api/all`

Bundled snapshot — one round-trip returning `equities`, `launches`, `news`, `tokens`, `amplifier`, `earnings`. Use this when the user asks "what's the space sector doing right now?" — it's the single best general-purpose call.

```json
{
  "ok": true,
  "ts": 1779778500000,
  "elapsedMs": 142,
  "equities":  { /* same as /api/equities */ },
  "launches":  { /* same as /api/launches */ },
  "news":      { /* same as /api/news */ },
  "tokens":    { /* same as /api/tokens */ },
  "amplifier": { /* same as /api/amplifier */ },
  "earnings":  { /* same as /api/earnings */ }
}
```

### `GET /api/chart/:sym?interval=5m&range=1d`

Yahoo Finance chart proxy for an individual ASCENT-8 ticker. Returns OHLCV candles. Used by the in-terminal chart modal. Pass `interval` of `5m | 15m | 1h | 1d` and `range` of `1d | 5d | 1mo | 3mo`.

```json
{
  "chart": {
    "result": [{
      "meta": { "symbol": "RKLB", "regularMarketPrice": 135.76, /* … */ },
      "timestamp": [1779700000, 1779700300, /* … */],
      "indicators": {
        "quote": [{
          "open":   [132.84, 132.91, /* … */],
          "high":   [133.10, 133.05, /* … */],
          "low":    [132.50, 132.60, /* … */],
          "close":  [132.91, 132.88, /* … */],
          "volume": [148230, 92150, /* … */]
        }]
      }
    }]
  }
}
```

Field notes:

- Use this for "show me RKLB's price action today" / "draw RKLB the last week" — much richer than the sparkline in `/api/equities`.
- Server-cached 30s, so repeated calls within that window cost nothing extra.

---

## Sample Prompts

Once installed, users in any MCP client can ask:

```text
What is the space sector doing right now?
```

```text
When is the next SpaceX launch and what mission?
```

```text
Is the ASCENT amplifier amplified right now?
```

```text
Show me the on-chain space tokens trending today.
```

```text
What's RKLB's price action today?
```

```text
Which space company reports earnings next?
```

The agent should call the relevant `GET /api/*` endpoint, surface the data inline, and offer follow-up actions where on-chain (e.g. "want me to swap into ORB?" — route through Base MCP's `swap` tool with `toAsset = the ca field`).

---

## Phase 2 — Transactional Endpoints (post token launch)

When the `$ASCENT` ERC-20 ships on Base, this plugin will add prepare endpoints returning unsigned calldata for the user to approve in their Base Account. Until then, this section is a forward reference.

### `GET /api/prepare/buy?amountEth=0.1`

Returns Uniswap V4 swap calldata for ETH → `$ASCENT`. Single-call envelope shape, same as the bankr swap path.

```json
{
  "ok": true,
  "data": {
    "to":      "0x...uniswap-v4-router",
    "value":   "0x16345785D8A0000",
    "data":    "0x...",
    "chainId": 8453
  }
}
```

Map to `send_calls`:
```json
{
  "chain": "base",
  "calls": [
    { "to": "0x...uniswap-v4-router", "value": "0x16345785D8A0000", "data": "0x..." }
  ]
}
```

### `GET /api/prepare/stake?amountAscent=1000&tierDays=90`

Returns approve + deposit transactions as an ordered batch (the user signs once, Base MCP executes both).

```json
{
  "transactions": [
    { "step": "approve", "to": "0x...ascent-erc20", "data": "0x095ea7b3...", "value": "0x0", "chainId": 8453 },
    { "step": "stake",   "to": "0x...ascent-staking", "data": "0x...", "value": "0x0", "chainId": 8453 }
  ]
}
```

Map to `send_calls`:
```json
{
  "chain": "base",
  "calls": [
    { "to": "0x...ascent-erc20",   "value": "0x0", "data": "0x095ea7b3..." },
    { "to": "0x...ascent-staking", "value": "0x0", "data": "0x..." }
  ]
}
```

`tierDays` values: `30 | 90 | 180 | 365`. Each maps to a yield-weight on `AscentStaking.sol` (1.0× / 1.5× / 2.5× / 5.0× respectively).

### `GET /api/prepare/claim`

Returns a single unsigned `claim()` calldata for the user's current pending yield.

```json
{
  "ok": true,
  "data": {
    "to":      "0x...ascent-staking",
    "value":   "0x0",
    "data":    "0x4e71d92d",
    "chainId": 8453
  }
}
```

### `GET /api/prepare/burn-for-patch?amountAscent=1000`

Burns ASCENT for a `MissionPatch` ERC-721 NFT (on-chain SVG generator, no IPFS).

```json
{
  "ok": true,
  "data": {
    "to":      "0x...mission-patch",
    "value":   "0x0",
    "data":    "0x...",
    "chainId": 8453
  }
}
```

---

## Security

- All read endpoints are public and rate-limited at the Express server level.
- No private keys are ever touched by the ASCENT backend — all transactions are constructed as unsigned calldata and returned to the agent, which routes them through Base MCP's standard approval flow.
- The `OracleAmplifier` contract on Base is operator-pushed (single-key) for the off-chain index → on-chain mirror. The multiplier derivation function on-chain is deterministic and view-only; the only state the operator can mutate is the index level itself.
- Buyback wallet (DEFENSE mode) is multisig-gated.

---

## Source

The full backend powering this plugin is at https://ascent-production.up.railway.app. Public dashboards at:

- Landing: https://ascent-production.up.railway.app/
- Live terminal: https://ascent-production.up.railway.app/terminal

Contact: [@base](https://x.com/base) DM or open an issue at the ASCENT repo.
