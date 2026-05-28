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

## Orchestration Pattern

```
web_request GET /api/v1/routes
  → { data: { routeSummary, routerAddress, amountOut, amountOutUsd, gasUsd } }
      ↓
web_request POST /api/v1/route/build
  → { data: { encodedSwapData, transactionValue, routerAddress } }
      ↓
send_calls(chain, [approval_call?, swap_call])
  → approvalUrl + requestId
      ↓
User approves at the returned approval URL
      ↓
get_request_status(requestId) → confirmed
```

Include an ERC-20 approval call before the swap whenever `tokenIn` is not a native token. Batch both calls together so the user approves once.

---

## Swap Flow

Base URL: `https://aggregator-api.kyberswap.com/{chain}`

Chain slugs: `base` · `ethereum` · `arbitrum` · `optimism` · `polygon` · `bsc` · `avalanche`

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
| `amountIn` | ✅ | Amount in base units — plain integer string, no decimals, no scientific notation. Multiply the human amount by `10^decimals`: 1 ETH = `1000000000000000000`, 100 USDC = `100000000` |
| `to` | recommended | Recipient wallet address |
| `slippageTolerance` | recommended | Basis points (50 = 0.5%). See [Slippage Warnings](#slippage-warnings) |
| `source` | recommended | Pass `base-mcp` for attribution |

Response shape:

```json
{
  "data": {
    "routeSummary": { "...": "keep this object verbatim for the build step" },
    "routerAddress": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
    "amountIn": "100000000",
    "amountInUsd": "100.00",
    "amountOut": "38650000000000000",
    "amountOutUsd": "99.71",
    "gas": "300000",
    "gasUsd": "0.29"
  }
}
```

Keep the **complete `routeSummary` object** exactly as returned — it is required verbatim in the build step body.

### 2. `POST /api/v1/route/build`

Use `web_request` with `method: POST`:

```json
{
  "url": "https://aggregator-api.kyberswap.com/{chain}/api/v1/route/build",
  "method": "POST",
  "headers": { "content-type": "application/json", "x-client-id": "base-mcp" },
  "body": {
    "routeSummary": { "...": "complete object from GET response" },
    "sender": "<walletAddress>",
    "recipient": "<walletAddress>",
    "slippageTolerance": 50,
    "deadline": "<current unix timestamp + 1200>",
    "source": "base-mcp"
  }
}
```

Do not modify or truncate `routeSummary`. Routes expire in ~30 seconds — if this step fails with "return amount is not enough", re-fetch the route and retry.

Response shape:

```json
{
  "data": {
    "amountIn": "100000000",
    "amountOut": "38650000000000000",
    "gas": "300000",
    "transactionValue": "0x0",
    "routerAddress": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
    "encodedSwapData": "0x..."
  }
}
```

`transactionValue` is a hex wei string — pass it directly as `value` in the swap call. It is non-zero only for native token input (e.g. `"0xde0b6b3a7640000"` for 1 ETH).

### 3. ERC-20 Approval

For ERC-20 `tokenIn`, always include a standard `approve` call before the swap. Skip this step only for native tokens (ETH, BNB, MATIC, AVAX, etc.).

Function: `approve(address spender, uint256 amount)`
- `spender`: `0x6131B5fae19EA4f9D964eAc0408E4408b66337b5`
- `amount`: `amountIn` value from the GET routes response (exact amount, in base units)

Calldata encoding:
```
selector:  0x095ea7b3
spender:   000000000000000000000000 + {router without 0x}
amount:    {amountIn as 32-byte hex, left-padded with zeros}

Example (approve 100 USDC = 100000000):
0x095ea7b3
  0000000000000000000000006131b5fae19ea4f9d964eac0408e4408b66337b5
  0000000000000000000000000000000000000000000000000000000005f5e100
```

Approval call shape:
```json
{ "to": "<tokenIn address>", "value": "0x0", "data": "<approve calldata>" }
```

**USDT on Ethereum mainnet**: if the existing allowance is non-zero, the approve call will revert. Send a zero-approval first (`amount = 0x0...0`), then send the real approval.

### 4. `send_calls`

For ERC-20 `tokenIn` — batch approval + swap:

```json
{
  "chain": "base",
  "calls": [
    { "to": "<tokenIn address>", "value": "0x0", "data": "<approve calldata>" },
    { "to": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5", "value": "<transactionValue>", "data": "<encodedSwapData>" }
  ]
}
```

For native `tokenIn` — swap only:

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
3. web_request POST /api/v1/route/build → encodedSwapData, transactionValue
4. Build calls array:
     native tokenIn  → [swap_call]
     ERC-20 tokenIn  → [approval_call, swap_call]
5. send_calls(chain, calls)
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

For unknown tokens, resolve via the KyberSwap token API:

```
web_request: https://token-api.kyberswap.com/api/v1/public/tokens?chainIds={chainId}&name={symbol}&isWhitelisted=true
```

Pick the result with exact `symbol` match and highest `marketCap`. If no whitelisted match, retry without `isWhitelisted`.

Chain IDs: base=8453, ethereum=1, arbitrum=42161, optimism=10, polygon=137, bsc=56, avalanche=43114

---

## Example Prompts

**Swap 100 USDC to ETH on Base**

1. `get_wallets` → address
2. `web_request GET /api/v1/routes` — tokenIn=`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` (USDC, 6 dec), tokenOut=`0xEeee...eEEE`, amountIn=`100000000`, chain=`base`
3. `web_request POST /api/v1/route/build` → encodedSwapData, transactionValue=`0x0`
4. Build approval calldata: approve router to spend `100000000` USDC
5. `send_calls("base", [approval_call, swap_call])`

**Swap 0.1 ETH to USDC on Arbitrum**

1. `get_wallets` → address
2. `web_request GET /api/v1/routes` — tokenIn=`0xEeee...eEEE`, tokenOut=USDC on arbitrum=`0xaf88d065e77c8cC2239327C5EDb3A432268e5831`, amountIn=`100000000000000000`, chain=`arbitrum`
3. `web_request POST /api/v1/route/build` → encodedSwapData, transactionValue=`0xde0b6b3a7640000` (non-zero, native input)
4. No approval needed for native ETH
5. `send_calls("arbitrum", [swap_call])` with value=transactionValue

---

## Slippage Warnings

| Tolerance | Level | Action |
|---|---|---|
| ≤ 1% (100 bps) | Normal | Proceed. |
| > 1% and ≤ 5% | Elevated | Mention the value and ask the user to confirm. |
| > 5% and ≤ 20% | High | Warn that the trade can fill significantly below quote and is a likely sandwich target. Require explicit confirmation. |
| > 20% | Very high | Strongly warn; do not submit without the user re-confirming the exact number. |

If the user does not specify slippage, use `50` bps for common pairs (ETH/USDC, WBTC/ETH) and `100` bps for long-tail or volatile tokens. Always pass an explicit value — the API defaults to 0 bps if `slippageTolerance` is omitted, which will cause most trades to fail.

---

## Notes

- Native token sentinel (ETH/BNB/MATIC/AVAX/etc.): `0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE`
- Router address is the same on all chains: `0x6131B5fae19EA4f9D964eAc0408E4408b66337b5`
- KyberSwap splits trades across multiple pools when beneficial — `routeSummary` may describe a multi-hop or split route. Pass it as-is; do not modify it.
- USDC on Base: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` · WETH on Base: `0x4200000000000000000000000000000000000006`
