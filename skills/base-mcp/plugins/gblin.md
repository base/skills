---
title: "GBLIN Plugin"
description: "Park surplus USDC in the GBLIN basket vault at NAV, redeem it back to USDC just in time, and read the market risk regime via HTTP API → send_calls on Base."
tags: [vaults, ai-agents, agent-commerce]
name: gblin
version: 0.2.0
integration: http-api
chains: [base]
requires:
  shell: none
  allowlist: [gblin.digital]
  externalMcp: null
  cliPackage: null
auth: none
risk: [slippage, irreversible]
---

# GBLIN Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before calling any GBLIN endpoint. The user's wallet address, required by the `health`, `invest` and `jit` endpoints, is fetched lazily with `get_wallets` when a flow needs it.

## Overview

GBLIN is a basket vault on Base mainnet: one ERC-20 share backed by cbBTC, WETH and USDC held in the contract, priced by Chainlink feeds, minted and redeemed at net asset value (NAV). The vault never swaps by itself; it rebalances through a Dutch auction and cuts the weight of an asset during a severe drawdown (the crash shield). The plugin reads treasury state and quotes over the GBLIN HTTP API, fetches **unsigned calldata** from its prepare endpoints, and executes via `send_calls`. Typical use: keep operating cash in USDC, park the surplus in GBLIN, and redeem just in time when an x402 invoice needs USDC.

**Supported chain:** Base mainnet (8453). GBLIN is not a stablecoin: its NAV moves with cbBTC and WETH.

## Surface Routing

GBLIN is HTTP-only; every capability follows the standard HTTP routing in [../references/custom-plugins.md](../references/custom-plugins.md).

| Capability | Path |
|-----------|------|
| Read NAV, basket, shield status, quotes, wallet health, governance | Harness HTTP tool if available, else `web_request` GET against `gblin.digital`. |
| Prepare an investment (USDC → GBLIN) or a just-in-time redemption (GBLIN → USDC) | Harness HTTP tool or `web_request` GET → calldata → `send_calls`. |
| Paid attestation of the risk regime (x402, USDC on Base) | Harness with an x402 client only (`@x402/fetch`). On chat-only surfaces skip it: the same regime is readable for free from `treasury-state`. |
| Execute the prepared calldata | Base MCP `send_calls` (works on every surface). |

**Prerequisite:** `gblin.digital` must be in the MCP server's `web_request` allowlist. Every prepare endpoint is a GET with query-string parameters: if the host is rejected and no harness HTTP tool is available, construct the URL, ask the user to paste the JSON response into the chat, and continue with `send_calls`.

## Endpoints

### Read endpoints (free)

```
GET https://gblin.digital/api/x402/llms.txt
GET https://gblin.digital/api/x402/treasury-state
GET https://gblin.digital/api/x402/health?wallet=<address>&daily_burn=<usd_per_day>
GET https://gblin.digital/api/x402/quote?direction=buy&amount=<eth_decimal>
GET https://gblin.digital/api/x402/quote?direction=sell&amount=<gblin_decimal>
GET https://gblin.digital/api/x402/governance
```

- `llms.txt` — human-readable summary of the protocol and the endpoints with their prices. Use it first to confirm the API is reachable.
- `treasury-state` — `nav_usd`, `eth_price_usd`, basket rows with dynamic weights, `crash_shield_active`, current `slippage_buffer_pct`.
- `health` — balances (`gblin`, `gblin_value_usd`, `usdc`, `eth`, `total_usd`), ratios, `gas_health`, the redemption `cooldown`; with `daily_burn` (optional), a runway estimate and a rebalance `recommendation`.
- `quote` — expected output, a safe `minOut` including the slippage buffer, and the fee breakdown. `buy` amounts are in ETH; `sell` amounts are in GBLIN.
- `governance` — verifies on-chain that the contract owner is the 48-hour timelock and reads its minimum delay.

### Prepare endpoints (free, unsigned calldata only)

```
GET https://gblin.digital/api/x402/invest?usdc=<decimal>&wallet=<address>
GET https://gblin.digital/api/x402/jit?usdc=<decimal>&wallet=<address>
```

Both return the same shape; nothing is executed server-side.

```json
{
  "action": "sequential_txs",
  "steps": [
    { "step": 1, "description": "Approve USDC to the GBLIN Zap", "target": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "calldata": "0x...", "value": "0" },
    { "step": 2, "description": "Swap USDC to WETH and mint GBLIN at NAV, in one transaction", "target": "0x0E9D6Ceb6D313b021622C121Cda9C62e86e60200", "calldata": "0x...", "value": "0", "gas": "1100000" }
  ],
  "gas_hint": 1100000,
  "expected": { "usdc_in": "...", "weth_min": "...", "gblin_expected": "...", "gblin_min": "...", "slippage_buffer_pct": 0 }
}
```

- `invest` — two steps: approve USDC to the GBLIN Zap, then one call that swaps USDC → WETH on the adapter and mints at NAV. Every step carries a non-zero `minOut`.
- `jit` — three steps: approve the shares to the Zap, `sellGBLINForEth` (redeem in kind and sell every leg, all or nothing), then a Uniswap WETH → USDC swap. `expected` carries `usdc_out`, `nav_used_usd`, `slippage_buffer_pct`; `compatibility` lists `eoa`, `erc4337`, `eip7702`. Requires the redemption cooldown to have elapsed (`health.cooldown`).

### Paid endpoints (x402, USDC on Base)

```
GET https://gblin.digital/api/x402/attestation      $0.003  signed, 10-minute proof of the risk regime (calm | elevated | crash)
GET https://gblin.digital/api/x402/catalog          $0.005  liveness report of the x402 catalogue
```

A plain GET returns HTTP 402 with the x402 v2 payment challenge; complete it with `@x402/fetch` or `@x402/axios` and retry. A free sample of the attestation schema is at `/api/x402/attestation-sample`.

## Orchestration

```
get_wallets → address
      ↓
GET /api/x402/treasury-state           → NAV, crash shield status
GET /api/x402/health?wallet=<address>  → USDC and GBLIN balances, cooldown, gas health
      ↓
GET /api/x402/invest?... or /api/x402/jit?...  → steps[], expected
      ↓
Show NAV, expected output, minimum output and fees; ask for confirmation
      ↓
send_calls(chain="base", calls mapped from steps[]) → approvalUrl + requestId
      ↓
User approves (see ../references/approval-mode.md) → get_request_status(requestId) → confirmed
```

### Park surplus USDC

1. `get_wallets` → address.
2. `health?wallet=<address>` → confirm `balances.usdc` ≥ amount and `gas_health.status` is `ok`.
3. `treasury-state` → if `crash_shield_active` is true, tell the user before continuing.
4. `invest?usdc=<amount>&wallet=<address>` → show `expected.gblin_expected`, `expected.gblin_min` and the fees; ask for confirmation.
5. `send_calls` with both steps in order.
6. `get_request_status(requestId)`.

### Just-in-time redemption for an x402 invoice

1. `get_wallets` → address.
2. `health?wallet=<address>` → confirm `balances.gblin_value_usd` covers the amount and `cooldown.active` is false.
3. `jit?usdc=<amount>&wallet=<address>` → show `expected.usdc_out` and `expected.nav_used_usd`; ask for confirmation.
4. `send_calls` with the three steps in order.
5. `get_request_status(requestId)`, then pay the invoice.

### Treasury check (read-only)

1. `get_wallets` → address.
2. `treasury-state` and `health?wallet=<address>&daily_burn=<usd>` → present holdings, NAV, basket weights, runway estimate and recommendation. No transaction.

## Submission

Target tool: **`send_calls`**.

GBLIN steps use `target` and `calldata`; map them to `to` and `data`, convert `value` to hex, and keep the order returned:

```json
{
  "chain": "base",
  "calls": [
    { "to": "<steps[0].target>", "value": "0x0", "data": "<steps[0].calldata>" },
    { "to": "<steps[1].target>", "value": "0x0", "data": "<steps[1].calldata>" }
  ]
}
```

One entry per element of `steps[]`: two for `invest`, three for `jit`. Never reorder them (approvals come first). A step that carries `gas` needs at least that limit: the vault forwards gas-capped transfers, and a wallet's own estimate can land just under what the call needs. If the wallet estimates the batch as a whole and it reverts out of gas, send the steps one by one with the given limit. Then walk the approval flow (see [../references/approval-mode.md](../references/approval-mode.md)) and poll `get_request_status`.

## Example Prompts

**"I have 500 USDC idle on Base. Park 400 in GBLIN and keep 100 liquid."**

1. `get_wallets` → address.
2. `health?wallet=<address>` → `balances.usdc` ≥ 400, `gas_health.status` = `ok`, `cooldown.active` = false.
3. `treasury-state` → NAV and shield status; mention it if the shield is active.
4. `invest?usdc=400&wallet=<address>` → show `gblin_expected`, `gblin_min` and the fees; confirm.
5. `send_calls("base", calls from steps[0..1])`.
6. `get_request_status(requestId)`.

**"An x402 invoice needs 12 USDC and I only hold GBLIN."**

1. `get_wallets` → address.
2. `health?wallet=<address>` → `balances.gblin_value_usd` ≥ 12, `cooldown.active` = false.
3. `jit?usdc=12&wallet=<address>` → show `usdc_out` and `nav_used_usd`; confirm.
4. `send_calls("base", calls from steps[0..2])`.
5. `get_request_status(requestId)`, then pay the invoice.

**"What is my GBLIN position worth, and how long does my USDC last at $20 a day?"** *(read-only)*

1. `get_wallets` → address.
2. `treasury-state` → NAV and basket.
3. `health?wallet=<address>&daily_burn=20` → balances, runway estimate, recommendation. No transaction submitted.

**"Who can change GBLIN's parameters?"** *(read-only)*

1. `governance` → the owner is the 48-hour timelock; report its minimum delay. Do not describe the token as immutable.

## Risks & Warnings

- **Slippage.** `invest` swaps USDC → WETH before minting, and `jit` sells the redeemed legs on a DEX before the final swap to USDC; each step carries a `minOut` derived from the API's slippage buffer. Show the `expected` values and the buffer to the user and never raise the buffer silently. A large amount against thin liquidity fails the whole `jit` call by design (all or nothing): the shares stay with the holder.
- **Irreversible.** A confirmed mint or redemption cannot be undone. Always show NAV, expected output and fees before `send_calls`, and never invest without an explicit confirmation: GBLIN's NAV moves with cbBTC and WETH; it is managed exposure for surplus capital, not a USDC substitute.

## Notes

- **Fees.** Mint with ETH or WETH: 0.10% (0.05% to the protocol, 0.05% stays in the vault and lifts the NAV). Management: 0.50% a year, accrued as new shares. Redemption in kind: no fee. The API reports current values; the x402 prices are API charges, not gas.
- **Cooldown.** A mint made directly on the vault for oneself sets a 20-second redemption cooldown; a mint through the Zap, as `invest` prepares it, does not. `health.cooldown` reports it either way.
- **Crash shield.** When `crash_shield_active` is true, the weight of an asset in a severe drawdown has been cut and moved to USDC; the contract handles it, the agent explains it.
- **Governance.** Every parameter change goes through the 48-hour timelock, within bounds written in the contract.
- **Hosted MCP (optional, free).** `https://gblin-mcp.gblin-mcp-worker.workers.dev/mcp` (Streamable HTTP) exposes the risk regime, treasury state and protocol info as MCP tools; `npx @gblin-protocol/mcp-server` runs the same server over stdio. The HTTP endpoints above are sufficient on their own.
- **Gasless GBLIN payments.** The share implements EIP-3009. `https://gblin.digital/api/relay/gblin` carries a signed `transferWithAuthorization` on chain for a fee quoted in GBLIN at NAV; not an x402 endpoint.

### Addresses (Base mainnet)

| Contract | Address |
|---|---|
| GBLIN vault (ERC-20 share) | `0xc2181d975c05c8c724b334bcED0764c0b86B1D53` |
| GBLIN Zap | `0x0E9D6Ceb6D313b021622C121Cda9C62e86e60200` |
| GBLIN Lens | `0xfCFea8027019E8551A1f09AD91532471F5D26f61` |
| Timelock (48 h) | `0x6aBeC8716fFeEcf7C3D6e68255b4797113E8e5Dd` |
| USDC | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |
| WETH | `0x4200000000000000000000000000000000000006` |
| cbBTC | `0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf` |

### Resources

- Site: https://gblin.digital · Agent guide: https://gblin.digital/agents
- Protocol source and test write-ups: https://github.com/gblinproject/GBLIN-Protocol
- Basescan: https://basescan.org/address/0xc2181d975c05c8c724b334bcED0764c0b86B1D53
