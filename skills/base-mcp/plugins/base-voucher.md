---
title: "Base Voucher Plugin"
description: "Create and redeem ETH/USDC crypto gift cards on Base via Base Voucher MCP or HTTP prepare API → Base MCP send_calls."
tags: [agent-commerce, payment-cards, gift-cards]
name: base-voucher
version: 0.3.0
integration: hybrid
chains: [base]
requires:
  shell: none
  allowlist: [base-analytics-app.vercel.app]
  externalMcp:
    name: base-voucher
    transport: http
    url: https://base-analytics-app.vercel.app/api/mcp
  cliPackage: null
auth: none
risk: [pii, irreversible]
---

# Base Voucher Plugin

> [!IMPORTANT]
> Run Base MCP onboarding first (see `SKILL.md`). Base Voucher prepares **unsigned calldata only** — execute through Base MCP `send_calls` after the user approves. **Card secrets are shown once at create time and cannot be recovered** from chain or the app if lost.

## Overview

Base Voucher is a decentralized crypto gift card protocol on Base mainnet (ETH and USDC only). Users deposit a total amount, split it evenly into 1–50 cards, and share each card's **Card ID** + **Secret** with recipients who redeem onchain.

This plugin has two prepare paths that both return unsigned `calls[]` for Base MCP `send_calls`:

1. **Base Voucher MCP (preferred):** hosted at `https://base-analytics-app.vercel.app/api/mcp` — tools `voucher_prepare_create`, `voucher_prepare_redeem`, `voucher_lookup_batch`, `voucher_list_by_creator`.
2. **HTTP fallback:** GET prepare endpoints on `base-analytics-app.vercel.app` when the MCP is not connected but HTTP is available (harness HTTP, allowlisted `web_request`, or GET user-paste on consumer chat surfaces).

**App:** https://base-analytics-app.vercel.app  
**Supported chain:** Base mainnet (`8453` / Base MCP chain string `base`).

## Detection

After Base MCP onboarding (`SKILL.md`), pick a prepare path:

1. **Base Voucher MCP connected** — `voucher_prepare_create`, `voucher_prepare_redeem`, or `voucher_lookup_batch` are callable → use MCP tools (Path 1). No JSON paste.
2. **Harness HTTP tool available** (Claude Code, Cursor, Codex, …) → GET the HTTP endpoints below (Path 2).
3. **No harness HTTP, Base MCP `web_request` allowlists `base-analytics-app.vercel.app`** → GET via `web_request` (Path 2).
4. **Claude / ChatGPT consumer surface, host not allowlisted** → construct the full GET URL, ask the user to paste it into chat, then parse the response (Path 2, GET-only fallback per [../references/custom-plugins.md](../references/custom-plugins.md)).
5. **None of the above** → stop and link the user to https://base-analytics-app.vercel.app for manual create/redeem.

Onchain execution always uses Base MCP `get_wallets` (when needed) and `send_calls` — Base Voucher never signs or broadcasts.

## Installation

Base Voucher MCP is a separate remote MCP server. Base MCP (`https://mcp.base.org`) must also be connected for wallet reads and `send_calls`.

**Base Voucher MCP URL:** `https://base-analytics-app.vercel.app/api/mcp` (no OAuth)

- **Claude.ai / Claude Desktop:** Settings → Connectors → Add custom connector  
  - Name: `Base Voucher`  
  - URL: `https://base-analytics-app.vercel.app/api/mcp`  
  One-click: [Add Base Voucher connector](https://claude.ai/customize/connectors?modal=add-custom-connector&connectorName=Base%20Voucher&connectorUrl=https%3A%2F%2Fbase-analytics-app.vercel.app%2Fapi%2Fmcp)
- **Claude Code:** `claude mcp add --transport http base-voucher https://base-analytics-app.vercel.app/api/mcp`
- **Cursor:** `.cursor/mcp.json` or `~/.cursor/mcp.json`:

  ```json
  {
    "mcpServers": {
      "base-voucher": {
        "url": "https://base-analytics-app.vercel.app/api/mcp"
      }
    }
  }
  ```

Reconnect or restart the harness after adding. For HTTP fallback on chat-only surfaces without the MCP, `base-analytics-app.vercel.app` must be on the Base MCP `web_request` allowlist — request this when opening the `base/skills` PR.

### MCP tools (Path 1)

| Tool | Parameters | Returns |
|------|------------|---------|
| `voucher_prepare_create` | `total`, `cards`, `asset?`, `message?`, `creator?` | JSON with `valid`, `calls[]`, `cards[]` |
| `voucher_prepare_redeem` | `cardId`, `secret` | JSON with `valid`, `calls[]`, `preview` |
| `voucher_lookup_batch` | `batchId` | Live batch + per-card `redeemed` flags (no secrets) |
| `voucher_list_by_creator` | `creator` | All batches for wallet + `totalUnredeemed` summary |

After a successful prepare tool call, map `calls[]` to Base MCP `send_calls` with `chain: "base"`.

## Surface Routing

HTTP routing follows [../references/custom-plugins.md](../references/custom-plugins.md). Prepare endpoints are **GET-only**, so the user-paste fallback is viable on Claude/ChatGPT consumer surfaces when the host is not allowlisted.

| Capability | Harness with Base Voucher MCP | Harness HTTP / allowlisted `web_request` | Chat-only, host not allowlisted |
| --- | --- | --- | --- |
| Prepare create / redeem | `voucher_prepare_create` / `voucher_prepare_redeem` | GET prepare URLs below | User-paste GET URL → parse JSON |
| List creator batches | `voucher_list_by_creator` | GET `/api/vouchers?creator=&live=1` | User-paste GET URL |
| Batch redemption status | `voucher_lookup_batch` | GET `/api/vouchers?batchId=&live=1` | User-paste GET URL |
| Execute onchain | Base MCP `send_calls` | Base MCP `send_calls` | Base MCP `send_calls` |

Shell access is not required. If neither Base Voucher MCP nor any HTTP path can reach `base-analytics-app.vercel.app`, stop and link https://base-analytics-app.vercel.app.

## Endpoints

Base URL: `https://base-analytics-app.vercel.app`

### Read endpoints (Path 2)

```
GET https://base-analytics-app.vercel.app/api/vouchers?batchId=<batchId>&live=1
GET https://base-analytics-app.vercel.app/api/vouchers?creator=<0x-address>&live=1
```

**`live=1`** reads onchain redemption state. No card secrets are returned.

**Creator summary** (`creator` + `live=1`):

```json
{
  "creator": "0x...",
  "batchCount": 2,
  "totalCards": 15,
  "totalRedeemed": 3,
  "totalUnredeemed": 12,
  "batches": [
    {
      "batchId": 42,
      "cardCount": 5,
      "redeemedCount": 1,
      "unredeemedCount": 4,
      "amountPerCardFormatted": "$2.00 USDC"
    }
  ]
}
```

**Batch detail** (`batchId` + `live=1`):

```json
{
  "batch": {
    "batchId": 42,
    "redeemedCount": 1,
    "unredeemedCount": 4
  },
  "cards": [
    { "cardIndex": 0, "cardId": "42-0", "redeemed": true },
    { "cardIndex": 1, "cardId": "42-1", "redeemed": false }
  ]
}
```

Without `live=1`, stored metadata only (may be stale for `redeemedCount`).

### Prepare create (Path 2)

```
GET https://base-analytics-app.vercel.app/api/voucher/prepare-create?asset=USDC&total=10&cards=5&message=Happy+Birthday&creator=<0x-address>
```

| Param | Required | Notes |
|-------|----------|-------|
| `asset` | no (default `USDC`) | `USDC` or `ETH` |
| `total` | yes | Human decimal string — `10` = $10 USDC or 10 ETH units |
| `cards` | yes | Integer 1–50; total must divide evenly per card |
| `message` | no | Optional note on cards (max 280 chars onchain) |
| `creator` | recommended | User wallet from `get_wallets`; omits USDC `approve` call when allowance is sufficient |

**Success response shape:**

```json
{
  "valid": true,
  "protocol": "Base Voucher",
  "chain": "base",
  "contract": "0x...",
  "expectedBatchId": 42,
  "asset": "USDC",
  "total": "10",
  "cardCount": 5,
  "perCardFormatted": "$2.00 USDC",
  "calls": [
    { "to": "0x...", "data": "0x...", "value": "0x0" }
  ],
  "cards": [
    {
      "cardId": "42-0",
      "cardIndex": 0,
      "secret": "ABCDE-FGHIJ-KLMNO-PQRST",
      "shareText": "🎁 Base Voucher — Crypto Gift Card\n..."
    }
  ]
}
```

When `valid: false`, read `error` and ask the user to adjust `total` or `cards`. Do not call `send_calls`.

For USDC, `calls` may contain **two** ordered steps: `approve` (USDC) then `createUsdcBatch`. For ETH, `calls` contains one payable step; use each item's `value` field (may be non-zero for ETH).

### Prepare redeem (Path 2)

```
GET https://base-analytics-app.vercel.app/api/voucher/prepare-redeem?cardId=12-3&secret=ABCDE-FGHIJ-KLMNO-PQRST
```

| Param | Required | Notes |
|-------|----------|-------|
| `cardId` | yes | Format `batchId-cardIndex` (e.g. `12-3`) |
| `secret` | yes | UniVoucher-style code `XXXXX-XXXXX-XXXXX-XXXXX` (case-insensitive) |

**Success response shape:**

```json
{
  "valid": true,
  "cardId": "12-3",
  "batchId": 12,
  "cardIndex": 3,
  "calls": [{ "to": "0x...", "data": "0x...", "value": "0x0" }],
  "preview": {
    "asset": "USDC",
    "amountFormatted": "$2.00 USDC",
    "message": "Happy Birthday",
    "alreadyRedeemed": false
  }
}
```

If `preview.alreadyRedeemed` is `true` or `valid` is `false`, stop — do not call `send_calls`.

## Orchestration

### Create and share cards (MCP — preferred)

```
1. get_wallets → address (Base MCP)
2. voucher_prepare_create(total, cards, asset?, message?, creator=address) (Base Voucher MCP)
3. If valid: false → show error, stop
4. send_calls(chain="base", calls from response.calls[]) (Base MCP)
5. User approves → get_request_status(requestId)
6. Print response.cards[] — cardId, secret, shareText
```

### Create and share cards (HTTP fallback)

```
1. get_wallets → address
2. GET /api/voucher/prepare-create?... (Path 2 routing above)
3. send_calls → show cards
```

### Redeem a card (MCP — preferred)

```
1. get_wallets → address
2. voucher_prepare_redeem(cardId, secret)
3. Confirm preview.amountFormatted with user
4. send_calls(chain="base", calls from response.calls[])
5. User approves → get_request_status
```

### Redeem a card (HTTP fallback)

```
1. GET /api/voucher/prepare-redeem?cardId=...&secret=...
2. send_calls after user confirms preview
```

### Lookup batch (read-only)

```
1. voucher_lookup_batch(batchId) or GET /api/vouchers?batchId=<n>&live=1
2. Report redeemedCount, unredeemedCount, and per-card redeemed flags (no secrets)
```

### List creator batches (read-only)

```
1. get_wallets → address (Base MCP)
2. voucher_list_by_creator(creator=address) or GET /api/vouchers?creator=<address>&live=1
3. Report batchCount, totalUnredeemed, and each batch's unredeemedCount
```

## Submission

Target tool: **`send_calls`**.

Map every object in `response.calls[]` directly into the `calls` array:

```json
{
  "chain": "base",
  "calls": [
    { "to": "<call.to>", "value": "<call.value>", "data": "<call.data>" }
  ]
}
```

- `value` defaults to `0x0` when omitted in the mapping; ETH create batches may require a non-zero `value` on the final call — always pass through the API value unchanged.
- Execute all `calls` in order as **one** `send_calls` batch so the user approves once (USDC approve + create is atomic).
- After broadcast, poll `get_request_status(requestId)` per [../references/approval-mode.md](../references/approval-mode.md).

## Example Prompts

### Create 5 USDC gift cards with $10 total

```
1. get_wallets → address
2. voucher_prepare_create(total="10", cards=5, creator=<address>)
3. send_calls(chain="base", calls from response.calls)
4. User approves → get_request_status
5. Return all cardId + secret + shareText pairs to the user
```

### Split 0.01 ETH into 3 cards with a message

```
1. get_wallets → address
2. voucher_prepare_create(asset="ETH", total="0.01", cards=3, message="GM from Base", creator=<address>)
3. send_calls(chain="base", calls from response.calls) — preserve ETH value field
4. User approves → get_request_status
5. Share cards with user
```

### Redeem card 12-3

```
1. get_wallets → address
2. voucher_prepare_redeem(cardId="12-3", secret=<user-provided-secret>)
3. Confirm preview.amountFormatted with user
4. send_calls(chain="base", calls from response.calls)
5. User approves → get_request_status
```

### Check batch status

```
1. voucher_lookup_batch(batchId=12)
2. Report unredeemedCount and which cardIds are still available
```

### How many of my vouchers are unredeemed?

```
1. get_wallets → address
2. voucher_list_by_creator(creator=<address>)
3. Say: "You created X batches. Y of Z cards are not redeemed yet." List each batch with unredeemedCount.
```

## Risks & Warnings

- **PII / secrets.** Create responses include irreversible gift-card secrets. Display them only to the creator, warn that loss is permanent, and do not store secrets in long-term memory without explicit user consent.
- **Irreversible onchain writes.** Create and redeem move real ETH/USDC. Always run Base MCP onboarding, show the approval link, and wait for user confirmation before `send_calls`.
- **One redeem per wallet per batch.** Onchain rule: each wallet may redeem at most one card per batch. If redeem fails with a wallet-limit error, explain this constraint.
- **Even split requirement.** Total deposit must divide evenly across card count (USDC 6 decimals, ETH 18 decimals). The prepare endpoint returns `valid: false` when split is impossible — adjust amounts rather than forcing the transaction.

## Notes

- **Card ID format:** `{batchId}-{cardIndex}` — zero-based index (batch with 5 cards uses `N-0` … `N-4`).
- **Secret format:** `XXXXX-XXXXX-XXXXX-XXXXX` (uppercase alphanumeric, no ambiguous chars).
- **Max cards:** 50 per batch.
- **Assets:** ETH (native) and USDC on Base (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`) only.
- **expectedBatchId:** predicted from `nextBatchId` at prepare time; verify onchain after create if batch ID matters for support.
- **Web UI:** https://base-analytics-app.vercel.app — manual create/redeem fallback when HTTP is unavailable.
- **Allowlist request:** submitters should ask Base maintainers to add `base-analytics-app.vercel.app` to the MCP `web_request` allowlist when opening the `base/skills` PR.
