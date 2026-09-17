---
title: "BETRMINT Plugin"
description: "Mint–spin–win rounds and $BETR staking on Base via HTTP API → send_calls."
tags: [yield, staking, token-launches]
name: betrmint
version: 0.2.0
integration: http-api
chains: [base]
requires:
  shell: none
  allowlist: [betrmint.fun]
  externalMcp: null
  cliPackage: null
auth: none
risk: [irreversible]
---

# BETRMINT Plugin

> [!IMPORTANT]
> Run Base MCP onboarding first (see SKILL.md): call `get_wallets` (Detection) and present wallet status and disclaimer (Onboarding). The user's wallet address — required by every prepare call — is only confirmed during Detection.

## Overview

BETRMINT is a Base-native mint–spin–win protocol backed by the **$BETR** token. Users mint tickets in live rounds, spin for prizes, and claim winnings on-chain; stakers earn $BETR rewards funded by protocol activity. This plugin calls the BETRMINT HTTP API to read state and build **unsigned calldata**, then submits batches through Base MCP `send_calls` on **Base mainnet** (`8453` / `0x2105`).

**API base URL:** `https://betrmint.fun`

## Surface Routing

| Capability | Harness (Cursor, Claude Code, Codex) |
| --- | --- |
| Read (token, round) | HTTP tool → GET `https://betrmint.fun/api/plugin/betrmint/read/...` |
| Write (stake, claim, mint, win) | HTTP tool → GET prepare URL → `send_calls` |
| Explain / summarize | Same read paths as above |

All prepare endpoints are GET with query parameters. See [custom-plugins.md](https://docs.base.org/ai-agents/plugins/custom-plugins) for full plugin integration details.

## Endpoints

### Read — token + staking state

```
GET https://betrmint.fun/api/plugin/betrmint/read/token?wallet=<address>
```

Returns BETR balance, staked amount, claimable staking rewards, global stake totals, and pause flags.

### Read — running round

```
GET https://betrmint.fun/api/plugin/betrmint/read/round?slug=<slug>&wallet=<address>
```

- Omit `slug` to use the current **running** round (from BETRMINT ops state).
- Include `wallet` to see mint count, pending draws, and whether `win` is ready.

Example response shape:

```json
{
  "ok": true,
  "data": {
    "slug": "base:0x...",
    "name": "...",
    "contract": "0x...",
    "status": "active",
    "isLive": true,
    "availableMints": "1234",
    "wallet": {
      "pendingDraws": "0",
      "readyToWin": true
    }
  }
}
```

### Prepare — stake $BETR

```
GET https://betrmint.fun/api/plugin/betrmint/prepare/stake?from=<address>&amount=<decimal>
```

- `amount` is human-readable BETR (18 decimals), e.g. `amount=1000`.
- Includes `approve` when allowance is insufficient, then `stake(amount)`.

### Prepare — claim staking rewards

```
GET https://betrmint.fun/api/plugin/betrmint/prepare/claim-rewards?from=<address>
```

- Single call: `claim()` on the rewards contract.
- Fails if `claimable` is zero or rewarding is paused.

### Prepare — mint (mint to spin)

```
GET https://betrmint.fun/api/plugin/betrmint/prepare/mint?from=<address>&slug=<slug>&quantity=<n>&referral=<address>
```

- Omit `slug` for the running round.
- `quantity` defaults to `1` if omitted.
- Optional `referral` (zero address if unset on new round contracts).
- Includes payment-token `approve` when needed, then `mint(recipient, quantity, referral, data)`.
- `value` is set when the round is paid in native ETH (usually `0x0` for ERC-20 payment).

### Prepare — win (claim round prizes)

```
GET https://betrmint.fun/api/plugin/betrmint/prepare/win?from=<address>&slug=<slug>
```

- Call after mint confirms and `read/round` shows `readyToWin: true` (no pending draws).
- Executes `win(recipient)` on the round contract.

All prepare endpoints return an ordered batch for atomic execution:

```json
{
  "ok": true,
  "transactions": [
    { "step": "approve", "to": "0x...", "data": "0x...", "value": "0x0", "chainId": 8453 },
    { "step": "mint", "to": "0x...", "data": "0x...", "value": "0x0", "chainId": 8453 }
  ]
}
```

## Orchestration

Wallet address comes from `get_wallets` during Base MCP onboarding. Validate read state before every prepare call. Use the full URLs below.

### Stake BETR

```
1. get_wallets → address
2. GET https://betrmint.fun/api/plugin/betrmint/read/token?wallet=<address>  → confirm balance and staking state
3. GET https://betrmint.fun/api/plugin/betrmint/prepare/stake?from=<address>&amount=<decimal>
4. send_calls(chain="base", calls from transactions[])
5. User approves → get_request_status(requestId)
```

### Claim staking rewards

```
1. get_wallets → address
2. GET https://betrmint.fun/api/plugin/betrmint/read/token?wallet=<address>  → confirm rewardsClaimable > 0
3. GET https://betrmint.fun/api/plugin/betrmint/prepare/claim-rewards?from=<address>
4. send_calls(...)
5. get_request_status(requestId)
```

### Mint, spin, and win (running round)

```
1. get_wallets → address
2. GET https://betrmint.fun/api/plugin/betrmint/read/round?wallet=<address>  → confirm isLive and note slug
3. GET https://betrmint.fun/api/plugin/betrmint/prepare/mint?from=<address>&quantity=<n>  (slug optional)
4. send_calls(...) → user approves mint
5. Poll GET https://betrmint.fun/api/plugin/betrmint/read/round?wallet=<address> until pendingDraws is 0 and readyToWin is true
6. GET https://betrmint.fun/api/plugin/betrmint/prepare/win?from=<address>
7. send_calls(...) → user approves prize claim
8. get_request_status(requestId)
```

### Explain BETR / BETRMINT (no transaction)

```
1. GET https://betrmint.fun/api/plugin/betrmint/read/token?wallet=<address>
2. GET https://betrmint.fun/api/plugin/betrmint/read/round?wallet=<address>
3. Summarize: token balances, APY context, live round status, mint URL in data.mintSpinWinUrl
```

## Submission

Target tool: **`send_calls`**. Map every `transactions[*]` item from a prepare response into the `calls` array:

```json
{
  "chain": "base",
  "calls": [
    { "to": "<tx.to>", "value": "<tx.value>", "data": "<tx.data>" }
  ]
}
```

- `value` defaults to `0x0` if omitted.
- Execute the full batch in one approval — steps are ordered (`approve` before the protocol action).
- Map `chainId: 8453` to `chain: "base"`.
- After `send_calls`, present the approval URL and poll `get_request_status(requestId)` until confirmed. See approval-mode.md.

## Example Prompts

### "Stake 1000 BETR for me"

1. `get_wallets` → address
2. `GET https://betrmint.fun/api/plugin/betrmint/read/token?wallet=<address>` → confirm balance ≥ 1000
3. `GET https://betrmint.fun/api/plugin/betrmint/prepare/stake?from=<address>&amount=1000`
4. `send_calls(chain="base", calls from transactions[])`
5. User approves → `get_request_status(requestId)`

### "Claim my staking rewards"

1. `get_wallets` → address
2. `GET https://betrmint.fun/api/plugin/betrmint/read/token?wallet=<address>` → confirm `rewardsClaimable > 0`
3. `GET https://betrmint.fun/api/plugin/betrmint/prepare/claim-rewards?from=<address>`
4. `send_calls(...)` → poll status

### "Mint 2 tickets in the current round"

1. `get_wallets` → address
2. `GET https://betrmint.fun/api/plugin/betrmint/read/round?wallet=<address>` → confirm `isLive`, note slug
3. `GET https://betrmint.fun/api/plugin/betrmint/prepare/mint?from=<address>&quantity=2`
4. `send_calls(...)` → user approves
5. Poll `GET https://betrmint.fun/api/plugin/betrmint/read/round?wallet=<address>` until `readyToWin: true`
6. `GET https://betrmint.fun/api/plugin/betrmint/prepare/win?from=<address>` → `send_calls(...)`

### "What's my BETR balance and is there a live round?" (read-only)

1. `get_wallets` → address
2. `GET https://betrmint.fun/api/plugin/betrmint/read/token?wallet=<address>` and `GET https://betrmint.fun/api/plugin/betrmint/read/round?wallet=<address>`
3. Summarize balances, staking APY context, and round status (no `send_calls`)

## Risks & Warnings

- **irreversible** — Stake, mint, claim, and win transactions cannot be undone once confirmed on-chain. Always confirm the amount, round slug, and wallet with the user before calling `send_calls`. Never auto-submit without explicit approval.

## Notes

### Mainnet contracts

| Contract | Address |
| -------- | ------- |
| $BETR token | `0x051024B653E8ec69E72693F776c41C2A9401FB07` |
| Staking | `0x808a12766632b456a74834F2FA8aE06DFC7482f1` |
| Staking rewards | `0x2Fb46818b6A5F6fC349D2f73d145BeD6FCc58DB0` |
| Round factory | `0x81D7C584569EB51C42FBeDd647dB9eA152Dafa1b` |

- **Spin animation** is off-chain UI; on-chain flow is `mint` → wait for settlement → `win`.
- **Daily stake spin bonuses** (`/stake/claim/...`) use signed airdrops and are separate from on-chain `claim-rewards`; this plugin covers on-chain staking rewards only.
- Legacy rounds (version ≤ 1.7) omit the referral argument on `mint`.
- [Base Custom Plugins](https://docs.base.org/ai-agents/plugins/custom-plugins)
- [BETRMINT](https://betrmint.fun)
