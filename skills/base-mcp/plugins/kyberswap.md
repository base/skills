---
title: "KyberSwap Plugin"
description: "Skill plugin for swapping tokens on KyberSwap through Base MCP — best-rate aggregation across 50+ DEXes on 7 chains."
---

# KyberSwap Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before calling any KyberSwap endpoint. The user's wallet address — passed as `sender` in every swap call — is fetched lazily when needed.

KyberSwap is a DEX aggregator that routes trades across 50+ liquidity sources (Uniswap V2/V3/V4, Curve, Balancer, and others) to find the best execution price. Use it when the user wants the best rate across all available liquidity — not just a single protocol's pools.

No additional MCP server is required.

**Prerequisite:** `aggregator-api.kyberswap.com` and `token-api.kyberswap.com` must be in the MCP server's `web_request` allowlist. If requests are rejected by the allowlist, inform the user.

**Router address (same on all supported chains):** `0x6131B5fae19EA4f9D964eAc0408E4408b66337b5`

---

## Swap Flow

Base URL: `https://aggregator-api.kyberswap.com/{chain}`

Chain slugs: `base` · `ethereum` · `arbitrum` · `optimism` · `polygon` · `bsc` · `avalanche`

```
GET  /api/v1/routes       →  best route + quote (read-only)
POST /api/v1/route/build  →  unsigned swap transaction calldata
```

### 1. `GET /api/v1/routes`

```
https://aggregator-api.kyberswap.com/{chain}/api/v1/routes
  ?tokenIn={address}
  &tokenOut={address}
  &amountIn={amountInWei}
  &to={walletAddress}
  &slippageTolerance={bps}
  &source=base-mcp
```

| Param | Required | Notes |
|---|---|---|
| `tokenIn` | ✅ | Token address. Use `0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE` for native (ETH, BNB, MATIC, etc.) |
| `tokenOut` | ✅ | Token address |
| `amountIn` | ✅ | Integer string in base units — no decimals, no scientific notation |
| `to` | recommended | Recipient wallet address |
| `slippageTolerance` | recommended | Basis points (50 = 0.5%). See [Slippage Warnings](#slippage-warnings) |
| `source` | recommended | Pass `base-mcp` for attribution |

Response shape:

```json
{
  "data": {
    "routeSummary": { ... },
    "routerAddress": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
    "amountIn": "...",
    "amountInUsd": "...",
    "amountOut": "...",
    "amountOutUsd": "...",
    "gas": "...",
    "gasUsd": "..."
  }
}
```

Keep the **complete `routeSummary` object** — it is required verbatim for the build step.

### 2. `POST /api/v1/route/build`

```
https://aggregator-api.kyberswap.com/{chain}/api/v1/route/build
```

Request body:

```json
{
  "routeSummary": { ... },
  "sender": "<walletAddress>",
  "recipient": "<walletAddress>",
  "slippageTolerance": 50,
  "deadline": "<unix_timestamp + 1200>",
  "source": "base-mcp"
}
```

Pass `routeSummary` exactly as returned from the GET step — do not modify or truncate it.

Response shape:

```json
{
  "data": {
    "amountIn": "...",
    "amountOut": "...",
    "gas": "...",
    "transactionValue": "0x0",
    "routerAddress": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
    "encodedSwapData": "0x..."
  }
}
```

### 3. ERC-20 Approval Check

Before calling send_calls, check whether the router has enough allowance for `tokenIn`:

- **Native tokens** (ETH, BNB, MATIC, AVAX, etc.): no approval needed — proceed directly to send_calls.
- **ERC-20 tokens**: if current allowance < `amountIn`, include a standard ERC-20 approve call in the batch.

Approval call:

```json
{
  "to": "<tokenIn contract address>",
  "value": "0x0",
  "data": "<approve(address,uint256) selector + ABI-encoded (router, amountInWei)>"
}
```

`approve` selector: `0x095ea7b3`

### 4. `send_calls`

Batch approval (if needed) and swap into a single user approval:

```json
{
  "chain": "base",
  "calls": [
    { "to": "<tokenIn address>", "value": "0x0", "data": "<approval calldata>" },
    { "to": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5", "value": "<transactionValue>", "data": "<encodedSwapData>" }
  ]
}
```

For native token input (no approval):

```json
{
  "chain": "base",
  "calls": [
    { "to": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5", "value": "<transactionValue>", "data": "<encodedSwapData>" }
  ]
}
```

Use chain name strings (`base`, `ethereum`, `arbitrum`, `optimism`, `polygon`, `bsc`, `avalanche`) — not numeric chainIds.

### Swap Orchestration

```
1. get_wallets → walletAddress
2. web_request GET /api/v1/routes → routeSummary, amountOut, gasUsd
3. Check approval:
     native token? → skip
     ERC-20 allowance ≥ amountIn? → skip
     otherwise → prepare approval calldata
4. web_request POST /api/v1/route/build → encodedSwapData, transactionValue
5. send_calls(chain, [approval_call?, swap_call])
6. Open approvalUrl if requested; do not approve unless the user explicitly asks
7. get_request_status only after the user acts
```

---

## Token Resolution

For common tokens on Base:

| Token | Address |
|---|---|
| ETH (native) | `0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE` |
| USDC | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |
| WETH | `0x4200000000000000000000000000000000000006` |
| DAI | `0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb` |
| cbBTC | `0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf` |

For unknown tokens, resolve via the KyberSwap token API (GET):

```
web_request: https://token-api.kyberswap.com/api/v1/public/tokens?chainIds={chainId}&name={symbol}&isWhitelisted=true
```

Pick the result with exact `symbol` match and highest `marketCap`.

Chain IDs: base=8453, ethereum=1, arbitrum=42161, optimism=10, polygon=137, bsc=56, avalanche=43114

---

## Example Prompts

**Swap 100 USDC to ETH on Base**

1. `get_wallets` → address
2. `web_request GET /api/v1/routes` tokenIn=`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`, tokenOut=`0xEeee...eEEE`, amountIn=`100000000`, chain=`base`
3. USDC is ERC-20: prepare approval calldata for router
4. `web_request POST /api/v1/route/build` → encodedSwapData
5. `send_calls` batching approval + swap

**Swap 0.1 ETH to USDC on Arbitrum**

1. `get_wallets` → address
2. `web_request GET /api/v1/routes` tokenIn=`0xEeee...eEEE`, tokenOut=USDC on arbitrum, amountIn=`100000000000000000`, chain=`arbitrum`
3. Native token: no approval needed
4. `web_request POST /api/v1/route/build` → encodedSwapData, transactionValue (non-zero hex)
5. `send_calls` with value=transactionValue

---

## Slippage Warnings

| Tolerance | Level | Action |
|---|---|---|
| ≤ 50 bps (0.5%) | Normal | Proceed. |
| > 50 and ≤ 200 bps | Elevated | Mention the value and ask the user to confirm. |
| > 200 and ≤ 500 bps | High | Warn that the trade can fill significantly below quote and is a likely sandwich target. Require explicit confirmation. |
| > 500 bps | Very high | Strongly warn; do not submit without the user re-confirming the exact number. |

If the user does not specify slippage: use `50` bps for common pairs (ETH/USDC, WBTC/ETH), `100` bps for long-tail or volatile tokens.

If the build step returns error code `4227` with "return amount is not enough", the price moved since the route was fetched — re-fetch the route and retry before adjusting slippage.

---

## Notes

- Native token sentinel (ETH/BNB/MATIC/AVAX/etc.): `0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE`
- Router address is the same on all chains: `0x6131B5fae19EA4f9D964eAc0408E4408b66337b5`
- `transactionValue` from the build response is a hex wei string — pass it directly as `value` in send_calls. It is non-zero only for native token input.
- Routes expire in ~30 seconds. If the build step fails with "return amount not enough", re-fetch the route and retry.
- USDT on Ethereum mainnet requires setting allowance to 0 before a new non-zero approval. If approval fails, suggest revoking first.
- KyberSwap splits trades across multiple DEX pools when beneficial — the `routeSummary` may describe a multi-hop or split route. Pass it as-is to the build endpoint.
