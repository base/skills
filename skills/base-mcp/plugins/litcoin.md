---
title: "LITCOIN Plugin"
description: "Full LITCOIN protocol plugin on Base mainnet. Read wallet state (balances, staking, vaults, escrow, claimable, oracle). Build unsigned calldata for staking, claims, LITCREDIT vaults (open / mint / repay / close), compute escrow, and ERC20 transfer. Discover LITCOIN buy venues. Purchase a Data Card subscription with one x402 HTTP payment. Everything in this plugin returns unsigned calldata for Base MCP send_calls; signing stays with the wallet."
---

# LITCOIN Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before calling any LITCOIN endpoint. The user's wallet address — used as `from` in every prepare call — is fetched lazily when needed.

LITCOIN is a decentralized AI-data protocol on Base mainnet (`chainId` 8453). AI agents mine quality-scored research submissions, earn LITCOIN rewards, stake into 4 tiers that scale yield + mining boost, deposit LITCOIN or USDC as collateral inside a vault to mint LITCREDIT (an AI-compute credit, ~1,000 model output tokens), spend LITCREDIT through the compute escrow, transfer protocol tokens, and purchase Data Card subscriptions over the x402 HTTP payment protocol. The plugin returns **unsigned** call data; signing and broadcasting are the wallet's job (Base MCP `send_calls`).

## Surface routing

| Capability | Hosts | Where it runs |
| --- | --- | --- |
| **View-only reads** — wallet balances, staking position, claimable rewards, tier configs, contract addresses | `api.litcoin.app` | Every surface. Use the harness HTTP tool when available; otherwise Base MCP `web_request` — `api.litcoin.app` is on the allowlist. |
| **Transaction-builder** — stake, unstake, early-unstake, upgrade-tier, add-to-stake, claim, ERC20 approve | `api.litcoin.app/v1/mcp/prepare/*` | Every surface. Same host as reads; the prepare endpoints return unsigned calldata only. No auth header required. |
| **Data Card buy flow (x402)** | `api.litcoin.app/v1/data/x402/*` | Every surface. Purchase a research dataset subscription with one signed EIP-3009 authorization. Uses HTTP 402 + `X-PAYMENT` header. Settlement via the public x402.org facilitator. |

Routing order for any LITCOIN HTTP call:

1. **Harness HTTP tool** (`curl`, `fetch`, shell) — works for every host, any method, no allowlist.
2. **Base MCP `web_request`** — chat-only surfaces, same `api.litcoin.app` host.

Do not sign, approve, or submit transactions unless the user explicitly asks. Generating call data and `send_calls` approval links is safe; the user approves any real transaction.

No API key or Authorization header is required for the documented public endpoints.

---

## API Service

| Service | Base URL | Routing | Purpose |
| --- | --- | --- | --- |
| litcoin-mcp | `https://api.litcoin.app/v1/mcp` | CLI or `web_request` | Wallet state + unsigned calldata for staking and claim operations on Base mainnet |
| litcoin-data-x402 | `https://api.litcoin.app/v1/data/x402` | CLI or `web_request` | Agent-native Data Card subscription purchase via the x402 HTTP payment protocol (USDC on Base) |

Source of truth for chain config + contract addresses:

```
GET https://api.litcoin.app/v1/mcp/addresses
# → { chainId, chainName, contracts: { LITCOIN, STAKING, CLAIMS, LITCREDIT, VAULT_MANAGER, COMPUTE_ESCROW, ORACLE, USDC }, docs, protocol_api }
```

---

## Base-Only Rules

- All prepare-endpoint call data targets Base mainnet (`chainId` 8453). There is no chain selector.
- LITCOIN is the protocol token. USDC is used for the optional Data Card buy flow (separate from staking/claim).
- Canonical Base LITCOIN: `0x316ffb9c875f900AdCF04889E415cC86b564EBa3`.
- Canonical Base USDC:    `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`.
- Default LITCOIN spender for staking is the STAKING contract: `0xC9584Ce1591E8EB38EdF15C28f2FDcca97A3d3B7`.

Live contract addresses:

| Contract | Mainnet address |
| --- | --- |
| `LITCOIN` (ERC20) | `0x316ffb9c875f900AdCF04889E415cC86b564EBa3` |
| `STAKING` | `0xC9584Ce1591E8EB38EdF15C28f2FDcca97A3d3B7` |
| `CLAIMS` | `0xF703DcF2E88C0673F776870fdb12A453927C6A5e` |
| `LITCREDIT` | `0x33e3d328F62037EB0d173705674CE713c348f0a6` |
| `VAULT_MANAGER` | `0xD23a9b32e38FABE2325e1d27f94EcCf0e4a2f058` |
| `COMPUTE_ESCROW` | `0x28C351FE1A37434DD63882dA51b5f4CBade71724` |
| `ORACLE` | `0x4f937937A3B7Ca046d0f2B5071782aFFC675241b` |
| `USDC` | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |
| `WETH` (Base canonical) | `0x4200000000000000000000000000000000000006` |
| Aerodrome V2 Router (for `prepare/buy-litcoin` calldata when V2 liquidity exists) | `0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43` |
| Aerodrome V2 PoolFactory | `0x420DD381b31aEf6683db6B902084cB0FFECe40Da` |

Stake tiers (snapshot — call `addresses` + `state` for live config):

| Tier | Name | Mining boost | Lock | Notes |
| --- | --- | --- | --- | --- |
| 1 | Bronze | 1.0x | shorter | Entry tier |
| 2 | Silver | 1.25x | medium | Mid tier |
| 3 | Core / Gold | 1.5x | longer | Most common active tier |
| 4 | Architect | 2.0x+ | longest | Top tier |

`getTierConfig(tier)` returns the precise on-chain values for `stakeRequired`, `lockDuration`, `collateralRatioBps`, `miningBoostBps`.

---

## Response envelope (prepare endpoints)

Every prepare endpoint returns:

```json
{
  "ok": true,
  "data": {
    "to": "0xC9584Ce1591E8EB38EdF15C28f2FDcca97A3d3B7",
    "from": "0x1111111111111111111111111111111111111111",
    "data": "0x...",
    "value": "0x0",
    "chainId": 8453,
    "description": "Stake into Core (tier 3, 100M LITCOIN, 90d lock)",
    "meta": { "validation": { ... } }
  }
}
```

| Field | Notes |
| --- | --- |
| `to`, `data`, `value` | Forwarded into Base MCP `send_calls`. `value` is `0x`-prefixed wei; convert with `BigInt(value)` if you need a numeric. |
| `from` | Who must sign. Pass the wallet address as `from=...` in the query string. |
| `chainId` | Always `8453`. |
| `description` | Human-readable label to show the user before they approve. |
| `meta` | Endpoint-specific context. Stake/upgrade-tier endpoints include a `validation` block with balance + allowance + lock state. |
| `nonce`, `gas` | Never returned. The wallet manages them. |

Errors:

```json
{ "ok": false, "error": { "code": "VALIDATION_ERROR", "message": "...", "details": { "balanceWei": "0", "requiredWei": "100000000000000000000000000" } } }
```

Error codes: `BAD_REQUEST` (malformed params), `VALIDATION_ERROR` (call would revert — details explain why), `UPSTREAM_ERROR` (coordinator dependency down), `INTERNAL_ERROR`.

---

## Read endpoints

### Wallet state — one round-trip

```
GET https://api.litcoin.app/v1/mcp/state/<wallet>
```

Returns balances, staking position, allowance, claimable rewards in a single response. Call this **first** to decide which action to offer the user.

```json
{
  "ok": true,
  "wallet": "0xc1ae2db18ee47c97bd7b83165f3afea0d9c31f3c",
  "chainId": 8453,
  "balances": {
    "litcoinWei":   "0",
    "litcoin":      0,
    "usdcMicros":   "0",
    "usdc":         0,
    "litcreditWei": "0",
    "litcredit":    0
  },
  "staking": {
    "tier": 3,
    "tierName": "Core",
    "amountWei": "106940702000000000000000000",
    "amount": 106940702,
    "stakedAt": 1736472999,
    "lockUntil": 1744203399,
    "locked": false,
    "allowanceWei": "115792089237316195423570985008687907853269984665640564039457584007913129639935"
  },
  "vaults": {
    "count": 1,
    "ids": ["30"],
    "details": [{
      "vaultId": "30",
      "owner": "0xc1ae2db18ee47c97bd7b83165f3afea0d9c31f3c",
      "token": "0x316ffb9c875f900adcf04889e415cc86b564eba3",
      "tokenSymbol": "LITCOIN",
      "collateral": 10000,
      "debt": 0.0074,
      "openedAt": 1778036169,
      "closed": false,
      "maxMintable": 4.11
    }]
  },
  "escrow": { "litcreditWei": "0", "litcredit": 0 },
  "oracle": { "priceUsd": 0.0102, "rawWei": "10200", "contract": "0x4f937937..." },
  "claimable": {
    "totalEarnedLit": "9.2M",
    "claimableLit": "83.7K",
    "breakdown": { "research": "9.1M", "staking": "122.9K", "comprehension": "0", "relay": "0" }
  }
}
```

`oracle` is `null` if the on-chain keeper hasn't published a price recently. `vaults.details` only includes vaults the contract returns data for (closed vaults are still listed in `vaults.ids` but skipped from `details`).

### Contract addresses + chain config

```
GET https://api.litcoin.app/v1/mcp/addresses
# → { chainId: 8453, contracts: { LITCOIN, STAKING, CLAIMS, LITCREDIT, VAULT_MANAGER, COMPUTE_ESCROW, ORACLE, USDC }, docs, protocol_api }
```

---

## Prepare endpoints (unsigned calldata)

### Approve LITCOIN for STAKING

Required **once** per wallet before the first `stake` or `add-to-stake`. Pass `amount=max` to approve unlimited (most common) or a decimal LITCOIN value for a bounded approval.

```
GET https://api.litcoin.app/v1/mcp/prepare/approve-litcoin?from=0x...&amount=max
GET https://api.litcoin.app/v1/mcp/prepare/approve-litcoin?from=0x...&amount=100000000
GET https://api.litcoin.app/v1/mcp/prepare/approve-litcoin?from=0x...&spender=0x...&amount=max
```

`spender` defaults to the STAKING contract. Override only if approving for a different LITCOIN consumer (LITCREDIT vault, compute escrow).

### Stake into a tier

```
GET https://api.litcoin.app/v1/mcp/prepare/stake?from=0x...&tier=3
```

`tier` is 1, 2, 3, or 4. Endpoint validates that the wallet has enough LITCOIN AND enough allowance before encoding. If allowance < required, the call will return `VALIDATION_ERROR`; route the user through `approve-litcoin` first, then retry.

The meta block includes:

```json
"meta": {
  "validation": {
    "tierName": "Core",
    "requiredWei": "100000000000000000000000000",
    "requiredLitcoin": 100000000,
    "currentBalanceWei": "150000000000000000000000000",
    "currentAllowanceWei": "115792089237316195423570985008687907853269984665640564039457584007913129639935",
    "hasEnoughBalance": true,
    "hasEnoughAllowance": true,
    "existingStakeTier": 0,
    "warning": null
  }
}
```

If `existingStakeTier > 0`, route to `prepare/upgrade-tier` (move up) or `prepare/add-to-stake` (top up at current tier) instead.

### Unstake (lock-respecting)

```
GET https://api.litcoin.app/v1/mcp/prepare/unstake?from=0x...
```

Returns `VALIDATION_ERROR` if the stake is still locked. The error details include `lockUntil` (unix seconds) so the assistant can tell the user when they'll be eligible.

### Early-unstake (pays penalty)

```
GET https://api.litcoin.app/v1/mcp/prepare/early-unstake?from=0x...
```

Only valid when the stake IS locked. Forfeits a portion of the stake as a contract-enforced penalty. The `meta.warning` field reminds the assistant to confirm the user accepts the penalty before submitting.

### Upgrade tier

```
GET https://api.litcoin.app/v1/mcp/prepare/upgrade-tier?from=0x...&tier=4
```

Target tier must be strictly greater than current. The meta block includes the new tier's full config so the assistant can describe the upgrade in user-readable terms.

### Add to existing stake

```
GET https://api.litcoin.app/v1/mcp/prepare/add-to-stake?from=0x...&amount=50000000
```

`amount` is decimal LITCOIN. Validates balance + allowance.

### Claim mining rewards

```
GET https://api.litcoin.app/v1/mcp/prepare/claim?from=0x...
```

The coordinator signs `(wallet, totalEarned, claimsContract, chainId)` off-chain using its admin signer; the on-chain CLAIMS contract validates that signature when the user submits the tx. Same flow Bankr-keyed claims use.

Returns `VALIDATION_ERROR` if `claimable == 0`. Meta block includes `signedTotalEarnedWei`, `fullEarnedWei`, `claimableWei`, `fullClaimableWei`, and `partial` (true if the signed amount is less than the full off-chain claimable — this happens when a per-call cap kicks in).

---

### Generic ERC20 approve (for LITCREDIT / USDC / WETH / etc.)

Same shape as `approve-litcoin`, but the spender and token are explicit. Use this for repaying LITCREDIT debt (token=`litcredit`, spender=`vault`), depositing LITCREDIT into the escrow (spender=`escrow`), or approving USDC for the Aerodrome router (token=`usdc`, spender=router address).

```
GET https://api.litcoin.app/v1/mcp/prepare/approve-token?from=0x...&token=litcredit&spender=escrow&amount=max
GET https://api.litcoin.app/v1/mcp/prepare/approve-token?from=0x...&token=usdc&spender=vault&amount=5000
```

`token` accepts `litcoin`, `litcredit`, `usdc`, `weth`, or any 0x-prefixed ERC20 address. `spender` accepts `staking`, `vault`, `escrow`, `claims`, or any 0x-prefixed address. `amount` accepts `max` (uint256.max) or a decimal token amount in the token's native decimals.

### Open a vault with LITCOIN collateral

```
GET https://api.litcoin.app/v1/mcp/prepare/open-vault?from=0x...&amount=10000
```

The wallet must have approved the VAULT_MANAGER contract to spend LITCOIN first (`prepare/approve-token?token=litcoin&spender=vault`). The meta block surfaces balance + allowance up front so an agent can route the user through the right two-step approve-then-open sequence.

### Open a vault with USDC (or arbitrary ERC20) collateral

```
GET https://api.litcoin.app/v1/mcp/prepare/open-vault-v2?from=0x...&token=USDC&amount=5000
```

`token` defaults to USDC. Use the explicit `?token=` query for any other ERC20. Allowance is checked against the same VAULT_MANAGER spender.

### Mint LITCREDIT against an existing vault

```
GET https://api.litcoin.app/v1/mcp/prepare/mint-litcredit?from=0x...&vaultId=30&amount=2
```

The endpoint reads `getMaxMintable(vaultId)` and returns a `VALIDATION_ERROR` (with the current cap in the `details`) if the request would breach the collateral ratio. Always show the user the `maxMintable` field from the meta block before they sign.

### Repay LITCREDIT debt

```
GET https://api.litcoin.app/v1/mcp/prepare/repay-debt?from=0x...&vaultId=30&amount=max
GET https://api.litcoin.app/v1/mcp/prepare/repay-debt?from=0x...&vaultId=30&amount=0.5
```

`amount=max` repays the full outstanding debt. The handler enforces that the wallet has both enough LITCREDIT balance and allowance against VAULT_MANAGER; route through `approve-token?token=litcredit&spender=vault` first if needed.

### Add or withdraw collateral on an open vault

```
GET https://api.litcoin.app/v1/mcp/prepare/add-collateral?from=0x...&vaultId=30&amount=1000
GET https://api.litcoin.app/v1/mcp/prepare/withdraw-collateral?from=0x...&vaultId=30&amount=500
```

`add-collateral` checks balance + allowance against the vault's stored collateral token (USDC uses 6-decimal amounts; LITCOIN uses 18). `withdraw-collateral` warns if the vault still has outstanding LITCREDIT debt and the withdraw might breach the collateral ratio on-chain.

### Close a vault

```
GET https://api.litcoin.app/v1/mcp/prepare/close-vault?from=0x...&vaultId=30
```

Returns `VALIDATION_ERROR` if the vault still has debt. The error message tells the agent to call `prepare/repay-debt?amount=max` first.

### Compute escrow: deposit / withdraw LITCREDIT

```
GET https://api.litcoin.app/v1/mcp/prepare/deposit-escrow?from=0x...&amount=10
GET https://api.litcoin.app/v1/mcp/prepare/withdraw-escrow?from=0x...&amount=2
```

`deposit-escrow` checks LITCREDIT balance and allowance against the COMPUTE_ESCROW contract; route through `approve-token?token=litcredit&spender=escrow` first. The escrow balance powers the LITCOIN compute marketplace at <https://litcoin.app/compute>.

### Send LITCOIN / LITCREDIT / USDC to another wallet

```
GET https://api.litcoin.app/v1/mcp/prepare/transfer?from=0x...&token=litcoin&to=0x...&amount=100
GET https://api.litcoin.app/v1/mcp/prepare/transfer?from=0x...&token=usdc&to=0x...&amount=25
```

Standard ERC20 transfer calldata. `token` accepts the same aliases as `approve-token`.

### Buy LITCOIN (discovery first, calldata if available)

LITCOIN's deepest liquidity today is on Uniswap V4 LITCOIN/WETH (~$388K). Aerodrome V2 has no liquid pool yet, so the recommended path is to surface a swap URL to the user rather than build calldata that would revert. Two endpoints:

```
GET https://api.litcoin.app/v1/mcp/buy-info
```

Returns the canonical Aerodrome swap UI URL (auto-routes through V2 / Slipstream / Uniswap V4), alternate venues (Uniswap, Matcha, DexScreener, Bankr), the top 5 live pools from DexScreener, and a Coinbase Onramp link.

```
GET https://api.litcoin.app/v1/mcp/prepare/buy-litcoin?from=0x...&token=USDC&amount=100
GET https://api.litcoin.app/v1/mcp/prepare/buy-litcoin?from=0x...&token=ETH&amount=0.05
```

Best-effort Aerodrome V2 router builder. While V2 has no LITCOIN liquidity it returns a clean `VALIDATION_ERROR` pointing the agent at `/v1/mcp/buy-info` and the Aerodrome UI. Once V2 liquidity is bootstrapped the same call returns a valid envelope with a slippage-protected `minOut`.

### Oracle: LITCOIN/USD price

```
GET https://api.litcoin.app/v1/mcp/oracle/price
```

Reads the on-chain ORACLE contract for the LITCOIN/USD spot price the keeper publishes. Returns `503 UPSTREAM_ERROR` (with a DexScreener fallback URL) if the keeper hasn't published yet. Cache for 30s on the CDN.

### Vault read

```
GET https://api.litcoin.app/v1/mcp/vault/:vaultId
```

Per-vault enrichment: owner, collateral token + amount, outstanding LITCREDIT debt, `maxMintable` at the current ratio, and `collateralRatioBps` / `collateralRatioPct`. The `/state` route already includes this for every vault the wallet owns; use this endpoint when you need to inspect a vault that isn't yours.

---

## Data Card x402 buy flow (agent-native subscription purchase)

The Data Card sells subscription access to the LITCOIN research dataset (rows, DPO preference pairs, recipe bundles). Four tiers, priced in USD:

| Tier | Price | Row limit | DPO pairs | Recipe bundles | Duration |
| --- | --- | --- | --- | --- | --- |
| `pilot` | $5,000 | 100K | no | no | one-time |
| `standard` | $37,500 | 1M | no | no | 365d |
| `domain` | $87,500 | unlimited | yes | yes | 365d |
| `enterprise` | $250,000 | unlimited | yes | yes | 365d |

The legacy path requires the buyer to send a real on-chain tx to the treasury wallet and POST the tx hash to `/v1/data/onboard` (still supported for human dashboard buyers). The agent-native path uses the **x402 HTTP payment protocol** so any Base wallet (including MCP-connected agents) can sign one EIP-3009 authorization and complete the purchase in a single HTTP round-trip.

### Discover

```
GET https://api.litcoin.app/v1/data/x402/info
```

Returns the route map for the four x402-enabled tiers:

```json
{
  "protocol": "x402",
  "version": 1,
  "network": "base",
  "facilitator": "https://x402.org/facilitator",
  "pay_to": "0xd61d769D1E745bBdE207fdC8978f3E492eFF7A8b",
  "accepted_asset": "USDC on Base (auto-selected by facilitator)",
  "routes": [
    { "tier": "pilot", "price_usd": 5000, "path": "/v1/data/x402/onboard/pilot", "method": "POST", "body_fields": ["companyName", "contactEmail", "..."], "duration_days": null },
    { "tier": "standard", "price_usd": 37500, "path": "/v1/data/x402/onboard/standard", "method": "POST", "body_fields": ["companyName", "contactEmail", "..."], "duration_days": 365 },
    { "tier": "domain", "price_usd": 87500, "path": "/v1/data/x402/onboard/domain", "method": "POST", "body_fields": ["companyName", "contactEmail", "..."], "duration_days": 365 },
    { "tier": "enterprise", "price_usd": 250000, "path": "/v1/data/x402/onboard/enterprise", "method": "POST", "body_fields": ["companyName", "contactEmail", "..."], "duration_days": 365 }
  ]
}
```

### Two-call x402 onboard

**Step 1.** POST WITHOUT an `X-PAYMENT` header. The server returns HTTP 402 and a `paymentRequirements` payload describing the asset, amount, and authorization shape:

```
POST https://api.litcoin.app/v1/data/x402/onboard/pilot
Content-Type: application/json

{ "companyName": "ExampleLab", "contactEmail": "agent@example.com" }
```

Response (402):

```json
{
  "x402Version": 1,
  "error": "X-PAYMENT header is required",
  "accepts": [{
    "scheme": "exact",
    "network": "base",
    "maxAmountRequired": "5000000000",
    "resource": "https://api.litcoin.app/v1/data/x402/onboard/pilot",
    "description": "LITCOIN Data Card subscription: Pilot",
    "payTo": "0xd61d769D1E745bBdE207fdC8978f3E492eFF7A8b",
    "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "maxTimeoutSeconds": 300
  }]
}
```

**Step 2.** Sign an EIP-3009 `transferWithAuthorization` over USDC for the requested amount (`maxAmountRequired`, atomic units), base64-encode the payload per x402 v1 spec, attach as `X-PAYMENT`, and POST again. The body is the same.

The middleware verifies the signature, calls our handler (which creates the client + activates the key + emails the receipt), then settles the authorization on-chain through the public x402.org facilitator. On success the response body contains the API key and the `X-PAYMENT-RESPONSE` header contains the settlement tx hash:

```json
{
  "success": true,
  "protocol": "x402",
  "client_id": "dc-1737000000000-abcd1234",
  "tier": "pilot",
  "api_key": "ld_...",
  "activated_at": "2026-05-26T22:00:00.000Z",
  "expires_at": null,
  "payer_wallet": "0x...",
  "payment": {
    "authorization_nonce": "0x...",
    "authorization_value": "5000000000",
    "token": "USDC",
    "network": "base",
    "note": "Settlement tx hash is in the X-PAYMENT-RESPONSE header on this response."
  },
  "endpoints": {
    "status":      "GET /v1/data/status?key=YOUR_KEY",
    "export_rows": "GET /v1/data/export/rows?key=YOUR_KEY",
    "export_dpo":  null
  },
  "rate_limit": "10 requests/hour",
  "row_limit":  100000
}
```

Settlement is final once the facilitator returns success. The buyer can immediately start hitting `/v1/data/export/rows?key=<api_key>` to download data.

### Helper libraries

The protocol is agent-agnostic. Reference client libraries:

- **TypeScript / Node**: `x402-fetch`, `x402-axios` (Coinbase, x402 v1)
- **Python**: `x402` package (pip)
- **Base AI Agent SDK**: x402 is the canonical paid-API pattern; any wallet exposed to the agent can sign.

If the buyer prefers an on-chain receipt path (one tx, then onboard), the legacy `/v1/data/onboard` route is still live and documented at <https://litcoin.app/research/dataset>.

---

## send_calls mapping

After the wallet has a valid prepare-response envelope, build the Base MCP `send_calls` arg as:

```json
{
  "chain": "base",
  "calls": [
    {
      "to":    "<data.to>",
      "value": "<data.value>",
      "data":  "<data.data>"
    }
  ]
}
```

For first-time stakes, the call list is two-step (approve, then stake):

```json
{
  "chain": "base",
  "calls": [
    { "to": "0x316ffb9c875f900AdCF04889E415cC86b564EBa3", "data": "<approve calldata>", "value": "0x0" },
    { "to": "0xC9584Ce1591E8EB38EdF15C28f2FDcca97A3d3B7", "data": "<stake calldata>",   "value": "0x0" }
  ]
}
```

---

## Disclaimers

LITCOIN is a live protocol on Base mainnet. Staked LITCOIN is locked according to the on-chain tier config; early-unstake forfeits a contract-enforced penalty. Claim transactions release LITCOIN credited to the user's coordinator ledger; the off-chain ledger is the source of truth for `totalEarned` and the on-chain `claim()` function validates the coordinator's signature.

Always show the user the prepare-response `description` field and the `meta.validation` block (when present) **before** routing the call to `send_calls`. The user is the only party authorized to sign.

For coordinator off-chain operations (submit research solutions, configure miner, query data card) the LITCOIN Python SDK (`pip install litcoin`) is the canonical path. The Base MCP plugin covers the on-chain financial primitives only.

---

## Links

- Protocol site: <https://litcoin.app>
- Docs: <https://litcoin.app/docs>
- API: <https://api.litcoin.app>
- SDK on PyPI: <https://pypi.org/project/litcoin/>
- LITCOIN on BaseScan: <https://basescan.org/token/0x316ffb9c875f900AdCF04889E415cC86b564EBa3>
- LITCOIN on DexScreener: <https://dexscreener.com/base/0x721763bb8c0697d9c7b4ba26d1664677e6e8c0e6>
