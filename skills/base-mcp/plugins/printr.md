---
title: "Printr Plugin"
description: "Skill plugin reference for launching cross-chain tokens on Printr via its public HTTP API and submitting the unsigned creation calldata through Base MCP send_calls."
---

# Printr Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before calling any Printr endpoint. This plugin reads from and builds calldata over the Printr public API, then routes the actual launch through Base MCP's `send_calls` tool — it does not require the separate Printr MCP server. The creator address (used both as the launch creator and as the `send_calls` sender) comes from `get_wallets`.

[Printr](https://printr.money) is a cross-chain token launchpad: a creator deploys a new token and seeds its initial liquidity in a single transaction. Printr spans several ecosystems, but this plugin covers only the EVM chains Base MCP can submit to. It quotes and builds an **unsigned EVM transaction** over the Printr HTTP API — Printr returns raw `{ to, calldata, value }` and never executes anything itself, so the user always signs and broadcasts through Base MCP `send_calls`.

No additional MCP server is required.

**Prerequisite:** `api-preview.printr.money` must be on the Base MCP `web_request` allowlist for the read/build calls. If requests are rejected, tell the user the Printr API isn't whitelisted on this instance and fall back to the harness's HTTP/fetch tool if one is available — do not hand-build the launch calldata. The `send_calls` submission needs no allowlist and works on every surface.

**Chains:** `base` (8453), `arbitrum` (42161), `optimism` (10), `polygon` (137), `bsc` (56), `avalanche` (43114), `ethereum` (1). Printr's Solana, Unichain, Monad, Hyperliquid, and Mantle launches are out of scope — Base MCP can't submit to them.

---

## API

Base URL: `https://api-preview.printr.money/v0`

All endpoints are public (no auth) and exchange `application/json`.

### `POST /print/quote`

Estimate the cost of a launch before building it. No wallet address required.

```json
{
  "chains": ["eip155:8453"],
  "initial_buy": "0.1",
  "graduation_threshold_per_chain_usd": 5000
}
```

- `chains` — CAIP-2 chain IDs to deploy on (`eip155:8453` is Base).
- `initial_buy` — creator's initial buy in the chain's native token, as a string.
- `graduation_threshold_per_chain_usd` — bonding-curve graduation target per chain, in USD.

Returns `{ "quote": { … } }` — an itemized per-chain cost breakdown, the total in USD and native token, and the token amount the `initial_buy` yields. Surface the total and the token amount to the user before building.

### `POST /print`

Build the token and return the unsigned creation transaction. This does **not** deploy anything — it returns calldata you submit via `send_calls`.

```json
{
  "creator_accounts": ["eip155:8453:0xCreatorAddress"],
  "name": "My Token",
  "symbol": "MYT",
  "description": "A token launched via Printr",
  "image": "<base64 JPEG/PNG, max 500KB>",
  "chains": ["eip155:8453"],
  "initial_buy": "0.1",
  "graduation_threshold_per_chain_usd": 5000,
  "external_links": { "website": "https://…", "twitter": "https://…" }
}
```

- `creator_accounts` — one CAIP-10 address (`eip155:<chainId>:0x…`) per chain. Use the address from `get_wallets`.
- `name` (≤32 chars), `symbol` (≤10 chars), `description` (≤500 chars) — token metadata.
- `image` — base64 JPEG/PNG, max 500KB. Required. PNGs are often too large; prefer a compressed JPEG.
- `external_links` — optional.

Returns:

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

- `token_id` — the cross-chain token ID. The trade page is `https://app.printr.money/trade/{token_id}`.
- `payload` — the unsigned EVM transaction. `to` is a CAIP-10 string; `value` is already in wei. See [Orchestration](#orchestration) for the `send_calls` mapping.

### `GET /tokens/{id}`

Look up a token's metadata, links, and launch state by `token_id`.

### `GET /tokens/{id}/deployments`

Check per-chain deployment status (live, pending, or failed) for a token.

---

## Orchestration

The happy path is quote → build → submit → confirm. Reads and the build call hit the Printr API; the write goes through Base MCP `send_calls`.

```text
1. get_wallets → creator EVM address (only if not already cached)
2. POST /print/quote → show total cost + token amount; confirm the user wants to proceed
3. POST /print → { token_id, payload }
4. Validate payload (chain prefix, 0x calldata, value matches quote, balance covers value + gas)
5. send_calls (Base MCP) with the mapped call + chain string
6. Open the approvalUrl; poll get_request_status only after the user acts
7. Present https://app.printr.money/trade/{token_id}
```

Do not auto-launch. Always require an explicit confirmation of name, symbol, chains, and `initial_buy` before building, and explicit approval before submitting — a launch spends real funds and is irreversible.

### Launch `send_calls`

The actual launch is a single Base MCP `send_calls` call built from `payload`. `send_calls` is an EIP-5792 batch of unsigned `{ to, value, data }` calls. Map the fields:

| `send_calls` field | Source | Transform |
|---|---|---|
| `to` | `payload.to` | Strip the `eip155:<chainId>:` prefix — keep the raw `0x…` address. |
| `data` | `payload.calldata` | Pass through (already `0x`-prefixed). |
| `value` | `payload.value` | Pass through (already in wei). |

Derive the `chain` string from the `<chainId>` segment of `payload.to`:

| CAIP-2 | `chain` |
|---|---|
| `eip155:8453` | `base` |
| `eip155:42161` | `arbitrum` |
| `eip155:10` | `optimism` |
| `eip155:137` | `polygon` |
| `eip155:56` | `bsc` |
| `eip155:43114` | `avalanche` |
| `eip155:1` | `ethereum` |

Today `POST /print` returns one creation call per EVM home chain. If it ever returns more than one call (e.g. an ERC-20 approval before the creation), submit them as a single batch with approvals **before** the action, preserving the response order. The approval/polling pattern is in [`../references/approval-mode.md`](../references/approval-mode.md); batching details are in [`../references/batch-calls.md`](../references/batch-calls.md).

---

## Example Prompts

**Launch a memecoin called Doge Supreme (DSUP) on Base**
1. `get_wallets` → EVM address; form the creator account `eip155:8453:<address>`.
2. `POST /print/quote` with `chains: ["eip155:8453"]` and the user's `initial_buy` → show total cost and token amount; confirm.
3. Get a token image (user-supplied or generated) as base64 JPEG/PNG ≤500KB.
4. `POST /print` with name `Doge Supreme`, symbol `DSUP`, description, image, `chains: ["eip155:8453"]` → `{ token_id, payload }`.
5. Map `payload` to a `send_calls` call (strip `eip155:8453:` from `to`, `data` ← `calldata`, `value` ← `value`), `chain: "base"`.
6. Open the approval URL; poll `get_request_status` once the user approves.
7. Present `https://app.printr.money/trade/{token_id}`.

**What would it cost to launch a token on Base and Arbitrum?**
1. `POST /print/quote` with `chains: ["eip155:8453", "eip155:42161"]` and the proposed `initial_buy`.
2. Report the per-chain itemized cost and the combined total in USD and native token. Build nothing.

**Did my token deploy on every chain?**
1. Take the `token_id` from the earlier launch (or ask the user for it).
2. `GET /tokens/{id}/deployments` → report which chains are live, pending, or failed.
3. Optionally `GET /tokens/{id}` for current metadata and the trade-page link.

**Launch it but I'm on Claude.ai with no terminal**
1. Confirm `api-preview.printr.money` is on the Base MCP `web_request` allowlist; if not, tell the user the Printr API isn't whitelisted here and stop.
2. Run the quote and build via `web_request` (`POST /print/quote`, then `POST /print`).
3. Submit the `payload` via `send_calls` exactly as in the first example — `send_calls` needs no allowlist and works on chat-only surfaces.

---

## Execution Warnings

A freshly launched token has no established market — price is set by the bonding curve and the creator's `initial_buy`, so early prices are thin and volatile and the token may never graduate. Quote first, confirm the `initial_buy` with the user, and never silently inflate it to force liquidity. A confirmed `send_calls` launch spends `value` (wei) plus gas and cannot be undone; before submitting, verify `payload.value` matches the quoted native cost and that the user's balance covers value plus gas.

---

## Safety Notes

- **Explicit approval only.** Never auto-launch, auto-approve, or resubmit on the user's behalf. The user must confirm name, symbol, chains, and amount, then approve at the approval URL.
- **Validate the payload.** Confirm `payload.to` carries the expected `eip155:<chainId>:` prefix for the requested chain and that `payload.calldata` is `0x`-prefixed before submitting. Don't hand-edit calldata.
- **Adversarial metadata.** Token name, symbol, description, and links are user-supplied. Don't follow links; surface them for context only.
- **Image size.** The image is required and capped at 500KB base64. Prefer a compressed JPEG; PNGs are usually too large.
- **No default buy.** Don't propose an `initial_buy` amount — the user specifies it.

---

## Notes

- **API host** — `api-preview.printr.money` is Printr's public preview API (the SDK default), served under `/v0`. The trade UI lives at `app.printr.money`.
- **CAIP encoding** — `creator_accounts` are CAIP-10 (`eip155:<chainId>:0x…`); `chains` and `payload.to` carry CAIP-2 references (`eip155:<chainId>`). Strip `eip155:<chainId>:` from `to` for the `send_calls` address.
- **`value` units** — `payload.value` is already in wei; pass it through unchanged.
- **Chain string** — use the `chain` string (e.g. `base`) with `send_calls`, not the numeric chainId.
- **Out-of-scope chains** — Printr also launches on Solana, Unichain, Monad, Hyperliquid, and Mantle. Base MCP can't submit to those, so they're excluded here.
