---
title: "Fibrous Plugin"
description: "Skill plugin reference for swapping on Base via the Fibrous Finance aggregator. Routes across PancakeSwap, Uniswap V3/V4, Tessera, and other Base DEXs, then submits via Base MCP send_calls."
---

# Fibrous Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before calling any Fibrous endpoint. The user's wallet address — used as `destination` in calldata — is fetched lazily when needed.

Fibrous is a DEX aggregator on Base, Starknet, and other chains. This plugin uses the Fibrous v2 HTTP API to get a route and structured swap parameters, ABI-encodes the router's `swap()` call locally, and submits the result through Base MCP `send_calls`.

No additional MCP server is required.

**Chain:** Base mainnet (`chainId` `8453`, Base MCP chain string `"base"`).

**Prerequisite:** `api.fibrous.finance` must be in the MCP server's `web_request` allowlist. If requests are rejected, inform the user. ABI-encoding requires a CLI harness with `node` + `ethers` available (this plugin ships a helper script and the router ABI under `fibrous-scripts/`).

---

## Swap Flow

The Fibrous router on Base is `0x274602a953847d807231d2370072f5f4e4594b44`. The flow is:

```text
GET  /base/v2/route        ->  read-only quote with route legs
POST /base/v2/calldata     ->  structured RouteParam + SwapParams[] (NOT pre-encoded)
ABI-encode swap(route, swap_parameters) with routerAbi.json
ERC-20 approve to router (skip for native ETH input)
send_calls(approve + swap, value = amount_in for native ETH else 0x0)
```

The API does **not** return pre-encoded calldata like Uniswap does — it returns the structured tuples that the router's `swap()` function expects. You must ABI-encode them yourself. Use the bundled helper.

### Native ETH

Use the standard EVM native sentinel `0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE` for `tokenInAddress` / `tokenOutAddress` when native ETH is involved. With native ETH input, skip the ERC-20 approval and set `value` on the swap call to `amount_in` (hex).

---

## 1. `GET /base/v2/route`

```text
https://api.fibrous.finance/base/v2/route
  ?amount=<base units string>
  &tokenInAddress=<address>
  &tokenOutAddress=<address>
```

Optional: `slippage`, `direct=true`, `excludeProtocols=<csv>`, plus integrator params (`integratorAddress`, `integratorFeePercentageBps`, `integratorSurplusPercentageBps`) which require an `X-API-Key` header.

Response includes `inputAmount`, `outputAmount`, `route[]` (legs), `routeSwapType`, plus a full token info object. Keep the full body — `/calldata` consumes it verbatim.

## 2. `POST /base/v2/calldata`

```json
{
  "route": { "...full /route response..." },
  "slippage": 0.5,
  "destination": "<wallet address>"
}
```

Response shape:

```json
{
  "route": {
    "token_in": "...",
    "token_out": "...",
    "amount_in": "...",
    "amount_out": "...",
    "min_received": "...",
    "destination": "...",
    "swap_type": 0
  },
  "swap_parameters": [
    {
      "token_in": "...",
      "token_out": "...",
      "rate": "...",
      "protocol_id": "...",
      "pool_address": "...",
      "swap_type": 0,
      "extra_data": "0x..."
    }
  ],
  "router_address": "0x274602a953847d807231d2370072f5f4e4594b44"
}
```

Some SDK / client envelopes nest the swap params under `calldata.swap_parameters` — accept either shape.

## 3. ABI-encode `swap(route, swap_parameters)`

The router function signature is:

```solidity
function swap(
  (address token_in, address token_out, uint256 amount_in, uint256 amount_out,
   uint256 min_received, address destination, uint8 swap_type) route,
  (address token_in, address token_out, uint32 rate, int24 protocol_id,
   address pool_address, uint8 swap_type, bytes extra_data)[] swap_parameters
) external payable returns (uint256);
```

Fetch the router ABI from Fibrous's official ABI repo and encode against it. The function selector is `0x8619b04e`.

```bash
curl -sL https://raw.githubusercontent.com/Fibrous-Finance/router-contract-abi/main/routerAbi.json \
  -o /tmp/fibrousRouterAbi.json
```

## 4. `send_calls`

```json
{
  "chain": "base",
  "calls": [
    { "to": "<tokenIn>", "data": "<erc20 approve calldata>", "value": "0x0" },
    { "to": "0x274602a953847d807231d2370072f5f4e4594b44", "data": "<swap calldata>", "value": "<0x0 or amount_in hex>" }
  ]
}
```

Omit the approval call when input is native ETH.

---

## Helper Script

Drop the snippet below into `build-swap.cjs` in a workdir that has `ethers` (v6) installed (`npm i ethers`). Uses global `fetch` (Node 18+). It performs steps 1–3 in one shot and prints a `send_calls`-ready JSON to stdout.

```js
// build-swap.cjs
// Usage: node build-swap.cjs <tokenIn> <tokenOut> <amount> <decimals> <destination> [slippage=0.5]
// Native ETH input: pass tokenIn = 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE
const { parseUnits, Interface, MaxUint256 } = require("ethers");
const fs = require("fs");

const NATIVE = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE";
const ABI_PATH = process.env.FIBROUS_ABI || "/tmp/fibrousRouterAbi.json";
const ROUTER_ABI = JSON.parse(fs.readFileSync(ABI_PATH, "utf8")).abi;
const ERC20_ABI = ["function approve(address spender, uint256 amount)"];

const [,, tokenIn, tokenOut, humanAmount, decimalsStr, destination, slippageStr] = process.argv;
if (!destination) { console.error("usage: build-swap.cjs tokenIn tokenOut amount decimals destination [slippage]"); process.exit(2); }
const slippage = Number(slippageStr ?? "0.5");

(async () => {
  const inputAmount = parseUnits(humanAmount, Number(decimalsStr)).toString();
  const routeUrl = `https://api.fibrous.finance/base/v2/route?amount=${inputAmount}&tokenInAddress=${tokenIn}&tokenOutAddress=${tokenOut}`;
  const route = await (await fetch(routeUrl, { headers: { "User-Agent": "Mozilla/5.0" } })).json();
  if (!route.success) throw new Error("route failed");

  const cd = await (await fetch("https://api.fibrous.finance/base/v2/calldata", {
    method: "POST",
    headers: { "Content-Type": "application/json", "User-Agent": "Mozilla/5.0" },
    body: JSON.stringify({ route, slippage, destination }),
  })).json();

  const router = cd.router_address;
  const r = cd.route;
  const sps = cd.calldata?.swap_parameters ?? cd.swap_parameters;

  const iface = new Interface(ROUTER_ABI);
  const routeTuple = [r.token_in, r.token_out, r.amount_in, r.amount_out, r.min_received, r.destination, r.swap_type];
  const spTuples = sps.map((p) => [p.token_in, p.token_out, p.rate, p.protocol_id, p.pool_address, p.swap_type, p.extra_data ?? "0x"]);
  const swapData = iface.encodeFunctionData("swap", [routeTuple, spTuples]);

  const isNativeIn = tokenIn.toLowerCase() === NATIVE.toLowerCase();
  const valueHex = isNativeIn ? "0x" + BigInt(r.amount_in).toString(16) : "0x0";
  const calls = [];
  if (!isNativeIn) {
    const approveData = new Interface(ERC20_ABI).encodeFunctionData("approve", [router, MaxUint256]);
    calls.push({ to: tokenIn, data: approveData, value: "0x0" });
  }
  calls.push({ to: router, data: swapData, value: valueHex });

  console.log(JSON.stringify({
    chain: "base",
    calls,
    _meta: { router, outputAmount: route.outputAmount, minReceived: r.min_received, slippagePercent: slippage },
  }, null, 2));
})().catch((e) => { console.error(e); process.exit(1); });
```

Run it:

```bash
node build-swap.cjs \
  0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 \
  0x4200000000000000000000000000000000000006 \
  1 6 \
  <wallet address> 0.5
```

Stdout shape:

```json
{
  "chain": "base",
  "calls": [
    { "to": "<tokenIn>", "data": "0x095ea7b3...", "value": "0x0" },
    { "to": "0x274602a953847d807231d2370072f5f4e4594b44", "data": "0x8619b04e...", "value": "0x0" }
  ],
  "_meta": { "router": "...", "outputAmount": "...", "minReceived": "...", "slippagePercent": 0.5 }
}
```

Pass the `chain` and `calls` fields directly to `send_calls`. Show `_meta.outputAmount` / `_meta.minReceived` for user confirmation.

---

## Orchestration

```text
1. get_wallets -> address
2. Convert tokenIn amount to base units (use token decimals)
3. Run the helper snippet to fetch route + calldata + ABI-encoded swap (fetch the router ABI from the Fibrous-Finance/router-contract-abi repo first if not cached)
4. Show outputAmount and minReceived to the user with the slippage percent
5. send_calls({ "chain": "base", "calls": <calls> })
6. Open the approvalUrl only if the user explicitly asks
7. get_request_status only after the user acts in Base Account
```

If the helper script cannot run (chat-only surface with no shell), call the two HTTP endpoints via `web_request`, then ABI-encode `swap(route, swap_parameters)` against the upstream `routerAbi.json` using whatever encoder the harness provides (`cast abi-encode`, viem, ethers). The function selector is `0x8619b04e` and the tuple layout is documented above.

---

## Slippage Warnings

| Tolerance | Level | Action |
| --- | --- | --- |
| ≤ 1% | Normal | Proceed. |
| > 1% and ≤ 5% | Elevated | Mention the value and ask the user to confirm. |
| > 5% and ≤ 20% | High | Warn that the trade can fill significantly below quote. Require explicit confirmation. |
| > 20% | Very high | Strongly warn; do not submit without the user re-confirming the exact number. |

Default to `slippage=0.5` when the user does not specify a value. The API caps slippage at 49.

---

## Example Prompts

**Swap 1 USDC to WETH on Base via Fibrous**
1. `get_wallets` → address.
2. `node build-swap.cjs 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 0x4200000000000000000000000000000000000006 1 6 <address> 0.5`.
3. Read `_meta.outputAmount` from stdout, show to user.
4. `send_calls` with the `calls` array.

**Swap 0.001 ETH to USDC on Base via Fibrous**
1. `get_wallets` → address.
2. `node build-swap.cjs 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 0.001 18 <address> 0.5`.
3. The helper emits a single swap call with `value` set to the wei amount and no approval.
4. `send_calls` with the `calls` array.

---

## Why Fibrous vs. Uniswap

Both plugins ultimately settle through `send_calls`. Reasons to prefer Fibrous:

- Aggregates across PancakeSwap (V2/V3/Infinity), Uniswap V3/V4, Tessera, and other Base DEXs in a single route. Often beats single-DEX quotes for mid-to-large size.
- One quote + one execute, no Permit2 dance.

Reasons to prefer Uniswap:

- Pre-encoded calldata returned by the API — no local ABI step. Works on chat-only surfaces.
- Native LP management endpoints (this plugin is swap-only).

If both plugins are available, quote both for the user's input and route to whichever delivers more `outputAmount`. Show the user the comparison before executing.

---

## Notes

- Native ETH sentinel: `0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE`.
- USDC on Base: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`.
- WETH on Base: `0x4200000000000000000000000000000000000006`.
- Token amounts are base units: USDC = 1e6 per token, ETH/WETH = 1e18 per token.
- Use `chain: "base"` with `send_calls`, not numeric chain id.
- The helper script issues an unlimited `approve(router, MaxUint256)`. If the user requests a single-use approval, change the approval amount to `amount_in` before encoding.
- Calldata can include time-sensitive routing; rebuild it if the user waits a long time before approving.
- API docs: https://docs.fibrous.finance/api-reference/endpoints/route-v2
