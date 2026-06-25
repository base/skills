---
title: "OpenOcean Plugin"
description: "DEX aggregation on OpenOcean V4 via HTTP API -> send_calls on Base chain."
tags: [dex, swap, liquidity, trading]
name: openocean
version: 0.2.0
integration: http-api
chains: [base]
requires:
  shell: none
  allowlist: [open-api.openocean.finance]
  externalMcp: null
  cliPackage: null
auth: none
risk: [slippage]
---

# OpenOcean Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before calling any OpenOcean endpoint. There are no per-session authentication prerequisites; all endpoints are publicly accessible.

OpenOcean is a leading DEX aggregator protocol. This plugin routes token swaps on the Base chain by fetching quotes and building unsigned transaction calldata via the OpenOcean V4 HTTP API. Transactions are then submitted to the blockchain using the Base MCP `send_calls` tool.

No additional MCP server is required — everything goes through `web_request` + `send_calls`.

**Prerequisite:** `open-api.openocean.finance` must be in the MCP server's `web_request` allowlist. If requests to this hostname are rejected, inform the user.

**Chain:** Base mainnet only (`chainId` `8453`, Base MCP chain string `"base"`).

---

## Surface Routing

| Capability | Claude Code / Codex / Cursor | Claude.ai / ChatGPT |
|---|---|---|
| **Read** (Quote, Allowance, Token List, Gas Price) | Harness HTTP tool (direct fetch) | Base MCP `web_request` |
| **Write** (Approve, Swap) | `send_calls` (EIP-5792) | `send_calls` (EIP-5792) |

OpenOcean is a public HTTP API requiring no shell or external MCP. On shell-less or chat-only surfaces, the agent uses the Base MCP `web_request` tool to access public endpoints on the allowlist host (`open-api.openocean.finance`). For transaction submissions, it maps the unsigned calldata to the Base MCP `send_calls` tool.

---

## Endpoints

Base URL: `https://open-api.openocean.finance/v4/8453`

### `GET /v4/8453/quote`

Quote the price of a specific trading pair on Base.

**Query Parameters:**
- `inTokenAddress` (string, required): Input token address. Use `0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE` for native ETH.
- `outTokenAddress` (string, required): Output token address.
- `amountDecimals` (string, required): Input token amount including token decimals (e.g. `1000000` for 1 USDC).
- `gasPriceDecimals` (string, required): Gas price in WEI (e.g. `1000000000` for 1 GWEI).
- `slippage` (string, optional): Slip tolerance in percent (e.g. `1` for 1%). Range: 0.05 to 50. Default is `1`.
- `disabledDexIds` (string, optional): DEX index values to disable, separated by commas.
- `enabledDexIds` (string, optional): DEX index values to enable, separated by commas.

**Response:**
```json
{
  "code": 200,
  "data": {
    "inToken": {
      "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
      "decimals": 6,
      "symbol": "USDC",
      "name": "USD Coin",
      "usd": "0.999955",
      "volume": 4.99
    },
    "outToken": {
      "address": "0x820C137fa70C8691f0e44Dc420a5e53c168921Dc",
      "decimals": 18,
      "symbol": "USDS",
      "name": "USDS Stablecoin",
      "usd": "0.998546",
      "volume": 4.99273
    },
    "inAmount": "5000000",
    "outAmount": "4993921938787056372",
    "estimatedGas": "129211",
    "dexes": [
      { "dexIndex": 0, "dexCode": "Pancake", "swapAmount": "4993921938787056372" }
    ],
    "path": {
      "from": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
      "to": "0x820C137fa70C8691f0e44Dc420a5e53c168921Dc",
      "parts": 10
    },
    "save": -0.0018,
    "price_impact": "0.01%",
    "exchange": "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64"
  }
}
```

- `exchange`: The router contract address that needs token approval.

---

### `GET /v4/8453/swap`

Build the swap transaction body for Base.

**Query Parameters:**
- Same as `/quote`, but note that **`slippage` is required** for `/swap`.
- `account` (string, required): The user's wallet address.
- `slippage` (string, required): Slip tolerance in percent (e.g. `1` for 1%). Range: 0.05 to 50.
- `referrer` (string, optional): Partner address.
- `referrerFee` (number, optional): Partner fee percentage.
- `minOutput` (string, optional): Minimum target tokens without decimals (or decimals).
- `sender` (string, optional): Caller address. If set, `account` behaves as the receiver of the swapped tokens.

**Response:**
```json
{
  "code": 200,
  "data": {
    "inToken": { "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "decimals": 6, "symbol": "USDC", "name": "USD Coin" },
    "outToken": { "address": "0x820C137fa70C8691f0e44Dc420a5e53c168921Dc", "decimals": 18, "symbol": "USDS", "name": "USDS Stablecoin" },
    "inAmount": "5000000",
    "outAmount": "4993921938787056372",
    "estimatedGas": 516812,
    "minOutAmount": "4943982719399185808",
    "from": "0x9116780aEf4B376499358fa7dEeC00cCF64fA801",
    "to": "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",
    "value": "0",
    "gasPrice": "1000000000",
    "data": "0x90411a32...",
    "chainId": 8453,
    "price_impact": "0.01%"
  }
}
```

- `to`: The OpenOcean router address (the spender address).
- `value`: Native currency amount to send with transaction (non-zero for native ETH swaps).
- `data`: Hex-encoded calldata for the transaction.

---

### `GET /v4/8453/allowance`

Check token allowance granted to OpenOcean's router on Base.

**Query Parameters:**
- `account` (string, required): Wallet address.
- `inTokenAddress` (string, required): Token contract address.

**Response:**
```json
{
  "code": 200,
  "data": [
    {
      "symbol": "USDC",
      "allowance": "79228162514.26434",
      "raw": "79228162514264340"
    }
  ]
}
```

---

### `GET /v4/8453/tokenList`

Get the list of supported tokens on Base.

---

### `GET /v4/8453/gasPrice`

Get current gas prices on Base.

**Response:**
```json
{
  "code": 200,
  "data": {
    "standard": 3000000000,
    "fast": 3000000000,
    "instant": 3000000000
  },
  "without_decimals": {
    "standard": "3",
    "fast": "3",
    "instant": "3"
  }
}
```

---

## Orchestration

```
1. get_wallets -> walletAddress
2. web_request GET /v4/8453/gasPrice -> get gasPriceDecimals (standard gasPrice in WEI)
3. web_request GET /v4/8453/allowance?account=<walletAddress>&inTokenAddress=<inTokenAddress>
4. Compare allowance.raw with target swap amountDecimals:
   a. If allowance.raw < amountDecimals:
      - Construct ERC-20 approve calldata: spender = router (from quote exchange or swap to), amount = max uint256
      - Add approve call to calls array
5. web_request GET /v4/8453/swap with account, amounts, slippage -> get swap tx (to, value, data)
6. Add swap call to calls array
7. send_calls(chain="base", calls) -> approvalUrl + requestId
8. Open the approvalUrl and poll get_request_status(requestId)
```

### Pre-submit Validations
- Native ETH (`0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE`) does not require allowance checks or approval transactions.
- Always require user confirmation before submitting any transaction, showing the route, expected output, and price impact.

---

## Submission

Target Tool: `send_calls`

Normalizes transaction objects from the `/swap` API and custom ERC-20 approvals into standard EIP-5792 calls on the Base chain.

### Custom ERC-20 Approval Call Construction
Because OpenOcean does not provide a transaction builder for approvals, the agent must construct the approval calldata directly when a token allowance check fails.

- **Approve Selector**: `0x095ea7b3`
- **Calldata encoding**: `0x095ea7b3` + `spender` (padded to 32 bytes) + `amount` (padded to 32 bytes).
- **Spender**: OpenOcean router address (value of `exchange` from `/quote` or `to` from `/swap`).
- **Amount**: Max uint256 (`ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff`) or exact swap amount.

### Batch call mapping
For approval + swap:
```json
{
  "chain": "base",
  "calls": [
    {
      "to": "<inTokenAddress>",
      "value": "0x0",
      "data": "0x095ea7b3000000000000000000000000<spender padded to 32 bytes><amount padded to 32 bytes>"
    },
    {
      "to": "<swap.to>",
      "value": "<swap.value>",
      "data": "<swap.data>"
    }
  ]
}
```

For swap only (native gas token, or if allowance is already sufficient):
```json
{
  "chain": "base",
  "calls": [
    {
      "to": "<swap.to>",
      "value": "<swap.value>",
      "data": "<swap.data>"
    }
  ]
}
```

---

## Example Prompts

**Swap 10 USDC to WETH on Base**
1. `get_wallets` -> wallet address `0x911678...`.
2. `web_request` GET `https://open-api.openocean.finance/v4/8453/gasPrice` -> standard gas price is `1000000` WEI.
3. `web_request` GET `https://open-api.openocean.finance/v4/8453/allowance?account=0x911678...&inTokenAddress=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` (USDC).
4. `web_request` GET `https://open-api.openocean.finance/v4/8453/quote?inTokenAddress=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913&outTokenAddress=0x4200000000000000000000000000000000000006&amountDecimals=10000000&gasPriceDecimals=1000000`.
5. Compare allowance raw. If insufficient, build approval call to spender `0x6352a56caadC4F1E25CD6c75970Fa768A3304e64` (exchange field).
6. `web_request` GET `https://open-api.openocean.finance/v4/8453/swap?inTokenAddress=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913&outTokenAddress=0x4200000000000000000000000000000000000006&amountDecimals=10000000&gasPriceDecimals=1000000&account=0x911678...`.
7. `send_calls` with chain `"base"`, batching the approval and swap transactions.
8. Present the `approvalUrl` to the user and poll `get_request_status`.

**Swap 0.1 ETH to USDC on Base**
1. `get_wallets` -> wallet address.
2. `web_request` GET `https://open-api.openocean.finance/v4/8453/gasPrice` -> gasPrice = `1000000` WEI.
3. No allowance check needed since input token is native ETH (`0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE`).
4. `web_request` GET `https://open-api.openocean.finance/v4/8453/swap?inTokenAddress=0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE&outTokenAddress=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913&amountDecimals=100000000000000000&gasPriceDecimals=1000000&account=0x911678...`.
5. `send_calls` with chain `"base"`, containing only the swap call with `value` equal to the ETH amount.
6. Present approval URL and poll.

---

## Risks & Warnings

- **Slippage**: Swaps can fill worse than quoted if market prices move. Before submitting swaps with elevated slippage, warn the user and require confirmation:
  
  | Slippage | Level | Action |
  |---|---|---|
  | ≤ 1% | Normal | Proceed. |
  | > 1% and ≤ 5% | Elevated | Mention value and ask user to confirm. |
  | > 5% and ≤ 20% | High | Warn of frontrunning risk. Require explicit confirmation. |
  | > 20% | Very high | Strong warning. Do not submit without user re-confirming the exact amount. |

- **Gas Limit Refinement**: OpenOcean returns `estimatedGas` as a reference. If the user's execution environment allows, run `eth_estimateGas` or add a 25%-50% buffer to the gas limit to avoid out-of-gas reverts.

---

## Notes

### Base Token Addresses
- Native ETH pseudo-token: `0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE`
- WETH: `0x4200000000000000000000000000000000000006`
- USDC: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- USDS: `0x820C137fa70C8691f0e44Dc420a5e53c168921Dc`
