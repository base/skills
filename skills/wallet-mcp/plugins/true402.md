---
title: "true402 Plugin"
description: "Pre-trade token, address and transaction risk checks over x402; paid calls route through Wallet MCP x402 request tools."
tags: [token-safety, token-launches, memecoins, trading]
name: true402
version: 0.1.0
integration: http-api
chains: [base, ethereum, bsc]
requires:
  shell: none
  allowlist: [true402.dev]
  externalMcp: null
  cliPackage: null
auth: none
risk: []
---

# true402 Plugin

> [!IMPORTANT]
> Run Wallet MCP onboarding first (see `SKILL.md`). true402 is an independent third-party service: its results are heuristic evidence from on-chain reads, not a guarantee and not advice. Every check is a single paid `POST`, paid through Wallet MCP `initiate_x402_request` → user approval → `complete_x402_request`. There is no separate true402 MCP server.

## Overview

[true402](https://true402.dev) answers "is this token, address or transaction safe to touch?" before an agent buys, approves or signs on Base, Ethereum or BSC. It reads on-chain state directly: ownership, mintability, liquidity depth, a gas-free buy→sell honeypot simulation, deployer history, and for an unsigned transaction an `eth_call` simulation plus decoded intent (for example an unlimited approval, judged on the spender). This plugin only reads: it returns a risk assessment and never builds or submits calldata. Use it before another plugin's `swap` or `send_calls`, not instead of one.

## Surface Routing

| Capability | HTTP-capable harness (Claude Code, Codex, Cursor) | Chat-only (Claude.ai, ChatGPT) |
|---|---|---|
| Unpaid call (free allowance or `402` quote) | Harness HTTP tool, `POST` with a JSON body. | Not available — the API is `POST`-only, so the user-paste GET fallback cannot reach it. Go straight to the paid path. |
| Paid check | Wallet MCP `initiate_x402_request` → approval → `get_request_status` → `complete_x402_request`. | Same Wallet MCP x402 request tools. |
| Host refused by Wallet MCP | — | Stop and tell the user this surface cannot reach true402. Do not retry through `web_request` or construct a paste URL. |

Decision order and the GET-only limit on consumer surfaces: see [custom-plugins.md](../references/custom-plugins.md).

## Endpoints

Base URL: `https://true402.dev/api`. Every route is `POST` with `Content-Type: application/json` and answers `405` to any other method. Prices are USDC on Base; always pay the amount in the live `402`, not the table.

| Route | Body | Price | Returns |
|---|---|---|---|
| `/v1/token-safety` (Base), `/v1/ethereum/token-safety`, `/v1/bsc/token-safety` | `{ "token": "0x…" }` | $0.005 | `ownership`, `mintable`, `liquidity`, `honeypot`, `score` (0–100), `risk`, `flags` |
| `/v1/{base,ethereum,bsc}/token-report` | `{ "token": "0x…" }` | $0.01 | token-safety plus a `verdict` object; on Base it also folds in recent liquidity removals and whale swaps |
| `/v1/{base,ethereum,bsc}/address-safety` | `{ "address": "0x…" }` | $0.005 | `score`, `risk`, `flags` for any EOA or contract |
| `/v1/{base,ethereum}/deployer-check` | `{ "token": "0x…" }` | $0.008 | who deployed the token and that wallet's age, balance and prior contracts |
| `/v1/base/tx-preflight` | `{ "from": "0x…", "to": "0x…", "data": "0x…", "value": "0" }` | $0.008 | `simulation`, `intent`, `counterparty`, `findings`, `risk`, `verdict`, `limits` |
| `/v1/base/dossier` | `{ "token": "0x…" }` | $0.10 | `rating`, plain-language `reasons`, deployer and liquidity-history sections, `limits` |

Result vocabularies:

- `risk` on token, address and deployer checks: `low` \| `medium` \| `high` \| `critical`.
- `verdict.rating` (token-report) and `rating` (dossier): `avoid` \| `caution` \| `ok`.
- tx-preflight `risk`: `reverts` \| `high` \| `medium` \| `none-observed`. It never answers "safe".
- `flags` name what was found **and what could not be checked** (e.g. `honeypot_not_checked`); `limits` lists what a result cannot establish.

Unpaid response: either `200` with the result and an `X-Free-Trial` header (a small per-IP daily allowance on some routes), or `402` with an x402 v2 challenge. The first `accepts` entry is `scheme: exact`, `network: eip155:8453`, `asset` Base USDC, and `amount` in 6-decimal atomic units.

The full request/response schema, with a worked example body for every route, is at `https://true402.dev/api/openapi.json`.

## Orchestration

### Check a token before buying it

1. Identify the token address and chain (`base`, `ethereum` or `bsc`). If the user named a symbol, resolve it to an address first — never check a guessed address.
2. Pick the route: `token-safety` for a quick screen, `token-report` for a verdict, `dossier` (Base only) when the user wants reasons and limits spelled out.
3. On an HTTP-capable harness, send the unpaid `POST`. A `200` is the answer — skip to step 6.
4. Otherwise read the `402` `accepts` entry for `eip155:8453` and check it against the payment guardrails in `## Notes`. Tell the user the price and get a yes.
5. Call Wallet MCP `initiate_x402_request` with the route and body, show the approval URL, poll `get_request_status` only after the user acts, then call `complete_x402_request(requestId)`.
6. Report `risk` / `rating`, the `flags`, and the `limits`. The buy decision stays with the user; if they proceed, hand off to the swap flow (Wallet MCP `swap`, or the relevant plugin).

### Preflight a transaction before `send_calls`

1. After another plugin has produced unsigned calls, get the sender from Wallet MCP `get_wallets`.
2. For each call on Base, `POST /v1/base/tx-preflight` with `{ from, to, data, value }`, value in wei as a decimal string. Pay through the same x402 flow if challenged.
3. Show the `risk`, `findings` and `limits` before the approval step. For `reverts`, explain that the simulation failed and the call would likely fail on-chain; for `high` or `medium`, name each finding. The user decides whether to submit.
4. Submission of the checked calls stays with the plugin that built them.

## Submission

Wallet MCP `initiate_x402_request`, `get_request_status` and `complete_x402_request`, for the paid read only. This plugin never calls `send_calls`, `swap` or `sign`.

```
method       POST
resource     https://true402.dev/api<route>
body         the JSON body from ## Endpoints
maxPayment   accepts[i].amount / 10^6   (the eip155:8453 entry; USDC has 6 decimals)
```

Pay exactly the quoted `amount`. The API accepts a payment for the exact quoted amount only, so a larger or smaller authorization is refused, not rounded.

## Example Prompts

**"Is 0x4200000000000000000000000000000000000006 safe to buy on Base?"**
1. Route `POST /v1/base/token-report` with `{ "token": "0x4200…0006" }`.
2. Unpaid call first on an HTTP-capable harness; otherwise quote the `402` price and get approval.
3. Pay via `initiate_x402_request` → `complete_x402_request`.
4. Report `verdict.rating`, `reasons`, `flags` and `limits`; the user decides whether to continue.

**"Check this new Bankr launch before I ape in."**
1. Take the contract address from the Bankr plugin's launch feed.
2. `POST /v1/token-safety`; for a fresh launch also `POST /v1/base/deployer-check`.
3. Report the result plainly — for example that `flags` contains `honeypot_sell_blocked`, or that `risk` is `high`/`critical` — and let the user decide whether to continue to the swap.

**"Before you send that approval, check it."**
1. Take the unsigned `{ to, data, value }` from the pending `send_calls` batch; `from` from `get_wallets`.
2. `POST /v1/base/tx-preflight` for each call.
3. An unlimited approval comes back as a `high` finding naming the spender — show it before the approval step.

**On Claude.ai, where Wallet MCP refuses the host:**
1. Explain that this surface cannot reach true402.
2. Stop. Suggest an HTTP-capable harness; do not build a paste URL for a `POST` API.

## Notes

- **Payment guardrails.** Each paid check settles USDC on Base when the result is served, with no refund. Confirm the price with the user before `initiate_x402_request`. Pay only an `accepts` entry with `network: eip155:8453`, `asset` = Base USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`, `payTo` = `0xFe257Ef6Dc89F5b688aC52Ef3eb8648C629fA9C4`, and an `amount` matching the route's listed price; refuse anything else. One check per user request unless they ask for more.
- **Reading results.** `ok`, `low` and `none-observed` mean nothing bad was *observed*. Always show `flags` and `limits`. A flag such as `honeypot_not_checked` means the test did not run, not that it passed. Do not describe a token or transaction as "safe".
- Payment is always Base USDC, even when the checked token is on Ethereum or BSC.
- A Solana route exists (`POST /v1/solana/token-safety`, SPL mint address) but Wallet MCP has no Solana chain string, so it is outside this plugin's `chains`.
- `tx-preflight` takes no key and no signature, so it cannot broadcast. It describes the calldata supplied, which is not necessarily the bytes eventually signed.
- Simulations reflect chain state at the current block. Re-check if the user waits before acting.
