---
title: "o1.exchange Plugin"
description: "Token trading on o1.exchange via HTTP API → send_calls on Base, Solana, and BSC."
tags: [trading, swap, dex]
name: o1-exchange
version: 0.2.0
integration: http-api
chains: [base, solana, bsc]
requires:
  shell: none
  allowlist: [api.o1.exchange]
  externalMcp: null
  cliPackage: null
auth: api-key
risk: [slippage, irreversible]
---

# o1.exchange Plugin

> [!IMPORTANT]
> Run Base MCP onboarding first (see SKILL.md). Authenticate once per session — see `## Auth`.

## Overview

o1.exchange is a trading API for token swaps with built-in MEV protection and optional Permit2 gasless approvals. The plugin calls the o1.exchange HTTP API to build unsigned transaction calldata, then submits via `send_calls`. Authentication requires a Bearer token generated at the o1.exchange dashboard.

## Auth

All requests require a Bearer token in the `Authorization` header:

```json
{
  "Authorization": "Bearer <USER_API_TOKEN>",
  "Content-Type": "application/json"
}
```

Ask the user for their o1.exchange API token if not already provided. Tokens are generated at https://o1.exchange/api-trading. Include both headers on every request to `api.o1.exchange`.

## Surface Routing

| Capability | Surface | Execution Path |
|---|---|---|
| Build swap tx | Harness with HTTP (Claude Code, Cursor, Codex) | Harness HTTP tool → POST api.o1.exchange |
| Build swap tx | Chat-only (Claude.ai, ChatGPT) | `web_request` → POST api.o1.exchange (host must be allowlisted) |
| Build swap tx | Chat-only, not allowlisted | Inform user that `api.o1.exchange` must be added to the `web_request` allowlist; stop |
| Submit tx | Any | `send_calls` with unsigned calldata from API response |

See [custom-plugins.md](../references/custom-plugins.md) for the full HTTP routing decision tree.

## Endpoints

Base URL: `https://api.o1.exchange/api/v2`

### POST /order

Builds unsigned transaction(s) for a token swap.

**Request:**

```json
{
  "networkId": 8453,
  "signerAddress": "<wallet address>",
  "tokenAddress": "<token contract address>",
  "uiAmount": "100",
  "direction": "buy",
  "slippageBps": 300,
  "mevProtection": true
}
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `networkId` | number | Yes | `8453` (Base), `1399811149` (Solana) | or `56` (BSC) |
| `signerAddress` | string | Yes | User's wallet address (`0x…`) |
| `tokenAddress` | string | Yes | Token contract address to trade |
| `uiAmount` | string | Yes | Human-readable amount (e.g. `"100"`, `"0.5"`) |
| `direction` | string | Yes | `"buy"` or `"sell"` |
| `slippageBps` | number | Yes | Slippage tolerance in basis points (100 bps = 1%) |
| `mevProtection` | boolean | Yes | Enable MEV protection via private mempool routing |
| `quoteTokenAddress` | string | No | Stablecoin to quote against (Base only) |
| `poolAddress` | string | No | Specific liquidity pool address (Base, BSC) |

**Response:**

```json
{
  "success": true,
  "id": "<batch-id>",
  "transactions": [
    {
      "id": "<tx-id>",
      "unsigned": {
        "to": "0x…",
        "data": "0x…",
        "value": "0x…",
        "gasLimit": "0x…",
        "chainId": 8453
      },
      "permit2": {
        "eip712": {
          "domain": { },
          "types": { },
          "values": { }
        }
      }
    }
  ]
}
```

`permit2` is present only when a gasless Permit2 approval is available (Base only). When absent, submit the `unsigned` transaction directly via `send_calls`.

### POST /order/complete

Submits signed transactions to the o1.exchange relay for broadcasting. **Not used in the standard `send_calls` flow** — documented for reference.

**Request:**

```json
{
  "id": "<batch-id from /order>",
  "transactions": [
    {
      "id": "<tx-id>",
      "signed": "0x<signed tx hex>",
      "permit2": {
        "eip712": {
          "signature": "0x…"
        }
      }
    }
  ]
}
```

**Response:**

```json
{
  "success": true,
  "transactions": [
    {
      "hash": "0x…",
      "status": "pending",
      "tokenDelta": "…"
    }
  ]
}
```

## Orchestration

### Standard swap (no Permit2)

1. `get_wallets` → wallet address.
2. Ask the user for their o1.exchange API token if not already provided.
3. Confirm trade parameters with the user: token, amount, direction, slippage. See [Risks & Warnings](#risks--warnings) before proceeding with elevated slippage.
4. `web_request` POST `https://api.o1.exchange/api/v2/order` with auth headers and swap parameters.
5. Verify `success: true` in response.
6. Map each `transactions[].unsigned` to `send_calls` calls — keep `to`, `data`, `value`; strip `gasLimit` and `chainId`. Map `networkId` to chain string (`8453` → `"base"`, `56` → `"bsc"`).
7. `send_calls(chain, calls)` → `approvalUrl` + `requestId`.
8. Present the approval URL: [Approve Transaction](approvalUrl). In CLI harnesses, also auto-open the link. Do not approve on the user's behalf.
9. After the user confirms approval, call `get_request_status(requestId)` once.

### Permit2 swap (Base only)

When `transactions[].permit2` is present in the `/order` response:

1. Follow steps 1–5 of the standard swap.
2. For each transaction with `permit2.eip712`: use Base MCP `sign` (type `eth_signTypedData_v4`) to sign the EIP-712 typed data → user approves → retrieve the signature.
3. In `unsigned.data`, replace the placeholder signature (`42f68902113a2a579bcc207c91254c8516d921250e748c18a082d91d74908f8e9a05f27b72a030c6a42d77d0e0aab6fb09219b01a01e7b5b24e4f322ee1762ff1b`) with the actual Permit2 signature returned from `sign`.
4. Map the corrected `unsigned` to `send_calls` calls and continue from step 7 of the standard swap.

If `sign` does not support `eth_signTypedData_v4`, fall back to the standard swap path without Permit2.

## Submission

**Target tool:** `send_calls`

Map each `transactions[].unsigned` from the `/order` response into `send_calls`:

```json
{
  "chain": "base",
  "calls": [
    {
      "to": "<unsigned.to>",
      "data": "<unsigned.data>",
      "value": "<unsigned.value>"
    }
  ]
}
```

- Strip `gasLimit` and `chainId` from each unsigned object — `send_calls` does not accept these fields.
- Chain string mapping: `networkId` `8453` → `"base"`, `56` → `"bsc"`.
- Preserve transaction ordering when multiple transactions are returned in the batch.
- Follow the approval/polling flow in [approval-mode.md](../references/approval-mode.md).

## Example Prompts

**Buy 100 USDC worth of a token on Base**
1. `get_wallets` → address.
2. `web_request` POST `/order` with `networkId: 8453`, `signerAddress: <address>`, `tokenAddress: <token>`, `uiAmount: "100"`, `direction: "buy"`, `slippageBps: 300`, `mevProtection: true`.
3. Map `transactions[].unsigned` → `send_calls(chain="base", calls)`.
4. User approves → `get_request_status(requestId)`.

**Sell tokens on Base with MEV protection**
1. `get_wallets` → address.
2. `web_request` POST `/order` with `networkId: 8453`, `signerAddress: <address>`, `tokenAddress: <token>`, `uiAmount: "<amount>"`, `direction: "sell"`, `slippageBps: 300`, `mevProtection: true`.
3. Map `transactions[].unsigned` → `send_calls(chain="base", calls)`.
4. User approves → `get_request_status(requestId)`.

**Buy a token with tight slippage**
1. `get_wallets` → address.
2. `web_request` POST `/order` with `slippageBps: 100` (1%), `mevProtection: true`.
3. Map `transactions[].unsigned` → `send_calls(chain="base", calls)`.
4. User approves → `get_request_status(requestId)`.

**Swap into a specific pool on Base**
1. `get_wallets` → address.
2. `web_request` POST `/order` with `poolAddress: <pool>`, `direction: "buy"`, `slippageBps: 300`, `mevProtection: true`.
3. Map `transactions[].unsigned` → `send_calls(chain="base", calls)`.
4. User approves → `get_request_status(requestId)`.

## Risks & Warnings

- **Slippage** — trades can fill materially worse than expected. Default to `300` bps (3%). For volatile or low-liquidity tokens, the user may need `500`–`1000` bps. Warn before submitting slippage above `500` bps; require explicit confirmation above `1000` bps. Never silently increase slippage.
- **Irreversible** — onchain swaps cannot be undone once confirmed. Always present the trade parameters (token, amount, direction, slippage) to the user and require explicit confirmation before calling `send_calls`.

## Notes

- **Network IDs:** `8453` = Base, `56` = BSC. Solana (`1399811149`) is supported by the o1.exchange API but not by Base MCP.
- **Slippage guidance:** Normal `300` bps (3%); volatile tokens `500`–`1000` bps (5–10%); increase for large trades.
- **MEV protection:** `mevProtection: true` routes through a private mempool to reduce front-running. Recommended for all trades.
- **Permit2 placeholder:** The fixed placeholder `42f68902113a2a579bcc207c91254c8516d921250e748c18a082d91d74908f8e9a05f27b72a030c6a42d77d0e0aab6fb09219b01a01e7b5b24e4f322ee1762ff1b` in `unsigned.data` must be replaced with the actual Permit2 signature when `permit2` is present.
- **Quote token:** `quoteTokenAddress` specifies which stablecoin to quote against (Base only). Omit to use the default.
- **Pool selection:** `poolAddress` targets a specific liquidity pool. Omit to let the API choose the best route.
- **API tokens:** Generated at https://o1.exchange/api-trading.
- **`/order/complete` relay:** The API provides a `/order/complete` endpoint for submitting signed transactions through o1.exchange's relay (for enhanced MEV protection). In the Base MCP flow, `send_calls` handles signing and broadcasting directly.
