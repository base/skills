---
title: "presign-guard Plugin"
description: "Pre-trade safety checks via the presign-guard HTTP API (free or paid with Wallet MCP x402) before any swap or send_calls on EVM chains."
tags: [security, token-safety, risk-check, trading, swap]
name: presign-guard
version: 0.3.0
integration: http-api
chains: [base, ethereum, arbitrum, optimism, polygon, bsc]
requires:
  shell: none
  allowlist: [presign-guard.fizzl.eu]
  externalMcp: null
  cliPackage: null
auth: none
risk: []
---

# presign-guard Plugin

> [!IMPORTANT]
> Run Wallet MCP onboarding first (see SKILL.md). This plugin only reads verdicts; it never submits a transaction. Paid checks are approved through Wallet MCP's x402 flow (`initiate_x402_request` → approval URL → `complete_x402_request`).

## Overview

[presign-guard](https://presign-guard.fizzl.eu) answers one question before your agent buys a token or signs a transaction: green, orange or red. It checks the token (honeypot, sell tax, mint or owner powers, thin or unlocked liquidity, fake look-alikes, very new token), the counterparty of a transaction or approval (flagged or sanctioned address, unverified contract, unlimited allowance), what a transaction really does (it is simulated against the latest block when the sending wallet is given) and the wallet's open approvals, on Base, Ethereum, Arbitrum, Optimism, Polygon and BSC. The plugin calls the presign-guard HTTP API to get a verdict and uses it to gate the user's own `swap` or `send_calls` (including calls prepared by other plugins such as Bankr, Clawnch, Uniswap or KyberSwap). A free quick verdict needs no payment; the full answer with reason codes costs $0.01 USDC on Base, paid through Wallet MCP's x402 tools.

## Surface Routing

Reads are plain HTTP. Follow the standard decision tree in [../references/custom-plugins.md](../references/custom-plugins.md).

| Capability | HTTP-capable harnesses (Claude Code, Codex, Cursor, …) | Chat-only (Claude.ai, ChatGPT) |
| - | - | - |
| Free token verdict (`GET /v1/token/quick`) | Harness HTTP tool. | `web_request` GET if `presign-guard.fizzl.eu` is allowlisted; otherwise the GET user-paste fallback works (all parameters are in the URL). |
| Paid token verdict (`GET /v1/token`) | Wallet MCP `initiate_x402_request` with method `GET`, then `complete_x402_request`. | Same Wallet MCP x402 tools (they work on every surface). |
| Paid transaction / approval / signature check (`POST /v1/check`) | Wallet MCP `initiate_x402_request` with method `POST` and the JSON body, then `complete_x402_request`. | Same. |
| Paid wallet approval audit (`GET /v1/approvals`) | Wallet MCP `initiate_x402_request` with method `GET`. | Same. |

The free quick check is limited to 10 calls per hour per caller IP; through a shared `web_request` egress that limit can be reached sooner. On a `429`, use the paid check instead of retrying.

## Endpoints

Base URL: `https://presign-guard.fizzl.eu`. Every answer has `verdict`: `green`, `orange` or `red`. Unpaid requests to paid routes return `402` with x402 payment requirements (USDC on Base; `/v1/token` and `/v1/approvals` also accept Solana USDC). Invalid input returns `400` before any payment; a failed check (`5xx`) is never charged.

### `GET /v1/token/quick` (free)

Query: `chain` (`base`, `ethereum`, `arbitrum`, `optimism`, `polygon`, `bsc`), `address` (the token contract).

```json
{ "chain": "base", "address": "0x8335…2913", "verdict": "green", "grade": "SAFE", "note": "Verdict only. GET /v1/token ($0.01) returns the reasons, summary and market data." }
```

### `GET /v1/token` ($0.01)

Same query as the quick check. Returns the verdict, a grade (`SAFE`, `CAUTION`, `RISKY`, `AVOID`), a one-line summary, reason codes and market data:

```json
{
  "verdict": "orange", "grade": "CAUTION",
  "one_liner": "CAUTION: high tax, liquidity not locked, 2 days old",
  "reasons": [{ "code": "TOKEN_HIGH_TAX", "severity": "orange" }, { "code": "LP_NOT_LOCKED", "severity": "orange" }, { "code": "NEW_TOKEN", "severity": "orange" }],
  "token": { "chain": "base", "address": "0x…", "name": "…", "symbol": "…" },
  "market": { "priceUsd": 0.0012, "liquidityUsd": 48000, "marketCapUsd": 900000, "volume24hUsd": 120000, "ageSeconds": 172800 }
}
```

### `POST /v1/check` ($0.01)

JSON body, one of:

* Transaction (what `send_calls` would send): `{ "type": "transaction", "chainId": 8453, "from": "0x…", "to": "0x…", "data": "0x…", "value": "0" }`. With `from` (the wallet that would send it) the transaction is simulated against the latest block, also inside routers, multicalls and batches: the answer gets a `simulation` field with every asset that leaves or arrives, and `HIDDEN_APPROVAL` (an approval the call doesn't show), `SIMULATION_NFT_OUT` (an NFT leaves the wallet) or `SIMULATION_FAILS` (it would revert) is orange.
* Token approval: `{ "type": "approval", "chainId": 8453, "token": "0x…", "spender": "0x…", "amount": "1000000" }` (`amount` in base units; `"0"` = revoke)
* EIP-712 signature (Permit, Permit2, EIP-3009, Seaport): `{ "type": "signature", "chainId": 8453, "typedData": { … } }`

Optional on all: `origin` (the site or dapp that asked; a domain under 30 days old is orange) and `intent` (one sentence: what the user wants to do, e.g. "swap 10 USDC for ETH"; a transaction that does something else, such as 5,000 USDC leaving, is orange `INTENT_MISMATCH`). Supported `chainId`: 8453 (Base), 1, 42161, 10, 137, 56.

```json
{ "verdict": "orange", "reasons": [{ "code": "UNLIMITED_APPROVAL", "severity": "orange", "subject": "0x0000…8ba3", "details": { "token": "0x8335…2913" } }] }
```

`POST /v1/check/explain` ($0.03) returns the same plus `explanation.text`, three to five plain-language sentences (`"lang": "en"` or `"nl"`).

### `GET /v1/approvals` ($0.02)

Query: `chain`, `address` (the wallet). Returns the verdict, a summary and every open ERC-20 allowance with its spender, which ones to revoke and a revoke.cash link.

## Orchestration

### Before buying a token (any `swap`, or a launch-feed plugin such as Bankr or Clawnch)

1. Take the target token's contract address and chain from the user or the other plugin's output.
2. Call `GET /v1/token/quick`. If it is `green`, continue to the swap. If it is `orange` or `red`, or the user wants the reasons, run the paid `GET /v1/token`.
3. For the paid check: Wallet MCP `initiate_x402_request` with method `GET`, resource `https://presign-guard.fizzl.eu/v1/token?chain=<chain>&address=<token>` and `maxPayment` `0.01` USDC; show the approval URL; after the user approves, poll `get_request_status`, then `complete_x402_request(requestId)` and parse the JSON.
4. Apply the verdict (see `## Submission`): `green` → proceed; `orange` → show `one_liner` and the reasons and ask the user; `red` → do not buy, explain why.

### Before `send_calls` (calldata from any plugin)

1. Get the wallet with `get_wallets` and the calls the other plugin prepared (`{ to, value, data }` per call).
2. For each call that moves value or grants access (approve, permit, transfer, swap router call), build a `POST /v1/check` body: `type: "transaction"` with `chainId`, `from` (the wallet from `get_wallets`, so the call is simulated), `to`, `data`, `value`, and `intent` (what the user asked for, in one sentence); for a plain ERC-20 `approve` you may send `type: "approval"` instead.
3. Pay and run it via `initiate_x402_request` (method `POST`, resource `https://presign-guard.fizzl.eu/v1/check`, the JSON body, `maxPayment` `0.01`) → approval → `complete_x402_request`.
4. Only submit the batch with `send_calls` if every call is `green`, or the user explicitly accepted each `orange` reason. Never submit when any call is `red`.

### Periodic wallet hygiene

1. `get_wallets` for the address, then the paid `GET /v1/approvals?chain=<chain>&address=<wallet>`.
2. Show `one_liner` and the approvals to revoke. Revoking is a separate `send_calls` the user starts (an `approve(spender, 0)` per token).

## Submission

`none` for transactions: this plugin never submits a transaction itself. It decides whether the user's next `swap` or `send_calls` should go ahead:

| Verdict | Action |
| - | - |
| `green` | Proceed with the user's `swap` / `send_calls` as planned. |
| `orange` | Show the reasons (or `one_liner`) and ask the user before submitting. Do not submit silently. |
| `red` | Do not submit. Explain the reason codes. Only the user can override, explicitly, after seeing them. |

Paid checks are paid with Wallet MCP `initiate_x402_request` / `complete_x402_request` (follow [../references/approval-mode.md](../references/approval-mode.md) for the approval URL and polling). Use the `chain` strings above directly for `GET` routes; map them to a numeric `chainId` for `POST /v1/check`: `base` 8453, `ethereum` 1, `arbitrum` 42161, `optimism` 10, `polygon` 137, `bsc` 56.

## Example Prompts

**"Is this Base token safe to buy? 0x4ed4e862860bed51a9570b96d89af5e1b0efefed"**

1. `GET /v1/token/quick?chain=base&address=0x4ed4…efed` (free).
2. Report the verdict and grade. If not `green`, offer the paid check for the reasons (`## Orchestration` → before buying).

**"Buy $20 of the newest Bankr launch, but check it first"**

1. Read the launch feed via the Bankr plugin; take the token address.
2. Free quick check; on anything but `green`, run the paid `GET /v1/token` through `initiate_x402_request`.
3. `green` → Wallet MCP `swap`; `orange` → show the reasons and ask; `red` → stop and explain.

**"Check these calls before you send them"** (after another plugin prepared calldata)

1. One paid `POST /v1/check` per value-moving call (`type: "transaction"`, with `from` and `intent`).
2. Show what the `simulation` says leaves and arrives in the wallet.
3. Submit with `send_calls` only if all are `green` or the user accepted each `orange`.

**"Do I have risky approvals on my Base wallet?"**

1. `get_wallets`, then paid `GET /v1/approvals?chain=base&address=<wallet>`.
2. List what to revoke; offer to prepare the revoke `send_calls`.

## Notes

* Prices: `/v1/token` and `/v1/check` $0.01, `/v1/check/explain` $0.03, `/v1/approvals` $0.02, USDC via x402. Always pay exactly what the `402` quotes; never hardcode `payTo` or the amount.
* Every paid answer carries a signed `receipt` (EIP-191, bound to the request) that proves later which verdict was delivered.
* The same checks are available as an MCP server (`https://presign-guard.fizzl.eu/mcp`, registry name `io.github.Fizzl13/presign-guard`) with free tools `presign_quick_check` and `token_quick_verdict`; this plugin uses the HTTP API so it works with Wallet MCP's x402 tools without a second MCP.
* presign-guard also checks Solana tokens and XRP Ledger transactions; those chains are outside Wallet MCP and not covered by this plugin.
* A verdict is a risk signal, not a guarantee: `green` means no known red flags, not that a token will keep its value.
* Machine-readable description: `https://presign-guard.fizzl.eu/openapi.json`.
