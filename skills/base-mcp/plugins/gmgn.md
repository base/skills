---
title: "GMGN Plugin"
description: "Token swap quotes and on-chain market intelligence for Base via GMGN API. Returns unsigned calldata for send_calls execution."
tags: [swap, quote, defi, market-data, trading]
name: gmgn
version: "1.0.0"
integration: http-api
chains: [base]
requires:
  shell: none
  allowlist: [openapi.gmgn.ai]
  externalMcp: null
  cliPackage: null
auth: api-key
risk: [quote-expiry, slippage]
---

# GMGN Plugin

> [!IMPORTANT]
> Complete the Base MCP onboarding flow defined in `SKILL.md` before calling any GMGN endpoint. The user's wallet address — passed as `from_address` in every quote call — is fetched lazily when needed.

GMGN on Base: token swaps using unsigned calldata returned directly from the quote endpoint, plus trending token market data. Fetch the quote (which includes `data.tx.to`, `data.tx.value`, and `data.tx.data`), handle any approvals in `data.tx.approve_txs`, then execute with `send_calls`.

No additional MCP server is required.

**Chain:** Base mainnet (chainId `8453`)

---

## Authentication

All requests require the `X-APIKEY` header and two query parameters:

| Parameter   | Description |
| ----------- | ----------- |
| `timestamp` | Current Unix timestamp in seconds (valid window ±5 s) |
| `client_id` | Fresh UUID v4 per request (replay protection, 7 s window) |

A public API key is available for all read-only operations:

```
X-APIKEY: gmgn_basesolbscethmonadtron
```

---

## Endpoints

Base URL: `https://openapi.gmgn.ai`

### 1. `GET /v1/trade/quote` — Swap Quote + Calldata

Returns the full unsigned transaction ready for `send_calls`. This is the primary endpoint for executing swaps.

Query parameters:

| Parameter      | Required | Description |
| -------------- | -------- | ----------- |
| `chain`        | Yes      | `base` |
| `from_address` | Yes      | User's wallet address |
| `input_token`  | Yes      | Input token contract address (`0x000...000` for native ETH) |
| `output_token` | Yes      | Output token contract address |
| `input_amount` | Yes      | Input amount in base units (USDC: × 1e6, ETH: × 1e18) |
| `slippage`     | Yes      | Integer 0–100 (e.g., `5` = 5%). See [Slippage Guidance](#slippage-guidance). |
| `timestamp`    | Yes      | Auth: Unix seconds |
| `client_id`    | Yes      | Auth: fresh UUID v4 |

Example request (swap 0.00001 ETH → token):

```
GET https://openapi.gmgn.ai/v1/trade/quote?chain=base&from_address=0xc76d...&input_token=0x0000000000000000000000000000000000000000&output_token=0xc2c1e0b7c401e6217193732272444d928646eba3&input_amount=10000000000000&slippage=5&timestamp=<ts>&client_id=<uuid>
X-APIKEY: gmgn_basesolbscethmonadtron
```

**Response `data` fields:**

Top-level summary fields:

| Field               | Description |
| ------------------- | ----------- |
| `input_token`       | Input token contract address |
| `output_token`      | Output token contract address |
| `input_amount`      | Input amount (base units) |
| `output_amount`     | Expected output amount (base units) |
| `min_output_amount` | Minimum output after slippage (base units) |
| `slippage`          | Slippage percentage |
| `tx`                | Full unsigned transaction object (see below) |

`data.tx` fields (the full unsigned transaction for `send_calls`):

| Field                  | Description |
| ---------------------- | ----------- |
| `tx.to`                | Router contract address — use as `to` in `send_calls` |
| `tx.value`             | Native ETH to send in wei (string) — use as `value` in `send_calls` |
| `tx.data`              | Encoded calldata — use as `data` in `send_calls` |
| `tx.approve_txs`       | Approval transactions to send before the swap (empty for native ETH input) |
| `tx.amount_in`         | Input amount (base units) |
| `tx.amount_out`        | Expected output amount (base units) |
| `tx.amount_min_out`    | Minimum output after slippage (base units) |
| `tx.amount_in_usd`     | Input value in USD |
| `tx.amount_out_usd`    | Expected output value in USD |
| `tx.amount_in_decimals`  | Input token decimals |
| `tx.amount_out_decimals` | Output token decimals |
| `tx.gas_limit`         | Estimated gas limit (string) |
| `tx.deadline`          | Transaction deadline (Unix timestamp) |
| `tx.chain_id`          | Chain ID (`8453` for Base) |

Example response:

```json
{
  "code": 0,
  "data": {
    "input_token": "0x0000000000000000000000000000000000000000",
    "output_token": "0xc2c1e0b7c401e6217193732272444d928646eba3",
    "input_amount": "10000000000000",
    "output_amount": "18500572860253689774247",
    "min_output_amount": "17575544217241005285535",
    "slippage": 5,
    "tx": {
      "chain_id": 8453,
      "to": "0xd8Ba9D1a99Fc21f0ECA24e9b85737c28A194a4E2",
      "from_address": "0xc76d1aabf25142f15010e992cb07bb81a8b5ae63",
      "slippage": 5,
      "value": "10000000000000",
      "amount_in": "10000000000000",
      "amount_out": "18500572860253689774247",
      "amount_min_out": "17575544217241005285535",
      "input_token_address": "0x0000000000000000000000000000000000000000",
      "output_token_address": "0xc2c1e0b7c401e6217193732272444d928646eba3",
      "token_in_usd_price": "1671.39",
      "token_out_usd_price": "0.00000088214833000000",
      "amount_in_usd": "0.0167139",
      "amount_out_usd": "0.01632024945271611581069006805751",
      "amount_in_decimals": 18,
      "amount_out_decimals": 18,
      "gas_limit": "922086",
      "data": "0xeffbec13...",
      "approve_txs": [],
      "deadline": 1781266225
    }
  }
}
```

Convert to human-readable: `data.tx.amount_out / 10^data.tx.amount_out_decimals`, `data.tx.amount_min_out / 10^data.tx.amount_out_decimals`.

---

### 2. `GET /v1/trade/gas_price` — Gas Price

Returns current recommended gas price tiers for Base.

Query parameters:

| Parameter   | Required | Description |
| ----------- | -------- | ----------- |
| `chain`     | Yes      | `base` |
| `timestamp` | Yes      | Auth: Unix seconds |
| `client_id` | Yes      | Auth: fresh UUID v4 |

Key response fields under `data`:

| Field                    | Description |
| ------------------------ | ----------- |
| `low` / `average` / `high` | Gas price tiers in wei |
| `low_estimate_time` / `average_estimate_time` / `high_estimate_time` | Estimated confirmation time (seconds) |
| `suggest_base_fee`       | Suggested EIP-1559 base fee (wei) |
| `average_prio_fee`       | Average priority fee (wei) |
| `native_token_usd_price` | ETH price in USD |

---

### 3. `GET /v1/market/rank` — Trending Tokens

Returns top trending tokens on Base ranked by swap activity.

Query parameters:

| Parameter   | Required | Default   | Description |
| ----------- | -------- | --------- | ----------- |
| `chain`     | Yes      | —         | `base` |
| `interval`  | No       | `1h`      | Time window: `1m` / `5m` / `1h` / `6h` / `24h` |
| `limit`     | No       | `10`      | Number of results (1–100) |
| `order_by`  | No       | `default` | Sort field: `default` / `swaps` / `volume` / `marketcap` / `holder_count` / `change1h` |
| `direction` | No       | `desc`    | `asc` / `desc` |
| `filters`   | No       | `not_honeypot,verified,renounced` | Safety filters (repeatable): `not_honeypot`, `verified`, `renounced`, `has_social`, `not_wash_trading` |
| `timestamp` | Yes      | —         | Auth: Unix seconds |
| `client_id` | Yes      | —         | Auth: fresh UUID v4 |

Response: `data.rank` array with token address, symbol, price (USD), market cap, 1h/24h price change, swap count, volume, holder count, and liquidity.

---

## Orchestration

### Swap flow: "Swap 0.00001 ETH for token X on Base"

```text
1. get_wallets -> user address (from_address)

2. web_request GET /v1/trade/quote
     ?chain=base
     &from_address=<address>
     &input_token=0x0000000000000000000000000000000000000000   (native ETH)
     &output_token=<token_address>
     &input_amount=<amount_in_wei>
     &slippage=5
     &timestamp=<ts>&client_id=<uuid>
   Headers: X-APIKEY: gmgn_basesolbscethmonadtron

3. Present quote to user:
     Input:           data.tx.amount_in / 10^data.tx.amount_in_decimals  (+ data.tx.amount_in_usd)
     Expected output: data.tx.amount_out / 10^data.tx.amount_out_decimals (+ data.tx.amount_out_usd)
     Minimum output:  data.tx.amount_min_out / 10^data.tx.amount_out_decimals
     Check slippage against Slippage Guidance table before proceeding.

4. Confirm with user before submitting.

5. Build calls from the quote response:
     approvalCalls = data.tx.approve_txs.map(t => ({ to: t.to, value: t.value ?? "0x0", data: t.data }))
     swapCall      = { to: data.tx.to, value: data.tx.value, data: data.tx.data }
     calls         = [...approvalCalls, swapCall]

6. send_calls("base", calls)

7. get_request_status only after the user acts on the approval link.
```

### Swap `send_calls` body

```json
{
  "chain": "base",
  "calls": [
    { "to": "<approve_tx.to>", "value": "0x0", "data": "<approve_tx.data>" },
    { "to": "<data.tx.to>", "value": "<data.tx.value>", "data": "<data.tx.data>" }
  ]
}
```

If `data.tx.approve_txs` is empty (native ETH input), omit the approval call and send only the swap call.

### Market discovery flow: "What tokens are trending on Base?"

```text
1. web_request GET /v1/market/rank?chain=base&interval=1h&limit=10&order_by=volume&timestamp=<ts>&client_id=<uuid>
   Headers: X-APIKEY: gmgn_basesolbscethmonadtron
2. Present the top tokens: name, symbol, price, 1h change, volume, holder count
3. Optionally follow up with GET /v1/trade/quote for any token the user wants to buy
```

---

## Example Prompts

**Swap 0.00001 ETH for a token on Base**
1. `get_wallets` → address.
2. `web_request GET /v1/trade/quote` with `input_token=0x000...000` (native ETH), `input_amount=10000000000000`, target token as `output_token`, `slippage=5`.
3. Display expected and minimum output, USD values.
4. Build approval + swap calls from `data.tx.approve_txs` and `data.tx.to/value/data`.
5. `send_calls("base", [...approvalCalls, swapCall])`.

**Swap 100 USDC for ETH on Base**
1. `get_wallets` → address.
2. `web_request GET /v1/trade/quote` with `input_token=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` (USDC), `input_amount=100000000` (100 × 1e6), `output_token=0x0000000000000000000000000000000000000000`.
3. USDC requires an ERC-20 approval — include `data.tx.approve_txs[0]` before the swap call.
4. `send_calls("base", calls)`.

**Show trending tokens on Base**
1. `web_request GET /v1/market/rank?chain=base&interval=1h&limit=10&order_by=volume`.
2. Present token list with price, change, and volume.

**What's the price to buy token X with 50 USDC?**
1. `get_wallets` → address.
2. `web_request GET /v1/trade/quote` with USDC as input, target token as output, `input_amount=50000000`.
3. Show `data.tx.amount_out_usd`, effective price (`data.tx.amount_in_usd / (data.tx.amount_out / 10^data.tx.amount_out_decimals)`), and slippage impact.

---

## Slippage Guidance

| Tolerance      | Level     | Action |
| -------------- | --------- | ------ |
| ≤ 1%           | Normal    | Proceed. |
| > 1% and ≤ 5%  | Elevated  | Mention the value and ask the user to confirm. |
| > 5% and ≤ 20% | High      | Warn that the trade can fill significantly below quote and is a likely sandwich target. Require explicit confirmation. |
| > 20%          | Very high | Strongly warn; do not submit without the user re-confirming the exact number. |

For meme tokens with low liquidity, higher slippage (10–20%) is common — always warn and confirm before proceeding.

---

## Notes

- Native ETH address: `0x0000000000000000000000000000000000000000`
- USDC on Base: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- WETH on Base: `0x4200000000000000000000000000000000000006`
- Token amounts are in base units. Use `data.tx.amount_in_decimals` / `data.tx.amount_out_decimals` from the quote response to convert to human-readable values.
- `data.tx.data` is unsigned calldata — pass it directly to `send_calls`; never sign or modify it.
- Quotes expire at `data.tx.deadline` (Unix timestamp). Re-fetch if the user has not confirmed within ~30 seconds.
- `data.tx.approve_txs` handles ERC-20 allowances. It is empty when the input is native ETH or when a sufficient allowance already exists.
- `timestamp` must be within ±5 seconds of server time. `client_id` must be a fresh UUID per request.
- Use `chain: "base"` (not numeric chain ID) with `send_calls`.
