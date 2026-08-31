---
title: "Aave Plugin"
description: "Lending and borrowing on Aave v3 via GraphQL API → send_calls on Base, Ethereum, Arbitrum, Optimism, Polygon, and Avalanche."
tags: [lending, borrowing, yield, vaults]
name: aave
version: 0.2.0
integration: http-api
chains: [base, ethereum, arbitrum, optimism, polygon, avalanche, bsc]
requires:
  shell: none
  allowlist: [api.v3.aave.com]
  externalMcp: null
  cliPackage: null
auth: none
risk: [liquidation, irreversible]
---

# Aave Plugin

> [!IMPORTANT]
> Run Base MCP onboarding first (see SKILL.md) before any Aave operation. Ensure your wallet is connected — supply, borrow, repay, and withdraw all require signing transactions via `send_calls`.

## Overview

Aave v3 is a decentralized, non-custodial liquidity protocol where users supply assets to earn yield or borrow assets against collateral. It is deployed across Base, Ethereum, Arbitrum, Optimism, Polygon, and Avalanche. This plugin queries the Aave GraphQL API (`https://api.v3.aave.com/graphql`) to read market data, resolve market addresses dynamically by chain ID, and build unsigned calldata for supply, borrow, repay, and withdraw operations — then submits them as unsigned `{ to, value, data }` calls via Base MCP `send_calls`.

## Surface Routing

| Capability | Claude Code / Codex / Cursor (harness HTTP) | Claude.ai / ChatGPT (`web_request`) |
|---|---|---|
| Read markets & user positions | Harness HTTP tool → `api.v3.aave.com` | `web_request` → `api.v3.aave.com` (allowlisted) |
| Supply / Borrow / Repay / Withdraw | Harness HTTP tool → build calldata → `send_calls` | `web_request` → build calldata → `send_calls` approval flow |

All write operations require user approval through the Base MCP approval flow. See [approval-mode.md](../references/approval-mode.md).

## Endpoints

All operations are POST requests to `https://api.v3.aave.com/graphql` with `Content-Type: application/json`.

### Discover Markets

Resolves the market contract address and user state (health factor, net worth, available borrows) for a given chain.

```graphql
query {
  markets(
    request: {
      chainIds: [8453]
      user: "0x<wallet-address>"  # include to fetch userState
    }
  ) {
    name
    address
    chain { chainId name }
    userState {
      healthFactor
      netWorth
      availableBorrowsBase
      totalCollateralBase
      totalDebtBase
      ltv { value formatted }
      currentLiquidationThreshold { value formatted }
    }
    reserves {
      underlyingToken { symbol address decimals }
      supplyAPY { formatted }
      variableBorrowAPY { formatted }
      isFrozen
      isPaused
      usageAsCollateralEnabled
      userState {
        suppliable { amount { value raw decimals } }
        supplied { amount { value raw decimals } }
        borrowed { amount { value raw decimals } }
        isCollateral
      }
    }
  }
}
```

Response key fields:
- `markets[].address` — the market contract address to use in transaction queries
- `markets[].userState.healthFactor` — `"∞"` when no debt; values below `1.0` are liquidatable
- `markets[].reserves[].userState.suppliable.amount.value` — human-readable token amount available to supply

### Build Supply Calldata

Returns an `ExecutionPlan` union: `TransactionRequest`, `ApprovalRequired`, or `InsufficientBalanceError`.

```graphql
query {
  supply(
    request: {
      market: "0x<market-address>"
      amount: {
        erc20: {
          currency: "0x<underlying-token-address>"
          value: "42"           # human-readable decimal, e.g. "42" for 42 USDC
        }
        # native: "0.5"        # use instead of erc20 to supply chain native token (e.g. ETH)
      }
      sender: "0x<wallet-address>"
      chainId: 8453
    }
  ) {
    __typename
    ... on TransactionRequest {
      to from data value chainId operation
    }
    ... on ApprovalRequired {
      reason
      requiredAmount { value decimals }
      currentAllowance { value decimals }
      approval { to from data value chainId operation }
      originalTransaction { to from data value chainId operation }
    }
    ... on InsufficientBalanceError {
      required { value decimals }
      available { value decimals }
    }
  }
}
```

### Build Borrow Calldata

Same `ExecutionPlan` response shape as supply.

```graphql
query {
  borrow(
    request: {
      market: "0x<market-address>"
      amount: {
        erc20: {
          currency: "0x<underlying-token-address>"
          value: "100"
        }
      }
      sender: "0x<wallet-address>"
      chainId: 8453
    }
  ) {
    __typename
    ... on TransactionRequest {
      to from data value chainId operation
    }
    ... on ApprovalRequired {
      approval { to from data value chainId operation }
      originalTransaction { to from data value chainId operation }
    }
    ... on InsufficientBalanceError {
      required { value decimals }
      available { value decimals }
    }
  }
}
```

### Build Repay Calldata

Use `value: { exact: "1" }` to repay a specific amount, or `value: { max: true }` to repay the full debt.

```graphql
query {
  repay(
    request: {
      market: "0x<market-address>"
      amount: {
        erc20: {
          currency: "0x<underlying-token-address>"
          value: { exact: "50" }  # or: { max: true }
        }
      }
      sender: "0x<wallet-address>"
      chainId: 8453
    }
  ) {
    __typename
    ... on TransactionRequest {
      to from data value chainId operation
    }
    ... on ApprovalRequired {
      approval { to from data value chainId operation }
      originalTransaction { to from data value chainId operation }
    }
    ... on InsufficientBalanceError {
      required { value decimals }
      available { value decimals }
    }
  }
}
```

### Build Withdraw Calldata

Use `value: { exact: "2" }` or `value: { max: true }` to withdraw all.

```graphql
query {
  withdraw(
    request: {
      market: "0x<market-address>"
      amount: {
        erc20: {
          currency: "0x<underlying-token-address>"
          value: { exact: "2" }  # or: { max: true }
        }
      }
      sender: "0x<wallet-address>"
      chainId: 8453
    }
  ) {
    __typename
    ... on TransactionRequest {
      to from data value chainId operation
    }
    ... on ApprovalRequired {
      approval { to from data value chainId operation }
      originalTransaction { to from data value chainId operation }
    }
    ... on InsufficientBalanceError {
      required { value decimals }
      available { value decimals }
    }
  }
}
```

### Poll for Confirmation

After submission, poll until `true` to confirm the API has indexed the transaction before re-reading state.

```graphql
query {
  value: hasProcessedKnownTransaction(
    request: { operations: [SUPPLY], txHash: "0x<tx-hash>" }
  )
}
```

Valid `operations` values: `SUPPLY`, `BORROW`, `REPAY`, `WITHDRAW`.

## Orchestration

### Supply

1. Call `get_wallets` to retrieve the user's wallet address.
2. Determine the target chain from the user's request; map it to the Base MCP chain string and numeric chain ID (see [Notes](#notes)).
3. Query `markets` with `chainIds: [<chainId>]` and `user: <wallet>` to fetch the market contract address, available reserves, and per-reserve `userState`.
4. Locate the target reserve by token symbol. Confirm:
   - `reserve.isFrozen === false`
   - `reserve.isPaused === false`
   - `reserve.userState.suppliable.amount.value > 0`
5. Query `supply` with the market address, token address, amount, sender, and chainId.
6. Handle the `ExecutionPlan`:
   - `TransactionRequest` → proceed to step 7 with a single call.
   - `ApprovalRequired` → proceed to step 7 with both `approval` and `originalTransaction` batched in that order.
   - `InsufficientBalanceError` → stop; report the required vs. available amounts to the user.
7. Submit via `send_calls` (see [Submission](#submission)). Confirm approval with the user before sending.
8. After the transaction is confirmed on-chain, poll `hasProcessedKnownTransaction` with operation `SUPPLY` until it returns `true`.

### Borrow

1. Call `get_wallets`.
2. Map chain to chain ID.
3. Query `markets` with user address. Read `userState.healthFactor`, `userState.availableBorrowsBase`, and the reserve's `variableBorrowAPY`.
4. Validate that `availableBorrowsBase > 0`. Estimate the post-borrow health factor; warn the user if it would fall below `1.5` (Aave liquidates at `< 1.0`).
5. Query `borrow` with market address, token address, amount, sender, and chainId.
6. Handle `ExecutionPlan` (same as supply step 6).
7. Present the borrow summary (amount, APY, projected health factor) and confirm with the user before calling `send_calls`.
8. Submit, then poll `hasProcessedKnownTransaction` with operation `BORROW`.

### Repay

1. Call `get_wallets`.
2. Map chain to chain ID.
3. Query `markets` with user to get the borrowed position for the target token (`reserve.userState.borrowed.amount.value`). If `borrowed == 0`, stop and inform the user.
4. Query `repay` with the desired amount (exact or max).
5. Handle `ExecutionPlan` — repay typically returns `ApprovalRequired` because the protocol needs allowance to pull debt tokens from the wallet.
6. Confirm the repayment amount and approval with the user, then submit via `send_calls`.
7. Poll `hasProcessedKnownTransaction` with operation `REPAY`.

### Withdraw

1. Call `get_wallets`.
2. Map chain to chain ID.
3. Query `markets` with user. Read `reserve.userState.supplied.amount.value` for the target token and the current `userState.healthFactor`.
4. Estimate post-withdrawal health factor. If the user has outstanding debt and the withdrawal would push health factor below `1.1`, warn and offer to proceed with a reduced amount.
5. Query `withdraw` with the desired amount (exact or max).
6. Handle `ExecutionPlan`.
7. Confirm with the user, then submit via `send_calls`.
8. Poll `hasProcessedKnownTransaction` with operation `WITHDRAW`.

## Submission

Target tool: **`send_calls`**

Map `TransactionRequest` fields to `send_calls`:

| `TransactionRequest` field | `send_calls` field | Notes |
|---|---|---|
| `to` | `to` | Pool contract address |
| `data` | `data` | ABI-encoded calldata |
| `value` | `value` | Wei; `"0"` for ERC-20 operations |
| `chainId` | `chain` | Convert via chain ID map in [Notes](#notes) |

When `ExecutionPlan.__typename === "ApprovalRequired"`, batch the approval before the action in a single `send_calls` call (EIP-5792):

```json
[
  { "to": "<approval.to>", "data": "<approval.data>", "value": "<approval.value>" },
  { "to": "<originalTransaction.to>", "data": "<originalTransaction.data>", "value": "<originalTransaction.value>" }
]
```

Both calls use the same `chain` string. Never reorder — the approval must execute before the action.

See [batch-calls.md](../references/batch-calls.md) for the full `send_calls` payload structure and [approval-mode.md](../references/approval-mode.md) for the approval/polling flow.

## Example Prompts

**"What is my Aave position on Base?"**

1. Call `get_wallets` to get the wallet address.
2. Query `markets` with `chainIds: [8453]` and `user: <wallet>`.
3. Read `userState.healthFactor`, `userState.netWorth`, `userState.totalCollateralBase`, `userState.totalDebtBase`, and per-reserve `userState.supplied` / `userState.borrowed`.
4. Report a summary: supplied assets, borrowed assets, current APYs, and health factor.

---

**"Supply 500 USDC to Aave on Base"**

1. Call `get_wallets`.
2. Query `markets` with `chainIds: [8453]`, `user: <wallet>`. Locate the USDC reserve; confirm `isFrozen: false`, `isPaused: false`, `suppliable > 500`.
3. Query `supply` with market address, USDC token address (`value: "500"`), sender, `chainId: 8453`.
4. If `ApprovalRequired`, batch `[approval, originalTransaction]`; if `TransactionRequest`, use a single call.
5. Confirm the action with the user (amount, current supply APY), then call `send_calls` with `chain: "base"`.
6. Poll `hasProcessedKnownTransaction` with operation `SUPPLY` until `true`, then report confirmation.

---

**"Borrow 0.1 ETH on Aave using my USDC collateral on Base"**

1. Call `get_wallets`.
2. Query `markets` with `chainIds: [8453]`, `user: <wallet>`. Read `availableBorrowsBase` and `healthFactor`.
3. Estimate post-borrow health factor; if it would fall below `1.5`, warn the user.
4. Query `borrow` with the WETH reserve address, `value: "0.1"`, `chainId: 8453`.
5. Present: borrow amount, variable APY, projected health factor. Confirm with user.
6. Submit via `send_calls` with `chain: "base"`.
7. Poll `hasProcessedKnownTransaction` with operation `BORROW`.

---

**"Repay my full USDC debt on Aave on Ethereum"**

1. Call `get_wallets`.
2. Query `markets` with `chainIds: [1]`, `user: <wallet>`. Read USDC `userState.borrowed`. If zero, stop.
3. Query `repay` with `value: { max: true }`, USDC address, `chainId: 1`.
4. The response is typically `ApprovalRequired` — batch `[approval, originalTransaction]`.
5. Confirm repayment amount and approval with user, then `send_calls` with `chain: "ethereum"`.
6. Poll `hasProcessedKnownTransaction` with operation `REPAY`.

## Risks & Warnings

- **Liquidation**: Borrow positions are subject to liquidation if the health factor falls below `1.0`. Always compute the projected post-action health factor before submitting a borrow or withdrawal. Warn the user if the resulting health factor falls below `1.5`. Never borrow an amount that would bring health factor below `1.1` without explicit user confirmation.
- **Irreversible**: All supply, borrow, repay, and withdraw transactions are onchain and cannot be undone once submitted. Require explicit user confirmation with a summary of the action (amount, asset, chain, estimated APY impact) before calling `send_calls`.

## Notes

### Chain ID → Base MCP Chain String

| Chain | Chain ID | Base MCP `chain` string |
|---|---|---|
| Ethereum | 1 | `ethereum` |
| Optimism | 10 | `optimism` |
| Polygon | 137 | `polygon` |
| Arbitrum One | 42161 | `arbitrum` |
| Avalanche C-Chain | 43114 | `avalanche` |
| Base | 8453 | `base` |
| BNB Chain | 56 | `bsc` |

### Market Contract Addresses (reference only — use `markets` query to resolve dynamically)

| Chain | Market Name | Pool Address |
|---|---|---|
| Ethereum | Aave v3 Ethereum | `0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2` |
| Base | Base V3 Market | resolved via `markets` query with `chainIds: [8453]` |
| Arbitrum | Aave v3 Arbitrum | resolved via `markets` query with `chainIds: [42161]` |
| Optimism | Aave v3 Optimism | resolved via `markets` query with `chainIds: [10]` |

Always resolve market addresses dynamically via the `markets` query rather than hardcoding them. The API may add or update markets.

### Amount Encoding

- `supply` and `borrow` `amount.value` is a human-readable decimal string (e.g. `"42"` for 42 USDC, `"0.5"` for 0.5 ETH).
- `repay` and `withdraw` accept either `{ exact: "<decimal>" }` or `{ max: true }` inside `value`.
- `TransactionRequest.value` is in **wei** (BigInt string) — pass directly to `send_calls` without conversion.

### Transaction Monitoring

Poll `hasProcessedKnownTransaction` after each `send_calls` submission. The API may serve stale cached state for several seconds after an on-chain transaction. Only re-read positions after this query returns `true`.
