---
title: "Haiku Plugin"
description: "Intent-based swaps and cross-chain bridging on Haiku via HTTP API → onchain Permit2 approval + send_calls across 7 chains."
tags: [dex, swap, bridge, trading]
name: haiku
version: 0.2.0
integration: http-api
chains: [base, ethereum, arbitrum, optimism, polygon, bsc, avalanche]
requires:
  shell: none
  allowlist: [api.haiku.trade]
  externalMcp: null
  cliPackage: null
auth: none
risk: [slippage, irreversible]
---

# Haiku Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before calling any Haiku endpoint. The user's wallet address is fetched lazily via `get_wallets` when a quote or build actually needs it.

## Overview

Haiku (`haiku.trade`) is an intent-based swap and cross-chain bridge aggregator. Instead of a single-pool swap, the user expresses an *intent* — a set of input token positions and desired target weights — and Haiku's solver routes across DEXs and bridge protocols (Relay, Across, LiFi, Squid) to build the transaction that reaches that target, on one chain or across chains. The plugin calls the Haiku HTTP API to fetch a quote, then builds **unsigned calldata** and submits it through Base MCP's `send_calls`. Haiku's router pulls input tokens via Permit2 (`IAllowanceTransfer`); this plugin grants that allowance **onchain** in the same `send_calls` batch (ERC-20 approve → Permit2 approve → router execute) so it works with Base MCP's default smart-account wallet — it does **not** ask the user to sign an off-chain Permit2 message.

## Surface Routing

| Capability | Harness surface (Claude Code, Cursor) | Chat-only surface (Claude.ai, ChatGPT) |
|---|---|---|
| POST /quote (quote + approval data) | Harness HTTP tool — no allowlist needed | `web_request` — requires `api.haiku.trade` allowlisted |
| POST /solve (build calldata) | Harness HTTP tool — no allowlist needed | `web_request` — requires `api.haiku.trade` allowlisted |
| Token resolution (GET /tokenList, /searchTokens) | Harness HTTP tool — no allowlist needed | `web_request` — requires `api.haiku.trade` allowlisted |
| Submit approvals + swap | `send_calls` — all surfaces | `send_calls` — all surfaces |

On chat-only surfaces where the allowlist is not configured: inform the user that the intent cannot be built and direct them to the Haiku web app at `haiku.trade`. Do **not** improvise a workaround. For the full decision tree, see [../references/custom-plugins.md](../references/custom-plugins.md).

## Endpoints

Base URL: `https://api.haiku.trade/v1`

Requests are public — no API key is required. Send `Haiku-Source: base-mcp` on each request for attribution.

Token positions are identified by an **IID** of the form `<haikuChain>:<tokenAddress>` (see the chain-name mapping in `## Notes` — Haiku uses short chain names like `base`, `arb`, `eth`, which differ from the Base MCP chain strings used by `send_calls`).

### POST /quote

Fetches a solved quote for an intent. Returns the `quoteId`, the ERC-20 `approvals` to batch, and `permit2Datas` (the Permit2 allowance parameters — used to build an **onchain** Permit2 approval, not to sign a message).

```json
{
  "url": "https://api.haiku.trade/v1/quote",
  "method": "POST",
  "headers": { "content-type": "application/json", "Haiku-Source": "base-mcp" },
  "body": {
    "intent": {
      "input_positions": { "base:0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913": 10 },
      "target_weights":   { "base:0x4200000000000000000000000000000000000006": 1 },
      "slippage": 0.01,
      "receiver": "<walletAddress>"
    }
  }
}
```

| Field | Required | Notes |
|---|---|---|
| `input_positions` | ✅ | Map of `<haikuChain>:<tokenAddress>` → **human-decimal** amount (e.g. `10` = 10 USDC, not wei). All input keys must share one chain. |
| `target_weights` | ✅ | Map of `<haikuChain>:<tokenAddress>` → weight. Weights must sum to between `0.99` and `1`. |
| `slippage` | ✅ | Number between `0` and `1` (e.g. `0.01` = 1%). See [Risks & Warnings](#risks--warnings). |
| `receiver` | ✅ | Recipient EVM address (the user's wallet). Must be a non-zero `0x…` address. |

Response shape (fields used by this plugin):

```json
{
  "quoteId": "98269e93-8efc-44c6-b9fd-fa500ee717a6",
  "balances": [{ "token": { "symbol": "WETH", "decimals": 18 }, "amount": "0.005201", "amountMin": "0.005149", "amountUSD": 10.0, "amountMinUSD": 9.9 }],
  "fees": [{ "token": { "symbol": "USDC" }, "amountUSD": 0 }],
  "gas": { "amount": 130265, "usd": "0.0015" },
  "approvals": [{ "data": "0x095ea7b3…", "to": "0x833589…2913", "chainId": 8453 }],
  "permit2Datas": {
    "domain": { "name": "Permit2", "chainId": 8453, "verifyingContract": "0x000000000022D473030F116dDEE9F6B43aC78BA3" },
    "types": { "PermitSingle": [ … ], "PermitDetails": [ … ] },
    "values": { "details": { "token": "0x833589…", "amount": { "type": "BigNumber", "hex": "0x989680" }, "expiration": 1784689975, "nonce": 0 }, "spender": "0x47e1…agent", "sigDeadline": 1784689975 }
  },
  "isComplexBridge": false,
  "routes": [{ "routeId": "…", "outputs": [ … ], "totalAmountUsd": 10.0 }]
}
```

Fields to keep:
- `approvals[]` — each is a ready-to-use ERC-20 `approve(Permit2, MAX)` call (`data`, `to` = token, `chainId`). Batch these first.
- `permit2Datas.values` — `details` (object for `PermitSingle`, array for `PermitBatch`), each detail's `token`, `amount` (an ethers `BigNumber` JSON `{type, hex}`), `expiration`, and the shared `spender` (the user's Haiku **agent** address, i.e. the Permit2 spender). Used to build the onchain Permit2 `approve` calls (see `## Submission`).
- `permit2Datas.domain.verifyingContract` — the Permit2 contract address (the `to` for the Permit2 approve call).

`balances` is the projected output. Show `amountUSD` (expected out), `amountMinUSD` (min out after slippage), and `gas.usd` to the user and confirm before proceeding. If `routes` has more than one entry, the user may pick a `routeId` to pass to `/solve`.

### POST /solve

Builds the final unsigned router transaction from a quote. **Call it without a signature** — the plugin grants the Permit2 allowance onchain in the batch, so no `permit2Signature` is sent.

```json
{
  "url": "https://api.haiku.trade/v1/solve",
  "method": "POST",
  "headers": { "content-type": "application/json", "Haiku-Source": "base-mcp" },
  "body": {
    "quoteId": "<quoteId from /quote>",
    "permit2Datas": { "…": "the permit2Datas object from /quote, verbatim" }
  }
}
```

Response shape:

```json
{ "to": "0x…routerAddress", "data": "0x…", "value": "0" }
```

`value` is a **decimal** wei string (`"0"` for ERC-20 input). Hex-encode it before passing as `value` in `send_calls`: `"0x" + BigInt(value).toString(16)`. Quotes are cached server-side and expire — if `/solve` reports the quote is not found, re-fetch `/quote` and retry. Do **not** send `permit2Signature`; a signature would be baked into the calldata as an EOA-style Permit2 `permit()` and would revert for a smart-account wallet.

### Token resolution (GET /tokenList, GET /searchTokens)

- `GET /tokenList?chain=<haikuChain>` — returns Haiku's token list (`iid`, `address`, `symbol`, `decimals`, `network`). Filter candidates to the requested chain before matching a symbol: prefer `iid` prefix (`base:`, `arb:`, `eth:`, etc.) or the `network` chainId from the table in `## Notes`. Use the filtered `iid` directly in `input_positions` / `target_weights`.
- `GET /searchTokens?...` — search tokens not in the base list via Relay's currencies index.

Prefer the known-addresses table in `## Notes` first, then these endpoints.

## Orchestration

### Swap / bridge

1. `get_wallets` → `walletAddress` (used as `receiver`).
2. Resolve token symbols to `<haikuChain>:<tokenAddress>` IIDs — use the `## Notes` table first, then `GET /tokenList`.
3. Build the `intent`: `input_positions` (human-decimal amount), `target_weights` (must sum to ~1), `slippage` (default `0.01`; apply the thresholds in `## Risks & Warnings`), `receiver = walletAddress`.
4. `POST /quote` → `quoteId`, `balances` (projected out), `gas`, `approvals`, `permit2Datas`, `routes`. Show expected output (`amountUSD`), minimum output (`amountMinUSD`), and gas cost; confirm with the user before proceeding.
5. `POST /solve` with `quoteId` and `permit2Datas` (and `routeId` if the user chose a route) — **no signature** → `{ to, data, value }`.
6. Build the calls array (all onchain, no off-chain signing):
   - **ERC-20 input**: `[erc20_approve..., permit2_approve..., router_execute]` — see `## Submission`.
   - **Native input** (sentinel `0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee`): `[router_execute]` only; the quote returns no `approvals` and `/solve` returns a non-zero `value`.
7. `send_calls(chain, calls)` → `approvalUrl`, `requestId`.
8. Present `approvalUrl` to the user. Do not auto-approve. Call `get_request_status(requestId)` only after the user acts.

## Submission

Target tool: **`send_calls`** (onchain approvals batched before the router execute call). This plugin does **not** use `sign` — the Permit2 allowance is granted onchain so the flow works for Base MCP's default smart-account wallet.

For ERC-20 input, build the batch with all ERC-20 approvals first, all Permit2 approvals second, and the router execution last:

```json
{
  "chain": "<Base MCP chain string>",
  "calls": [
    { "to": "<approvals[0].to (token)>", "value": "0x0", "data": "<approvals[0].data>" },
    { "to": "<...one call per approvals[] entry>", "value": "0x0", "data": "<...>" },
    { "to": "<permit2Datas.domain.verifyingContract>", "value": "0x0", "data": "<Permit2 approve calldata for details[0]>" },
    { "to": "<...one call per Permit2 detail>", "value": "0x0", "data": "<...>" },
    { "to": "<solve.to (router)>", "value": "<hex(solve.value)>", "data": "<solve.data>" }
  ]
}
```

1. **ERC-20 → Permit2 approve** — use each entry in the quote's `approvals` verbatim (`{ to, value: "0x0", data }`). These are `approve(Permit2, MAX)` calls already encoded by Haiku.

2. **Permit2 → agent approve** *(onchain, replaces the off-chain signature)* — encode `IAllowanceTransfer.approve(address token, address spender, uint160 amount, uint48 expiration)`:

   ```
   Function: approve(address token, address spender, uint160 amount, uint48 expiration)
   Selector: 0x87517c45
   token:      detail.token                             (32-byte left-padded)
   spender:    permit2Datas.values.spender              (the Haiku agent; 32-byte left-padded)
   amount:     detail.amount                            (uint160, from the BigNumber hex)
   expiration: detail.expiration                        (uint48)
   ```
   `to` = `permit2Datas.domain.verifyingContract` (the Permit2 contract, `0x000000000022D473030F116dDEE9F6B43aC78BA3`). For a single ERC-20 input, `permit2Datas.values.details` is an object (`PermitSingle`); wrap it as a one-item list before encoding. For multiple ERC-20 inputs, it is an array (`PermitBatch`); encode one onchain Permit2 `approve` call for each `details[]` entry, using the same `spender`.

3. **Router execute** — the `{ to, data, value }` from `/solve` (called without a signature). `to` is Haiku's router; `value` = `"0x" + BigInt(solve.value).toString(16)` (non-zero only for native input).

Use Base MCP **chain name strings** (`base`, `ethereum`, `arbitrum`, `optimism`, `polygon`, `bsc`, `avalanche`) for the `chain` param — **not** Haiku's short IID prefixes and not numeric chain IDs. For a cross-chain intent the input chain governs `send_calls`; the bridge delivers to the destination chain. The input/source chain must have a Base MCP `chain` string in the table below; destination-only chains may use Haiku's IID prefix even when Base MCP cannot submit transactions on that chain. After `send_calls` returns an approval URL, follow the flow in [../references/approval-mode.md](../references/approval-mode.md).

## Example Prompts

**"Swap 10 USDC to ETH on Base"**

1. `get_wallets` → address.
2. `POST /quote` — `input_positions` = `{ "base:0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913": 10 }`, `target_weights` = `{ "base:0x4200000000000000000000000000000000000006": 1 }`, `slippage` = `0.01`, `receiver` = address.
3. Show projected output (`balances[0].amountUSD`), min output, and `gas.usd`; confirm.
4. `POST /solve` with `quoteId` + `permit2Datas` (no signature) → `{ to, data, value: "0" }` → hex-encode value to `"0x0"`.
5. Encode the Permit2 `approve` call from `permit2Datas.values`.
6. `send_calls("base", [erc20_approve, permit2_approve, router_execute])` — first two from the quote/permit2Datas, last from `/solve`.

**"Bridge 100 USDC from Base to Arbitrum"** *(cross-chain)*

1. `get_wallets` → address.
2. `POST /quote` — `input_positions` = `{ "base:0x833589…2913": 100 }`, `target_weights` = `{ "arb:0xaf88d065e77c8cC2239327C5EDb3A432268e5831": 1 }`, `slippage` = `0.01`, `receiver` = address.
3. Show projected output on Arbitrum, min output, and gas; confirm. Note the input chain (`base`) governs submission.
4. `POST /solve` (no signature) → `{ to, data, value }`.
5. Encode the Permit2 `approve` call from `permit2Datas.values`.
6. `send_calls("base", [erc20_approve, permit2_approve, bridge_execute])`. The bridge delivers USDC to the wallet on Arbitrum.

**"What would I get swapping 500 USDC to WETH on Base?"** *(read-only)*

1. `get_wallets` → address (used as `receiver`).
2. `POST /quote` — `input_positions` = `{ "base:0x833589…2913": 500 }`, `target_weights` = `{ "base:0x4200000000000000000000000000000000000006": 1 }`, `slippage` = `0.01`.
3. Return `balances[0].amountUSD` (expected WETH out), `amountMinUSD`, and `gas.usd` to the user — no `/solve`, no transaction submitted.

## Risks & Warnings

- **Slippage** — The solver routes across DEXs and bridges; the executed price can move between quote and execution. Apply the following thresholds (`slippage` is a fraction, `0.01` = 1%):

  | Tolerance | Level | Action |
  |---|---|---|
  | ≤ 0.01 (1%) | Normal | Proceed. |
  | > 0.01 and ≤ 0.05 (5%) | Elevated | Mention the value and ask the user to confirm. |
  | > 0.05 and ≤ 0.20 (20%) | High | Warn that the trade can fill significantly below quote and is a likely sandwich target. Require explicit confirmation. |
  | > 0.20 | Very high | Strongly warn; do not submit without the user re-confirming the exact number. |

  If the user does not specify slippage, default to `0.01` for common pairs and `0.02` for long-tail or volatile tokens. Always show `amountMinUSD` (the minimum output after slippage) before submitting.

- **Irreversible** — Once submitted via `send_calls`, swaps and bridges cannot be undone, and cross-chain bridges can take time to settle on the destination chain. Confirm the input amount, expected output, destination chain, and `receiver` with the user before submitting. Never auto-submit; never silently raise slippage. The Permit2 approval in the batch grants Haiku's agent spender allowance to pull the input token — the amount matches the quote (via each `permit2Datas.values.details` entry); verify it before approving.

## Notes

**Haiku chain-name → Base MCP chain string** (IID prefixes differ from `send_calls` chain params). These are the Haiku chains where this plugin can submit the source transaction through Base MCP:

| Haiku IID prefix | chainId | Base MCP `chain` string |
|---|---|---|
| `base` | 8453 | `base` |
| `eth` | 1 | `ethereum` |
| `arb` | 42161 | `arbitrum` |
| `opt` | 10 | `optimism` |
| `poly` | 137 | `polygon` |
| `bsc` | 56 | `bsc` |
| `avax` | 43114 | `avalanche` |

Haiku supports more EVM chains than Base MCP can submit to. Use the full list below for token resolution and destination-chain target IIDs, but do **not** call `send_calls` with a source/input chain that lacks a Base MCP chain string above. If the user's input assets are on an unsupported source chain, stop and direct them to the Haiku web app at `haiku.trade`.

| Haiku IID prefix | chainId | Notes |
|---|---:|---|
| `arb` | 42161 | Base MCP source supported as `arbitrum` |
| `base` | 8453 | Base MCP source supported as `base` |
| `bera` | 80094 | Destination/token-resolution only |
| `bsc` | 56 | Base MCP source supported as `bsc` |
| `sonic` | 146 | Destination/token-resolution only |
| `eth` | 1 | Base MCP source supported as `ethereum` |
| `hype` | 999 | Destination/token-resolution only |
| `poly` | 137 | Base MCP source supported as `polygon` |
| `opt` | 10 | Base MCP source supported as `optimism` |
| `uni` | 130 | Destination/token-resolution only |
| `sei` | 1329 | Destination/token-resolution only |
| `avax` | 43114 | Base MCP source supported as `avalanche` |
| `gnosis` | 100 | Destination/token-resolution only |
| `scroll` | 534352 | Destination/token-resolution only |
| `katana` | 747474 | Destination/token-resolution only |
| `ape` | 33139 | Destination/token-resolution only |
| `worldchain` | 480 | Destination/token-resolution only |
| `plasma` | 9745 | Destination/token-resolution only |
| `lisk` | 1135 | Destination/token-resolution only |
| `bob` | 60808 | Destination/token-resolution only |
| `monad` | 143 | Destination/token-resolution only |
| `megaeth` | 4326 | Destination/token-resolution only |
| `robinhood` | 4663 | Destination/token-resolution only |

Solana and Bitcoin routes exist on Haiku but are out of scope for this Base MCP plugin.

**Permit2 (`IAllowanceTransfer`) model.** Haiku's router pulls input tokens through the canonical Permit2 contract `0x000000000022D473030F116dDEE9F6B43aC78BA3`. The allowance can be set either by an off-chain signed `permit()` **or** by an onchain `approve(token, spender, amount, expiration)` — they set the same allowance the router later consumes via `transferFrom`. Because the default Base MCP wallet is a smart contract (its `sign` output is a variable-length ERC-1271/6492 signature, not a 65-byte EOA sig), this plugin uses the **onchain** `approve` and calls `/solve` without a signature. The `spender` in `permit2Datas.values` is the user's per-account Haiku **agent** address (from `router.calcAgent`), not the router address returned by `/solve`; approve that spender.

**Selectors:** ERC-20 `approve(address,uint256)` = `0x095ea7b3` (already encoded in the quote's `approvals`); Permit2 `approve(address,address,uint160,uint48)` = `0x87517c45`.

**Native token sentinel (ETH/BNB/AVAX/etc.):** `0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee` (same across chains). Native input returns no `approvals` and no Permit2 step; `/solve` returns a non-zero `value`.

**Common token addresses:**

| Token | Chain | Address |
|---|---|---|
| USDC | Base | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |
| WETH | Base | `0x4200000000000000000000000000000000000006` |
| USDC | Arbitrum | `0xaf88d065e77c8cC2239327C5EDb3A432268e5831` |
| USDC | Ethereum | `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48` |
| USDC | Optimism | `0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85` |
| USDC | Polygon | `0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359` |

**Input amounts are human-decimal**, not base units — `10` means 10 USDC. `target_weights` must sum to between `0.99` and `1`. Quotes expire server-side; re-fetch `/quote` if `/solve` can't find the `quoteId`.
