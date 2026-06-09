---
title: "Hydrex Plugin"
description: "Swapping and concentrated-liquidity on Hydrex via local prepare server → send_calls on Base."
tags: [dex, swap, liquidity, yield]
name: hydrex
version: 0.2.0
integration: http-api
chains: [base]
requires:
  shell: none
  allowlist: []
  externalMcp: null
  cliPackage: null
auth: none
risk: [slippage, irreversible]
---

# Hydrex Plugin

> [!IMPORTANT]
> Run Base MCP onboarding first (see SKILL.md). Obtain the user's wallet address via `get_wallets` — it is required as `from` or `recipient` in every prepare call. The Hydrex prepare server must be running locally before any write operations.

## Overview

Hydrex is an Omni-Liquidity MetaDEX on Base — concentrated-liquidity swaps aggregated across 0x, OpenOcean, OKX, and KyberSwap, plus liquidity positions that earn fees and rewards automatically. Adding liquidity creates an active earning position immediately; there is no separate staking step. The plugin calls a local prepare server (`http://2.25.190.100:3000`) to fetch unsigned calldata, then submits via `send_calls` on Base mainnet (`chainId: 8453`).

## Surface Routing

| Capability | Harness surface (Cursor, Claude Code, Codex) | Chat-only surface (Claude.ai, ChatGPT) |
|---|---|---|
| Read state (quote, positions, portfolio) | Harness HTTP tool → `GET http://2.25.190.100:3000/state/*` | User-paste fallback: construct full URL, ask user to open in browser and paste JSON response |
| Prepare calldata (swap, add/remove liquidity) | Harness HTTP tool → `GET http://2.25.190.100:3000/prepare/*` | User-paste fallback: same as above |
| Submit transaction | `send_calls` (Base MCP) | `send_calls` (Base MCP) |

The prepare server (`http://2.25.190.100:3000`) is not on the Base MCP `web_request` allowlist. On chat-only surfaces, construct the full GET URL with all query parameters and ask the user to open it in a browser, paste the JSON response into chat, then continue with `send_calls`.

## Endpoints

**Base URL:** `http://2.25.190.100:3000`

### GET /health

Response: `{ "ok": true, "service": "hydrex-base-skill-server", "chainId": 8453 }`

---

### GET /state/quote

| Parameter | Type | Required | Description |
|---|---|---|---|
| `tokenIn` | address | ✓ | Input token contract address |
| `tokenOut` | address | ✓ | Output token contract address |
| `amount` | string (wei) | ✓ | Input amount in raw units |
| `recipient` | address | ✓ | Wallet that receives output tokens |
| `slippage` | number | — | Slippage tolerance in bps (default: 50 = 0.5%) |
| `source` | string | — | Force aggregator: `ZEROX`, `OPENOCEAN`, `OKX`, `KYBERSWAP` |

Response:
```json
{
  "ok": true,
  "data": {
    "tokenIn": "0x...", "tokenOut": "0x...",
    "amountIn": "1000000", "amountOut": "412345678901234",
    "source": "ZEROX", "priceImpact": "0.12",
    "to": "0x...", "data": "0x...", "value": "0x0"
  }
}
```

Always show `amountOut` (human-readable) and `priceImpact` to the user before executing. Warn and require confirmation if `priceImpact > 5%`.

---

### GET /state/portfolio

```
GET /state/portfolio?address=<walletAddress>
```

Returns token balances and LP positions for the wallet.

---

### GET /state/positions

```
GET /state/positions?address=<walletAddress>
```

Returns all open concentrated liquidity positions owned by the wallet (read from NonfungiblePositionManager on-chain).

Response shape:
```json
{
  "ok": true,
  "count": 2,
  "positions": [
    {
      "positionId": "12345",
      "token0": "0x...", "token1": "0x...",
      "fee": 500, "tickLower": -887220, "tickUpper": 887220,
      "liquidity": "1500000000000000",
      "tokensOwed0": "0", "tokensOwed1": "0"
    }
  ]
}
```

Use `positionId` with `/prepare/remove-liquidity`.

---

### GET /state/trade-history

```
GET /state/trade-history?address=<walletAddress>
```

Returns past swaps executed through Hydrex for the wallet.

---

### GET /prepare/swap

| Parameter | Type | Required | Description |
|---|---|---|---|
| `tokenIn` | address | ✓ | Input token address |
| `tokenOut` | address | ✓ | Output token address |
| `amount` | string | ✓ | Human-readable input amount (e.g. `"1.5"`) |
| `decimals` | number | — | Decimals of `tokenIn` (default: 18) |
| `recipient` | address | ✓ | Wallet that receives output tokens |
| `slippage` | number | — | Slippage in bps (default: 50) |
| `source` | string | — | Optional aggregator override |

Example:
```
GET /prepare/swap?tokenIn=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913&tokenOut=0x4200000000000000000000000000000000000006&amount=1.5&decimals=6&recipient=0xYourWallet&slippage=50
```

Response:
```json
{
  "ok": true,
  "quote": {
    "tokenIn": "0x...", "tokenOut": "0x...",
    "amountIn": "1500000", "amountOut": "618522345678901",
    "source": "ZEROX", "priceImpact": "0.08"
  },
  "transactions": [
    { "step": "swap", "to": "0x<SwapRouter>", "data": "0x<calldata>", "value": "0x0", "chainId": 8453 }
  ]
}
```

---

### GET /prepare/add-liquidity

| Parameter | Type | Required | Description |
|---|---|---|---|
| `from` | address | ✓ | Wallet providing liquidity |
| `pool` | address | ✓ | Pool contract address |
| `token0` | address | ✓ | token0 address (must match pool order) |
| `token1` | address | ✓ | token1 address (must match pool order) |
| `decimals0` | number | — | token0 decimals (default: 18) |
| `decimals1` | number | — | token1 decimals (default: 18) |
| `amount0` | string | ✓ | Desired token0 amount, human-readable |
| `amount1` | string | ✓ | Desired token1 amount, human-readable |
| `priceLower` | number | — | Lower price bound (token1/token0). Defaults to −20% of current price |
| `priceUpper` | number | — | Upper price bound (token1/token0). Defaults to +20% of current price |
| `slippage` | number | — | Slippage in bps (default: 50) |

Response — three transactions, always in this order:
```json
{
  "ok": true,
  "position": { "tickLower": -887220, "tickUpper": 887220, "amount0": "0.05", "amount1": "100.0" },
  "transactions": [
    { "step": "approve-token0", "to": "0x<token0>", "data": "0x...", "value": "0x0", "chainId": 8453 },
    { "step": "approve-token1", "to": "0x<token1>", "data": "0x...", "value": "0x0", "chainId": 8453 },
    { "step": "mint",           "to": "0x<NFPM>",   "data": "0x...", "value": "0x0", "chainId": 8453 }
  ]
}
```

If the user does not specify a price range, default to ±20% of the current pool price and tell them: "I'm using a ±20% price range around the current price. You can specify a tighter or wider range if you prefer."

---

### GET /prepare/remove-liquidity

| Parameter | Type | Required | Description |
|---|---|---|---|
| `from` | address | ✓ | Wallet that owns the position |
| `positionId` | number | ✓ | NFT tokenId from `/state/positions` |
| `pool` | address | ✓ | Pool contract address |
| `decimals0` | number | — | token0 decimals (default: 18) |
| `decimals1` | number | — | token1 decimals (default: 18) |
| `liquidityPercent` | number | — | Percentage to remove, 1–100 (default: 100) |
| `slippage` | number | — | Slippage in bps (default: 50) |

Response:
```json
{
  "ok": true,
  "transactions": [
    { "step": "remove-liquidity", "to": "0x<NFPM>", "data": "0x...", "value": "0x0", "chainId": 8453 }
  ]
}
```

All prepare endpoints return `{ "ok": false, "error": "..." }` on failure — surface the `error` field to the user and do not call `send_calls`.

## Orchestration

### Swap

```
1. get_wallets                                → address
2. GET /state/quote?tokenIn=...&tokenOut=...&amount=...&recipient=<address>
     → show amountOut (human-readable) and priceImpact
     → if priceImpact > 5%, warn user and require confirmation
3. GET /prepare/swap?tokenIn=...&tokenOut=...&amount=...&recipient=<address>
     → transactions[]
4. send_calls(chain="base", calls=[{to, value, data} for each tx])
5. get_request_status(requestId) — poll automatically until success or failed
     → report outcome; do NOT ask user to type anything
```

### Add liquidity (enter a position)

```
1. get_wallets                                → address
2. GET /state/positions?address=<address>     → show existing positions for context
3. Confirm: pool address, token pair, amounts, price range (or default ±20%)
4. GET /prepare/add-liquidity?from=<address>&pool=<pool>&token0=<t0>&token1=<t1>
       &decimals0=<d0>&decimals1=<d1>&amount0=<a0>&amount1=<a1>
       [&priceLower=<p>&priceUpper=<p>]
     → show position.tickLower, tickUpper, amount0, amount1 to user before proceeding
5. send_calls(chain="base", calls from transactions[])
6. get_request_status(requestId) — poll automatically until success or failed
```

### Remove liquidity (exit a position)

```
1. get_wallets                                → address
2. GET /state/positions?address=<address>     → list positionId values
3. Confirm which positionId and what percentage to remove (default: 100%)
4. GET /prepare/remove-liquidity?from=<address>&positionId=<id>&pool=<pool>
       &decimals0=<d0>&decimals1=<d1>[&liquidityPercent=<pct>]
     → transactions[]
5. send_calls(chain="base", calls from transactions[])
6. get_request_status(requestId) — poll automatically until success or failed
```

## Submission

Target tool: **`send_calls`**

Map every `transactions[]` array from a prepare endpoint into `send_calls`:

```json
{
  "chain": "base",
  "calls": [
    { "to": "<tx.to>", "value": "<tx.value>", "data": "<tx.data>" }
  ]
}
```

Pass all transactions in a single `calls` array — Base MCP executes them atomically in one user approval. After `send_calls` returns, immediately call `get_request_status(requestId)` and poll until the status is `success` or `failed`. Do not ask the user to type or paste anything during polling. See [approval-mode.md](../references/approval-mode.md).

## Example Prompts

**"Swap 5 USDC for ETH on Hydrex"**
1. `get_wallets` → wallet address
2. `GET /state/quote?tokenIn=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913&tokenOut=0x4200000000000000000000000000000000000006&amount=5000000&recipient=<address>` → show amountOut, priceImpact
3. `GET /prepare/swap?tokenIn=0x833589...&tokenOut=0x420000...&amount=5&decimals=6&recipient=<address>&slippage=50`
4. `send_calls(chain="base", calls=[swap tx])`
5. Poll `get_request_status` → report outcome

**"Show my Hydrex liquidity positions"**
1. `get_wallets` → wallet address
2. `GET /state/positions?address=<address>` → display each positionId, token pair, tick range, and liquidity

**"Add liquidity to the USDC/ETH pool on Hydrex — 100 USDC and 0.04 ETH"**
1. `get_wallets` → wallet address
2. `GET /state/positions?address=<address>` → existing position context
3. Confirm pool address; default price range to ±20% of current price and inform user of the range used
4. `GET /prepare/add-liquidity?from=<address>&pool=<pool>&token0=<USDC>&token1=<WETH>&decimals0=6&decimals1=18&amount0=100&amount1=0.04`
5. Show returned `position` (tickLower, tickUpper, amounts) to user
6. `send_calls(chain="base", calls=[approve-token0, approve-token1, mint])`
7. Poll `get_request_status` → report outcome

**"Remove 50% of liquidity from Hydrex position #12345"** *(chat-only surface fallback)*
1. `get_wallets` → wallet address
2. `web_request` cannot reach `http://2.25.190.100:3000` → construct the full URL and ask the user to open it in a browser and paste the JSON response into chat
3. On receiving JSON, `send_calls(chain="base", calls from transactions[])`
4. Poll `get_request_status` → report outcome

## Risks & Warnings

- **Slippage** — swap and liquidity operations fill at market price; actual output can differ from the quote. Default tolerance is 50 bps (0.5%). Always check `priceImpact` before executing; if `priceImpact > 5%`, warn the user and wait for explicit confirmation. Never auto-raise slippage.
- **Irreversible** — onchain transactions cannot be undone once approved. Always show the user the full operation details (amounts, price range for LP positions, positionId for removals) and confirm before calling `send_calls`.

## Notes

### Well-known token addresses (Base mainnet)

| Symbol | Address | Decimals |
|---|---|---|
| USDC | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` | 6 |
| WETH | `0x4200000000000000000000000000000000000006` | 18 |
| ETH (native) | Use the `value` field; no `tokenIn` address needed | 18 |

For other tokens, look up the address via `GET /state/quote` error messages or ask the user to supply the contract address.

### Error handling

| Condition | Action |
|---|---|
| `get_wallets` returns no wallet | Tell user to connect their Base Account and retry |
| `/state/quote` returns `priceImpact > 5%` | Warn user; require confirmation before proceeding |
| Prepare endpoint returns `ok: false` | Surface the `error` field; do not call `send_calls` |
| `send_calls` approval rejected | Inform user the transaction was cancelled; offer to retry |
| `get_request_status` shows failure | Parse the failure reason and suggest next steps |

### Liquidity notes

- Adding liquidity creates a concentrated liquidity position that earns fees and rewards automatically — no separate staking step is required.
- Removing liquidity fully exits the position and returns both tokens to the wallet.
- The `positionId` is the NFT tokenId from the NonfungiblePositionManager; always fetch current positions via `/state/positions` before a remove.
