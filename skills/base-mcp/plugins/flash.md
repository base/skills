---
title: "Definitive Flash Plugin"
description: "Swaps and advanced orders (limit, TWAP, stop, bracket) on Definitive Flash via HTTP API → send_calls + sign, with gasless MEV-protected execution across 7 chains."
tags: [swap, trading, dex, cross-chain]
name: flash
version: 0.1.0
integration: http-api
chains: [base, ethereum, arbitrum, optimism, polygon, bsc, avalanche]
requires:
  shell: none
  allowlist: [flash.definitive.fi]
  externalMcp: null
  cliPackage: null
auth: api-key
risk: [slippage, irreversible, low-liquidity]
---

# Definitive Flash Plugin

> [!IMPORTANT]
> Run Base MCP onboarding first (see SKILL.md). A development API key is pre-configured — no setup needed to start quoting.

## Overview

Definitive Flash is a trading API that routes swaps across 200+ liquidity sources and supports advanced order types — market, limit, TWAP, stop, stop-loss, take-profit, and bracket — with cross-chain settlement. Execution is intent-based and gasless: the plugin fetches a quote from the Flash HTTP API, submits any pre-trade funding transactions (wrap / ERC-20 approval) as unsigned calldata via `send_calls`, signs the order's EIP-712 payload via `sign`, and POSTs the signature back to Flash, which handles gas, simulation, MEV protection, and onchain landing. Use Flash when the user wants best-rate routing, resting orders (limit/TWAP/triggers), or cross-chain swaps from one API.

## Auth

All requests require an API key in the `x-definitive-api-key` header:

```json
{
  "x-definitive-api-key": "dpka_513a2bd7_57a2_46d2_927b_2a3857fe271b",
  "Content-Type": "application/json"
}
```

The key above is the public development key published in the [Flash docs](https://flash.definitive.fi/docs) — use it unless the user provides their own integrator key. API keys cannot move funds; every order additionally requires the funder wallet's EIP-712 signature. Integrators can obtain a production key (and configure integrator fees) from Definitive via the docs site.

## Surface Routing

| Capability                                 | Surface                                        | Execution Path                                                                                                                                                                                           |
| ------------------------------------------ | ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Asset search, balances, order status (GET) | Harness with HTTP (Claude Code, Cursor, Codex) | Harness HTTP tool → `flash.definitive.fi`                                                                                                                                                                |
| Asset search, balances, order status (GET) | Chat-only (Claude.ai, ChatGPT)                 | `web_request` (host must be allowlisted); else user-paste GET fallback                                                                                                                                   |
| Quote + submit order (POST)                | Harness with HTTP                              | Harness HTTP tool → POST `flash.definitive.fi`                                                                                                                                                           |
| Quote + submit order (POST)                | Chat-only                                      | `web_request` → POST (host must be allowlisted). If not allowlisted, inform the user that trading requires a harness with HTTP tools (e.g. Claude Code) and stop — there is no POST user-paste fallback. |
| Wrap / approval funding txs                | Any                                            | `send_calls` with unsigned calldata from the quote                                                                                                                                                       |
| Order + Permit2 signatures                 | Any                                            | `sign` (`eth_signTypedData_v4`)                                                                                                                                                                          |
| Cancel / update signatures                 | Any                                            | `sign` (`personal_sign`)                                                                                                                                                                                 |

See [custom-plugins.md](../references/custom-plugins.md) for the full HTTP routing decision tree.

## Endpoints

Base URL: `https://flash.definitive.fi/v1` · OpenAPI spec: `https://flash.definitive.fi/v1/openapi.json`

Chains: `base` · `ethereum` · `arbitrum` · `optimism` · `polygon` · `bsc` · `avalanche` (the API also supports `solana`, `hyperevm`, `plasma`, `monad`, `robinhood`, which Base MCP does not — see `## Notes`).

### GET /search

Resolve a token symbol, name, or contract address to a tradable asset.

```
GET /search?query={symbol|name|address}&chain={chain}&limit={n}
```

Returns `assets[]` with `chain`, `address`, `symbol`, `name`, `decimals`, `price` (USD), `marketCap`, `liquidity`, `volume24h`, and `riskFlagged`. Pass `address` straight back to `POST /quote` as `targetAsset` / `contraAsset`. EVM native assets use the sentinel `0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE`. If `riskFlagged` is `true`, warn the user before trading (see [Risks & Warnings](#risks--warnings)). A `price` of `"0"` means unknown, not zero.

### GET /balances/{address}

Native + token balances for a wallet across supported chains. Returns entries with `chain`, `address`, `symbol`, `balance`, `notional` (USD), and `isNative`. Read-only — useful before quoting a sell.

### POST /quote

Prices a trade and returns the signing/funding payloads needed to execute it.

**Request** (market swap shown; see `## Notes` for advanced order fields):

```json
{
  "targetChain": "base",
  "contraChain": "base",
  "targetAsset": "0x4200000000000000000000000000000000000006",
  "contraAsset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  "side": "buy",
  "qty": "100",
  "orderType": "market",
  "maxSlippage": 0.01,
  "funderAddress": "<wallet address>"
}
```

| Parameter                     | Required    | Notes                                                                                                                                                                                      |
| ----------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `targetChain` / `contraChain` | ✅          | Chain of the traded / counter asset. Differ for a cross-chain order (then `recipientAddress` is required at submit).                                                                       |
| `targetAsset` / `contraAsset` | ✅          | Asset addresses. `contraAsset` is spent on buys, received on sells.                                                                                                                        |
| `side`                        | ✅          | `"buy"` or `"sell"` (of `targetAsset`).                                                                                                                                                    |
| `qty`                         | ✅          | Amount **spent**, as a decimal string in the asset's **normalized (human) units** — not wei. Buys: `contraAsset` units; sells: `targetAsset` units.                                        |
| `orderType`                   | ✅          | `market` · `limit` · `twap` · `stop` · `stop-loss` · `take-profit` · `bracket`                                                                                                             |
| `maxSlippage`                 | recommended | **Decimal, not bps** — `0.01` = 1%. Defaults to `0.05` (5%). See [Risks & Warnings](#risks--warnings).                                                                                     |
| `maxPriceImpact`              | optional    | Decimal. Defaults to `0.05`.                                                                                                                                                               |
| `funderAddress`               | recommended | The wallet that funds the trade. Always pass it when quoting for execution — the funding payloads (`approveTx`, wrap) depend on its live allowances/balances. Omit for a price-only quote. |

**Response** (fields relevant to execution):

```json
{
  "quoteId": "q_abc123",
  "from": { "asset": "contra", "amount": "100", "notional": "100" },
  "to": { "asset": "target", "amount": "0.0527", "notional": "99.91" },
  "fees": { "estimatedFeeNotional": "0.29" },
  "estimatedPriceImpact": "0.0042",
  "wrap": {
    "evmTx": { "to": "0x…", "data": "0x…", "value": "<base-units decimal>" }
  },
  "evm": {
    "approveTx": { "to": "0x…", "data": "0x…" },
    "permitTypedData": "<JSON string | null>",
    "orderTypedData": "<JSON string>"
  }
}
```

- `from` / `to` are the spent and received (net, post-fee) legs; their `asset` field is the label `"target"` or `"contra"`, not an address.
- `wrap` is non-null only when spending the native gas asset: `wrap.evmTx` is a `deposit()` call on the wrapped-native contract that must land **before** submit.
- `evm.approveTx` is ERC-20 approve calldata (spender is Permit2 or the Definitive Flash allowance contract, chosen by the server). `null` when the allowance is already sufficient.
- `evm.permitTypedData` / `evm.orderTypedData` are **JSON-serialized** EIP-712 payloads — parse before signing, echo back verbatim at submit.
- Cross-chain quotes also return `bridgeQuoteId` — echo it at submit.

### POST /order

Submits the signed quote for MEV-protected execution.

```json
{
  "targetChain": "base",
  "contraChain": "base",
  "targetAsset": "0x…",
  "contraAsset": "0x…",
  "side": "buy",
  "qty": "100",
  "orderType": "market",
  "maxSlippage": 0.01,
  "funderAddress": "<wallet address>",
  "quoteId": "q_abc123",
  "userSignature": "0x<signature over evm.orderTypedData>",
  "evmOrderTypedData": "<echo of evm.orderTypedData>",
  "evmPermitTypedData": "<echo of evm.permitTypedData — only if it was non-null>",
  "evmPermitSignature": "0x<signature over evm.permitTypedData — only if it was non-null>"
}
```

Echo the same trade parameters used at quote time. `quoteId` executes the cached quote for marketable orders (skip re-pricing); for resting orders (limit/twap/triggers) it is unnecessary. TWAP orders must echo `twapBucketCount`/`startTime`; trigger orders must echo `triggers` exactly as quoted. Response: `{ "orderId": "…" }`.

### Order management (GET / PATCH / POST)

```
GET   /orders?funderAddress={address}&statuses={…}&pageSize={n}&pageToken={…}   → { orders, nextPageToken }
GET   /orders/{orderId}                                                          → status + execution fills
PATCH /orders/{orderId}                                                          → update a resting order's limit price (signature required)
POST  /orders/{orderId}/cancel                                                   → cancel a resting order (signature required)
```

Order statuses: `PENDING`, `ACCEPTED`, `PARTIALLY_FILLED`, `FILLED`, `CANCELLED`, `REJECTED`, `TERMINATED` (prefixed `ORDER_STATUS_`).

**Cancel** requires the funder to sign a canonical plaintext message with EIP-191 `personal_sign` (via Base MCP `sign`), echoed back with the signature:

```json
{
  "cancelMessage": "Definitive Flash v1 — Cancel Order\nOrder: <orderId>",
  "userSignature": "0x<personal_sign signature over cancelMessage>"
}
```

Cancel is idempotent — cancelling an already-cancelled order returns 200.

**Update** works the same way with its own message format (order id, an RFC3339 `Issued At:` freshness stamp, and the new limit value, which must match the request field exactly):

```json
{
  "limitNotionalPrice": "3000",
  "updateMessage": "Definitive Flash — Update Order\nOrder: <orderId>\nIssued At: <RFC3339 UTC now>\nLimit Notional Price: 3000",
  "userSignature": "0x<personal_sign signature over updateMessage>"
}
```

Set exactly one of `limitNotionalPrice` / `limitCrossPrice` (the message line is `Limit Notional Price:` or `Limit Cross Price:` accordingly). `422` means the order type does not accept limit updates or the order is in a terminal state.

## Orchestration

### Market swap (EVM)

1. `get_wallets` → funder wallet address.
2. Resolve assets: check `## Notes` for common addresses, else `GET /search`. Warn on `riskFlagged` assets.
3. `POST /quote` with `funderAddress`. Show the user: receive amount (`to.amount` / `to.notional`), total fee (`fees.estimatedFeeNotional`), and `estimatedPriceImpact`. **Confirm before proceeding.**
4. **Funding transactions** — only if the quote returned them: batch `wrap.evmTx` (first) and `evm.approveTx` into one `send_calls` (see [Submission](#submission)) → present the approval URL → after the user approves, poll `get_request_status` until confirmed. These must land onchain **before** submitting the order.
5. If `evm.permitTypedData` is non-null: JSON-parse it and sign via `sign` (`eth_signTypedData_v4`) → `evmPermitSignature`.
6. JSON-parse `evm.orderTypedData` and sign via `sign` (`eth_signTypedData_v4`) → `userSignature`. This signature authorizes the spend — re-show the trade summary if any time has passed.
7. `POST /order` echoing the quote parameters + `quoteId` + typed-data echoes + signatures → `orderId`.
8. Poll `GET /orders/{orderId}` until `FILLED` (or `REJECTED`/`TERMINATED` — report the error; do not blindly retry). A submit timeout does **not** mean failure — check order status before re-submitting.

### Limit / stop / take-profit / TWAP orders

Same flow as the market swap with these differences at quote time:

- **Limit**: `orderType: "limit"` + `limitNotionalPrice` (USD price of `targetAsset`) or `limitCrossPrice` (pair rate). Optional `expireTime` (ISO-8601; omit = good-til-cancelled).
- **Stop / stop-loss / take-profit**: `orderType` accordingly + `triggers` (each with exactly one of `notionalPrice` or `crossPrice`).
- **TWAP**: `orderType: "twap"` + `durationSeconds` (≥ 300); optional `startTime`, `twapBucketCount`.

The order rests with Flash after submit — funding (allowance) must remain in place until it fills. Manage via `GET /orders`, `PATCH /orders/{orderId}` (limit-price change), and `POST /orders/{orderId}/cancel` — cancel and update each require a `personal_sign` signature over their canonical message (see [Endpoints](#endpoints)): build the message, sign it via Base MCP `sign`, and POST message + signature.

### Cross-chain swap

Quote with different `targetChain` / `contraChain`; submit additionally requires `recipientAddress` (destination-chain receiver — default to the funder's own address unless the user names another) and must echo `bridgeQuoteId` when the quote returned one.

### Reads (no wallet interaction)

- "What's the price of X?" → `POST /quote` without `funderAddress`; report pricing only.
- "What do I hold?" → `get_wallets` → `GET /balances/{address}`.
- "My open orders?" → `GET /orders?funderAddress=…`.

## Submission

**Target tools:** `send_calls` (funding transactions only) + `sign` (EIP-712 order/permit payloads; `personal_sign` for cancel/update messages). The trade itself is **not** submitted through Base MCP — after signing, it is POSTed to `/order` and Flash broadcasts it gaslessly with MEV protection.

**Funding batch** — map the quote's funding payloads into one `send_calls`, wrap before approve:

```json
{
  "chain": "<targetChain/contraChain of the spent asset>",
  "calls": [
    {
      "to": "<wrap.evmTx.to>",
      "value": "<hex(wrap.evmTx.value)>",
      "data": "<wrap.evmTx.data>"
    },
    {
      "to": "<evm.approveTx.to>",
      "value": "0x0",
      "data": "<evm.approveTx.data>"
    }
  ]
}
```

- Include each call only if the quote returned it; skip `send_calls` entirely when both are absent (already funded).
- `wrap.evmTx.value` is a **decimal base-units string** — hex-encode it: `"0x" + BigInt(value).toString(16)`. `approveTx` has no value → `"0x0"`.
- Use Base MCP chain name strings, not numeric IDs. Follow the approval/polling flow in [approval-mode.md](../references/approval-mode.md); the funding batch must be confirmed onchain before `POST /order`.

**Signatures** — `evm.permitTypedData` / `evm.orderTypedData` are JSON strings. Parse and pass to `sign` as `eth_signTypedData_v4`. Two known quirks (see `## Notes`): `domain.chainId` is serialized as a string, and `types` includes an `EIP712Domain` entry — some signers need the chainId coerced to a number and the `EIP712Domain` entry stripped. Echo the **original unmodified strings** back to `/order`; the signature, not the echo, is what was normalized.

If `sign` does not support `eth_signTypedData_v4` on the current surface, stop and tell the user the order cannot be signed there — do not improvise.

## Example Prompts

**"Swap 100 USDC to ETH on Base"**

1. `get_wallets` → address.
2. `POST /quote` — `targetChain/contraChain: "base"`, `targetAsset: 0xEeee…EEeE` (native ETH), `contraAsset: 0x8335…2913` (USDC), `side: "buy"`, `qty: "100"`, `orderType: "market"`, `funderAddress`.
3. Show receive amount, fee, price impact → user confirms.
4. `send_calls("base", [approveTx])` if returned → user approves → confirmed.
5. `sign` permit typed data (if present), then order typed data.
6. `POST /order` with `quoteId`, echoes, signatures → poll `GET /orders/{orderId}` → report fill.

**"Buy 0.05 WETH with USDC when ETH drops to $3,000"**

1. `get_wallets` → address.
2. `POST /quote` — `orderType: "limit"`, `side: "buy"`, `qty: "<USDC to spend>"`, `limitNotionalPrice: "3000"`, `funderAddress`.
3. Confirm resting-order terms → fund (approve) via `send_calls` if needed → `sign` order typed data → `POST /order`.
4. Report the `orderId` and that it rests until the limit price is reached; offer `GET /orders/{orderId}` to check later.

**"TWAP 1 ETH into USDC over the next hour on Base"**

1. `get_wallets` → address.
2. `POST /quote` — `orderType: "twap"`, `side: "sell"`, `qty: "1"`, `durationSeconds: 3600`, `funderAddress`. Native ETH input → quote returns `wrap.evmTx`.
3. Confirm → `send_calls("base", [wrap, approve])` → confirmed → `sign` → `POST /order` (echo `twapBucketCount`/`startTime` from the quote).
4. Report `orderId`; fills accrue over the hour — check with `GET /orders/{orderId}`.

**"Cancel my open Flash orders"** _(management)_

1. `get_wallets` → address.
2. `GET /orders?funderAddress=…` filtered to open statuses → list them.
3. For each order the user confirms: build `"Definitive Flash v1 — Cancel Order\nOrder: <orderId>"`, sign it via `sign` (`personal_sign`), then `POST /orders/{orderId}/cancel` with `cancelMessage` + `userSignature`.

## Risks & Warnings

- **Slippage** — `maxSlippage` is a **decimal fraction** (`0.05` = 5%), and the API default is a permissive 5%. Prefer passing an explicit `0.005`–`0.01` for liquid pairs. Warn and require confirmation above `0.05`; strongly warn above `0.20` and re-confirm the exact number. Never silently raise slippage after a failed fill.
- **Irreversible** — the EIP-712 order signature authorizes spending real funds, and onchain fills cannot be undone. Always show a fresh quote (receive amount, fees, price impact) and get explicit confirmation in-conversation before signing `orderTypedData`. Resting orders (limit/TWAP/triggers) execute **later, unattended** — make sure the user understands what they are authorizing. Submit one order at a time; never parallelize submits for the same wallet.
- **Low liquidity** — `/search` flags risky assets via `riskFlagged` (thin liquidity, concentrated supply, mint/freeze authority). Surface the flag and the asset's `liquidity`/`volume24h` before trading it; treat the flag as a caution signal, not a guarantee either way. `estimatedPriceImpact` can exceed the quote's estimate at fill time.

## Notes

- **Native asset sentinel (EVM):** `0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE`. Spending native requires the quote's `wrap.evmTx` first; the trade itself is priced against the wrapped token.
- **`qty` is human units** (decimal string), not wei — `"100"` means 100 USDC. Direction: the amount **spent** (`contraAsset` on buys, `targetAsset` on sells).
- **Typed-data quirks:** `permitTypedData`/`orderTypedData` are JSON strings. `domain.chainId` arrives as a string — coerce to a number for signers that drop non-numeric chainIds from the domain hash (a silently-wrong signature otherwise). Strip the `EIP712Domain` key from `types` for libraries (e.g. viem) that reject it. Echo the original strings, unmodified, at submit.
- **Smart-account wallets:** signatures are accepted as raw hex without a length gate, and the backend unwraps ERC-6492-wrapped Permit2 signatures, so smart-account (ERC-1271/6492) wallets are supported on the trade path. Cancel/update verification is documented as a 65-byte EIP-191 signature — if a cancel or update returns a signature error on a smart-account wallet, report it to the user and suggest managing the order via `GET /orders` + Definitive support rather than retrying.
- **Solana and other chains:** the API also supports `solana`, `hyperevm`, `plasma`, `monad`, and `robinhood`. Base MCP wallets cannot sign for these — if the user asks, point them to Definitive's own tooling (the `@definitive-fi/flash-mcp` server) instead.
- **Attribution:** `POST /order` accepts `erc8021AttributionCode` — an ERC-8021 builder code registered on base.dev, appended to EVM settlement calldata. Optional; an unregistered code never fails the order.
- **Quote reuse:** for marketable orders, passing `quoteId` executes the cached quote. If submit rejects a stale quote, re-quote, re-confirm with the user, and re-sign — never reuse an old signature with new parameters.
- **Common Base addresses:** USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` · WETH `0x4200000000000000000000000000000000000006` · cbBTC `0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf`.
- **Statuses:** `ORDER_STATUS_{PENDING|ACCEPTED|PARTIALLY_FILLED|FILLED|CANCELLED|REJECTED|TERMINATED}`. `ACCEPTED` on a resting order means it is working, not filled.
