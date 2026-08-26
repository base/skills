---
title: "Corvo Edge Plugin"
description: "Token safety checks, live market data and self-custody swap preparation on Corvo Edge via HTTP API to send_calls on Base."
tags: [safety, market-data, swap]
name: corvo
version: 0.1.0
integration: http-api
chains: [base]
requires:
  shell: none
  allowlist: [app.corvoedge.xyz]
  externalMcp: null
  cliPackage: null
auth: none
risk: [slippage]
---

# Corvo Edge Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before calling any Corvo endpoint. The user's wallet address is fetched lazily when needed. Corvo is self-custody: it prepares calldata and checks safety, it can never execute or hold keys.

## Overview

Corvo Edge is a chat-first, self-custody trading terminal on Base. The plugin uses Corvo as a safety oracle and market brain: honeypot and tax checks, tradeability verdicts, a curated token set, live prices and market movers. With a free API key it also builds unsigned swap calldata for the user's own wallet, submitted through Base MCP's `send_calls`. Use Corvo when the user asks whether a token is safe to trade, wants market context before acting, or wants a checked swap prepared end to end.

## Surface Routing

| Capability | Harness surface (Claude Code, Cursor) | Chat-only surface (Claude.ai, ChatGPT) |
|---|---|---|
| GET safety, tokens, prices, pulse | Harness HTTP tool, no allowlist needed | `web_request`, requires `app.corvoedge.xyz` allowlisted |
| GET /api/swap/route (quote) | Harness HTTP tool, no allowlist needed | `web_request`, requires `app.corvoedge.xyz` allowlisted |
| POST /api/swap/build (calldata, key) | Harness HTTP tool, no allowlist needed | Not available (POST unsupported), use the read endpoints and direct the user to app.corvoedge.xyz to execute |
| Submit swap | `send_calls`, all surfaces | `send_calls`, all surfaces |

Where a surface cannot POST, do not improvise a workaround: quote and check with the GET endpoints, then direct the user to `app.corvoedge.xyz` to execute.

## Endpoints

Base URL: `https://app.corvoedge.xyz`

### GET /api/public/token/safety

Honeypot, buy and sell tax, holder count, open source flag and tradeability for any Base token.

```
GET https://app.corvoedge.xyz/api/public/token/safety?address={0xTokenAddress}
```

| Field | Notes |
|---|---|
| `safety.is_honeypot` | `true` is a hard stop |
| `safety.tradeability.can_sell` | `false` is a stop, not a warning |
| `safety.buy_tax_pct`, `safety.sell_tax_pct` | Surface to the user before any trade |

Call this BEFORE preparing any trade on a token the user did not explicitly verify.

### GET /api/public/edge-tokens

The curated tradeable token set with addresses, decimals and chains. USDC has 6 decimals, most tokens 18, B20 stock tokens 8.

### GET /api/public/chains

Supported chains and ids.

### GET /api/public/prices

Live prices for the listed set.

### GET /api/public/pulse

Market pulse, movers and recent launches.

### GET /api/swap/route

Best-route quote for a Base swap. Native ETH is `0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE`.

```
GET https://app.corvoedge.xyz/api/swap/route?tokenIn={address}&tokenOut={address}&amountIn={baseUnits}
```

Returns `data.routeSummary` with `amountOut` and `gas`.

### POST /api/swap/build (API key)

Builds the exact router calldata for the sender. Free key from `app.corvoedge.xyz` via /keys, passed as `Authorization: Bearer <key>`.

```
POST https://app.corvoedge.xyz/api/swap/build
{ "routeSummary": <from route>, "sender": "0x...", "slippageTolerance": 100 }
```

Returns `data.routerAddress` and `data.data`. Clients that can speak MCP can instead call the Corvo MCP server at `https://app.corvoedge.xyz/mcp` (tool `edge_swap_prepare`), which wraps both steps and returns a ready `send_calls` envelope, including a `simulated` eth_simulateV1 preview for ETH-in swaps.

## send_calls mapping

```json
{
  "chainId": 8453,
  "calls": [
    { "to": "<routerAddress>", "value": "<amountIn as hex when tokenIn is ETH, else 0x0>", "data": "<data>" }
  ]
}
```

A token-in swap may need a one-time ERC-20 `approve` to the router as its own call before the swap call. When a `simulated` field is present and reads `revert`, do not send.

## Rules

- Never skip the safety read on an unfamiliar token.
- Never modify returned calldata. Sign it exactly or drop it.
- Amounts are base units, respect per-token decimals from `/api/public/edge-tokens`.
- A 4xx with a reason is the API working. Show the reason to the user.
