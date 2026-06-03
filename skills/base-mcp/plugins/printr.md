---
title: "Printr Plugin"
description: "Launch cross-chain tokens on Printr via its HTTP API, then submit the unsigned creation calldata through Base MCP send_calls."
tags: [token-launches, memecoins, trading, discovery]
name: printr
version: 0.1.0
integration: http-api
chains: [base, arbitrum, optimism, polygon, bsc, avalanche, ethereum]
requires:
  shell: none
  allowlist: [api-preview.printr.money]
  externalMcp: null
  cliPackage: null
auth: none
risk: [low-liquidity, irreversible]
---

# Printr Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before calling any Printr endpoint. The user's wallet address — required as the creator account and as the `send_calls` sender — is fetched lazily via `get_wallets` when needed. No Printr API key or login is required.

## Overview

Printr is a cross-chain token launchpad: it lets a creator deploy a new token and seed its initial liquidity in a single transaction. Printr supports several ecosystems, but this plugin covers only the EVM subset that Base MCP can submit to — `base`, `arbitrum`, `optimism`, `polygon`, `bsc`, `avalanche`, and `ethereum` (Printr's Solana, Unichain, Monad, Hyperliquid, and Mantle support is out of scope here). The plugin reads cost estimates and builds an **unsigned EVM transaction payload** over the Printr HTTP API, then submits that payload as a `send_calls` batch through Base MCP. Printr returns raw `{ to, calldata, value }` calldata — it never executes the transaction itself, so the user always signs and broadcasts through Base MCP.

## Surface Routing

Printr is a plain HTTP API plus a `send_calls` submission, so no shell or CLI is ever required. The Printr API host must be reachable for the read/build steps; the actual onchain write always goes through Base MCP `send_calls`, which works on every surface.

| Capability | Harness with HTTP/shell (Claude Code, Codex, Cursor) | Chat-only / shell-less (Claude.ai, ChatGPT) |
|---|---|---|
| Quote a launch (read) | Harness HTTP tool → `POST /print/quote` | Base MCP `web_request` → `POST /print/quote` |
| Build a token (build calldata) | Harness HTTP tool → `POST /print` | Base MCP `web_request` → `POST /print` |
| Look up a token / deployments (read) | Harness HTTP tool → `GET /tokens/{id}`, `GET /tokens/{id}/deployments` | Base MCP `web_request` → same GETs |
| Submit the launch (write) | Base MCP `send_calls` | Base MCP `send_calls` |

On a shell-less / chat-only surface, `api-preview.printr.money` **must** be on the Base MCP `web_request` allowlist for the read/build steps to reach it. If `web_request` rejects that host, inform the user that the Printr API is not yet whitelisted on this MCP instance and stop — do not attempt to hand-build the launch calldata. The submission step (`send_calls`) is unaffected and needs no allowlist. The full execution decision tree (harness HTTP → `web_request` → user-paste, and the GET-only constraint on consumer surfaces) lives in [custom-plugins.md](../references/custom-plugins.md).

## Endpoints

All Printr endpoints are public (no auth) and are served under the `/v0` prefix on the Printr API host. Send and receive `application/json`.

Base URL: `https://api-preview.printr.money/v0`

### `POST /print/quote`

Estimate the cost of a launch before building it. No wallet address required.

Request body:

```json
{
  "chains": ["eip155:8453"],
  "initial_buy": "0.1",
  "graduation_threshold_per_chain_usd": 5000
}
```

- `chains` — array of CAIP-2 chain IDs to deploy on (e.g. `eip155:8453` for Base).
- `initial_buy` — creator's initial buy amount in the chain's native token (string).
- `graduation_threshold_per_chain_usd` — bonding-curve graduation target per chain, in USD.

Response: `{ "quote": { … } }` — an itemized cost breakdown per chain plus the total cost in USD and native tokens, and the number of tokens the `initial_buy` yields.

### `POST /print`

Build the token and return the unsigned creation transaction. This does **not** deploy anything — it returns calldata you submit via `send_calls`.

Request body (superset of the quote body):

```json
{
  "creator_accounts": ["eip155:8453:0xCreatorAddress"],
  "name": "My Token",
  "symbol": "MYT",
  "description": "A token launched via Printr",
  "image": "<base64-encoded image, max 500KB, JPEG/PNG>",
  "chains": ["eip155:8453"],
  "initial_buy": "0.1",
  "graduation_threshold_per_chain_usd": 5000,
  "external_links": { "website": "https://…", "twitter": "https://…" }
}
```

- `creator_accounts` — one CAIP-10 address (`eip155:<chainId>:0x…`) per chain being deployed to. Use the address from `get_wallets`.
- `name` (≤32 chars), `symbol` (≤10 chars), `description` (≤500 chars) — token metadata.
- `image` — base64-encoded JPEG/PNG, max 500KB. Required by the launchpad.
- `chains`, `initial_buy`, `graduation_threshold_per_chain_usd`, `external_links` — as above; `external_links` is optional.

Response (EVM home chain):

```json
{
  "token_id": "0x…",
  "payload": {
    "to": "eip155:8453:0x…",
    "calldata": "0x…",
    "value": "1000000000000000",
    "gas_limit": 2500000
  },
  "quote": { … }
}
```

- `token_id` — the cross-chain token ID (hex). The trade page is `https://app.printr.money/trade/{token_id}` — present this to the user after the launch confirms.
- `payload` — the unsigned EVM transaction (see [`## Submission`](#submission) for the `send_calls` mapping). `to` is a CAIP-10 string; `value` is already in wei.

### `GET /tokens/{id}`

Look up a token's details by its `token_id`. Returns metadata, links, and current launch state.

### `GET /tokens/{id}/deployments`

Check per-chain deployment status for a token (which target chains are live, pending, or failed).

## Orchestration

The happy path goes quote → build → submit → confirm. Reads and the build call hit the Printr HTTP API; the write goes through Base MCP `send_calls`.

1. **Get the creator address.** Call `get_wallets` and take the user's EVM address. This is both the `creator_accounts` entry (as CAIP-10, `eip155:<chainId>:<address>`) and the `send_calls` sender.
2. **Quote (optional but recommended).** `POST /print/quote` with `chains`, `initial_buy`, and `graduation_threshold_per_chain_usd`. Show the user the total cost in USD and native token, and the expected token amount from the initial buy. Confirm the user wants to proceed.
3. **Build the token.** `POST /print` with the full body (creator account, name, symbol, description, base64 image, chains, initial buy, graduation threshold, optional links). Receive `{ token_id, payload, quote }`.
4. **Validate before submit.** Confirm `payload.to` carries the expected `eip155:<chainId>:` prefix matching the requested chain, that `payload.calldata` is `0x`-prefixed, and that `payload.value` (wei) matches the quoted native-token cost. Confirm the user's balance covers `value` plus gas.
5. **Submit via `send_calls`.** Map the payload (see [`## Submission`](#submission)) and call `send_calls` with the matching chain string. This returns an approval URL and a request ID.
6. **Confirm.** The user approves at the returned approval URL (present as "Approve Transaction" — see [approval-mode.md](../references/approval-mode.md)). Poll `get_request_status(requestId)` until confirmed.
7. **Surface the trade page.** Once confirmed, give the user `https://app.printr.money/trade/{token_id}`. Optionally call `GET /tokens/{id}/deployments` to report per-chain status.

## Submission

Target Base MCP tool: **`send_calls`** — an EIP-5792 batch of unsigned `{ to, value, data }` calls. Printr's `POST /print` response carries a single EVM call in `payload`; map it as follows:

| `send_calls` call field | Source in Printr `payload` | Transform |
|---|---|---|
| `to` | `payload.to` | Strip the CAIP-10 prefix `eip155:<chainId>:` — keep the raw `0x…` address. |
| `data` | `payload.calldata` | Pass through (already `0x`-prefixed hex). |
| `value` | `payload.value` | Pass through (already in wei). |

Derive the `send_calls` `chain` string from the `<chainId>` segment of `payload.to` (the CAIP-2 chain reference), mapping it to the Base MCP chain string:

| CAIP-2 chain ID | Base MCP `chain` |
|---|---|
| `eip155:8453` | `base` |
| `eip155:42161` | `arbitrum` |
| `eip155:10` | `optimism` |
| `eip155:137` | `polygon` |
| `eip155:56` | `bsc` |
| `eip155:43114` | `avalanche` |
| `eip155:1` | `ethereum` |

Batching: if the launch ever returns more than one call (e.g. an ERC-20 approval ahead of the creation), submit them as a single `send_calls` batch with approvals **before** the action, preserving the response order. Today `POST /print` returns one creation call per EVM home chain. After submission, follow the approval/polling flow in [approval-mode.md](../references/approval-mode.md).

## Example Prompts

### "Launch a memecoin called Doge Supreme (DSUP) on Base"

1. `get_wallets` → EVM address; form the creator account `eip155:8453:<address>`.
2. `POST /print/quote` with `chains: ["eip155:8453"]` and the user's `initial_buy` → show total cost; confirm.
3. Obtain a token image (user-supplied or generated) as base64 JPEG/PNG ≤500KB.
4. `POST /print` with name `Doge Supreme`, symbol `DSUP`, description, image, `chains: ["eip155:8453"]` → `{ token_id, payload }`.
5. Map `payload` to a `send_calls` call (strip the `eip155:8453:` prefix from `to`, `data` ← `calldata`, `value` ← `value`), `chain: "base"`.
6. User approves at the approval URL → `get_request_status(requestId)` until confirmed.
7. Present `https://app.printr.money/trade/{token_id}`.

### "What would it cost to launch a token on Base and Arbitrum?"

1. `POST /print/quote` with `chains: ["eip155:8453", "eip155:42161"]` and the proposed `initial_buy`.
2. Report the per-chain itemized cost and the combined total in USD and native tokens; no transaction is built or submitted.

### "Did my token deploy on every chain?"

1. Take the `token_id` from the earlier launch (or ask the user for it).
2. `GET /tokens/{id}/deployments` → report which target chains are live, pending, or failed.
3. Optionally `GET /tokens/{id}` for current metadata and the trade-page link.

### "Launch it but I'm on Claude.ai with no terminal"

1. Confirm `api-preview.printr.money` is on the Base MCP `web_request` allowlist; if not, tell the user the Printr API isn't whitelisted on this instance and stop.
2. Run the quote and build via `web_request` (`POST /print/quote`, then `POST /print`).
3. Submit the resulting `payload` via `send_calls` exactly as in the first example — `send_calls` needs no allowlist and works on chat-only surfaces.

## Risks & Warnings

- **low-liquidity** — A freshly launched token has no established market: price is set by the bonding curve and the creator's `initial_buy`, so early prices are thin and volatile and the token may never graduate. Quote the launch first and confirm the `initial_buy` amount with the user; never silently inflate the initial buy to force liquidity.
- **irreversible** — A confirmed `send_calls` launch deploys the token and spends the `value` (in wei) plus gas; it cannot be undone. Before submitting, verify `payload.value` matches the quoted native-token cost and that the user's balance covers value plus gas, and require explicit user approval at the approval URL. Never auto-approve or resubmit on the user's behalf.

## Notes

- **API host** — `api-preview.printr.money` is Printr's public preview API host (the SDK default). All paths are served under `/v0` (e.g. `https://api-preview.printr.money/v0/print`). The app/trade UI lives at `app.printr.money`.
- **CAIP encoding** — `creator_accounts` are CAIP-10 (`eip155:<chainId>:0x…`); `chains` and the payload's `to` carry CAIP-2 chain references (`eip155:<chainId>`). Strip `eip155:<chainId>:` from `to` to get the raw `0x` address for `send_calls`.
- **`value` units** — `payload.value` is already in wei; pass it through to `send_calls` unchanged.
- **Image** — required, base64-encoded JPEG/PNG, max 500KB. PNGs are often too large; prefer a compressed JPEG.
- **Out-of-scope chains** — Printr also launches on Solana, Unichain, Monad, Hyperliquid, and Mantle. Base MCP does not submit to those, so they are excluded from this plugin's `chains`.

### EVM chain reference

| Chain | CAIP-2 | Base MCP `chain` |
|---|---|---|
| Base | `eip155:8453` | `base` |
| Arbitrum | `eip155:42161` | `arbitrum` |
| Optimism | `eip155:10` | `optimism` |
| Polygon | `eip155:137` | `polygon` |
| BSC | `eip155:56` | `bsc` |
| Avalanche | `eip155:43114` | `avalanche` |
| Ethereum | `eip155:1` | `ethereum` |
