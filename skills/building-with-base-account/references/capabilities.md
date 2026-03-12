# Capabilities & Batch Transactions

## Table of Contents

- [Overview](#overview)
- [Discovering Capabilities](#discovering-capabilities)
- [wallet_sendCalls](#wallet_sendcalls)
- [wallet_getCallsStatus](#wallet_getcallsstatus)
- [Capability: paymasterService](#capability-paymasterservice)
- [Capability: auxiliaryFunds](#capability-auxiliaryfunds)
- [Capability: atomic](#capability-atomic)
- [Capability: flowControl](#capability-flowcontrol)
- [Capability: dataCallback](#capability-datacallback)
- [Capability: dataSuffix (Attribution)](#capability-datasuffix-attribution)

## Overview

Capabilities are chain-specific feature flags that describe what a wallet supports. They're discovered via `wallet_getCapabilities` and used in `wallet_connect` and `wallet_sendCalls` calls.

Base Account (a smart wallet) supports capabilities that traditional wallets (EOAs) cannot: atomic batching, gas sponsorship, auxiliary funds, etc.

## Discovering Capabilities

```typescript
const capabilities = await provider.request({
  method: 'wallet_getCapabilities',
  params: [userAddress],
});

const baseCapabilities = capabilities['0x2105']; // Base Mainnet
```

Response structure (keyed by hex chain ID):

```typescript
{
  "0x2105": {
    auxiliaryFunds: { supported: true },
    atomic: { supported: "supported" },
    paymasterService: { supported: true },
    flowControl: { supported: false },
    datacallback: { supported: false },
  }
}
```

Use this to conditionally enable features:

```typescript
const hasPaymaster = !!baseCapabilities.paymasterService?.supported;
const hasAuxFunds = baseCapabilities.auxiliaryFunds?.supported || false;
const hasAtomicBatch = baseCapabilities.atomic?.supported === 'supported';
```

## wallet_sendCalls

**Spec: EIP-5792.** Submits a batch of calls to the wallet for execution.

```typescript
const { batchId } = await provider.request({
  method: 'wallet_sendCalls',
  params: [{
    version: '2.0.0',
    from: userAddress,
    chainId: '0x2105',
    atomicRequired: true,
    calls: [
      { to: '0xTokenAddress', data: '0xapproveCalldata', value: '0x0' },
      { to: '0xDexAddress', data: '0xswapCalldata', value: '0x0' },
    ],
    capabilities: {
      paymasterService: { url: 'https://your-paymaster.xyz' },
    },
  }],
});
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `version` | `string` | Yes | Must be `"2.0.0"` |
| `from` | `string` | Yes | Sender address |
| `chainId` | `string` | Yes | Hex chain ID |
| `atomicRequired` | `boolean` | Yes | Require all-or-nothing execution |
| `calls` | `Call[]` | Yes | Array of `{ to, value, data? }` |
| `capabilities` | `object` | No | Capability config |

Returns: `{ batchId, status }`

Error codes:

| Code | Meaning |
|------|---------|
| `4001` | User rejected |
| `5700` | Missing required capability |
| `5720` | Duplicate batch ID |
| `5740` | Batch too large |

## wallet_getCallsStatus

Check the status of a batch submitted via `wallet_sendCalls`.

```typescript
const result = await provider.request({
  method: 'wallet_getCallsStatus',
  params: [batchId],
});
```

Status codes:

| Code | Meaning |
|------|---------|
| `100` | Pending — received, not yet onchain |
| `200` | Success — included onchain, no reverts |
| `400` | Offchain failure — wallet will not retry |
| `500` | Chain failure — batch reverted |
| `600` | Partial failure — some changes may be onchain |

Returns: `{ version, chainId, id, status, atomic, receipts, capabilities }`

Polling pattern:

```typescript
async function waitForBatch(batchId: string) {
  while (true) {
    const { status, receipts } = await provider.request({
      method: 'wallet_getCallsStatus',
      params: [batchId],
    });
    if (status !== 100) return { status, receipts };
    await new Promise(r => setTimeout(r, 1000));
  }
}
```

## Capability: paymasterService

**Spec: ERC-7677.** Sponsors gas fees so users transact for free.

```typescript
capabilities: {
  paymasterService: {
    url: 'https://your-paymaster-service.xyz',
  },
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | `string` | Yes | HTTPS URL of an ERC-7677-compliant paymaster |

The paymaster service must implement:
- `pm_getPaymasterStubData` — for gas estimation
- `pm_getPaymasterData` — for actual UserOp paymaster data

Get a paymaster URL from [Coinbase Developer Platform](https://portal.cdp.coinbase.com). See also the [Base Gasless Campaign](https://docs.base.org/base-account/more/base-gasless-campaign) for gas credits.

Best practice: handle failures gracefully with a fallback to regular (user-pays-gas) transactions.

## Capability: auxiliaryFunds

**Spec: EIP-5792.** Indicates the wallet has access to funds beyond the visible onchain balance (MagicSpend — use Coinbase balances onchain).

No configuration parameters — it's a support flag only.

When `auxiliaryFunds.supported === true`:
- **Do not** block transactions based on visible onchain balance
- **Do not** show "insufficient funds" warnings based on balance checks
- Let the wallet handle funding — it can pull from the user's Coinbase account

```typescript
if (baseCapabilities.auxiliaryFunds?.supported) {
  // Skip balance check, let wallet handle it
} else {
  // Traditional balance check
  const balance = await client.getBalance({ address: userAddress });
  if (balance < requiredAmount) showInsufficientFundsWarning();
}
```

## Capability: atomic

**Spec: EIP-5792.** Ensures batched calls execute atomically — all succeed or all revert.

Support values (string, not boolean):

| Value | Meaning |
|-------|---------|
| `"supported"` | Wallet executes atomically |
| `"ready"` | Wallet can upgrade to atomic via EIP-7702 |
| `"unsupported"` | No atomicity guarantees |

Set `atomicRequired: true` in `wallet_sendCalls` to enforce atomic execution. If the wallet doesn't support it, the call fails with error `5700`.

Use cases: approve + swap, mint + pay, any multi-step flow requiring all-or-nothing.

## Capability: flowControl

**Spec: ERC-7867 (proposed, not finalized).** Controls behavior when individual calls in a batch fail.

```typescript
calls: [{
  to: '0x...',
  data: '0x...',
  flowControl: {
    onFailure: 'continue',
    fallbackCall: { to: '0xFallback', data: '0x...' },
  },
}]
```

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `onFailure` | `string` | `'continue'`, `'stop'`, `'retry'` | What to do when this call reverts |
| `fallbackCall` | `object` | `{ to, value?, data? }` | Optional alternative call to execute on failure |

**Note:** This spec is actively being developed. Check the latest docs before using.

## Capability: dataCallback

Collects user profile information (email, phone, address) during transaction flows. Same mechanism as `payerInfo` in `pay()` but for `wallet_sendCalls`.

```typescript
capabilities: {
  dataCallback: {
    requests: [
      { type: 'email' },
      { type: 'name', optional: true },
    ],
    callbackURL: 'https://your-api.com/validate',
  },
}
```

Request types: `'email'`, `'phoneNumber'`, `'physicalAddress'`, `'name'`

The `callbackURL` receives a POST with user data before the transaction. Respond with `{ request: requestData }` to accept or `{ errors: { email: 'Invalid' } }` to reject.

## Capability: dataSuffix (Attribution)

**Spec: ERC-8021.** Appends arbitrary bytes to transaction calldata for attribution tracking. Used primarily with **Builder Codes** for tracking which app generated a transaction.

```typescript
import { Attribution } from 'ox/erc8021';

const builderCodeSuffix = Attribution.toDataSuffix({
  codes: ['bc_foobar'], // Register at base.dev
});

capabilities: {
  dataSuffix: {
    value: builderCodeSuffix,
    optional: true,
  },
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `value` | `0x${string}` | Yes | Hex bytes to append to calldata |
| `optional` | `boolean` | No | If `true`, wallet may ignore if unsupported |

Best practice: use `optional: true` if your app functions without attribution. Register for a Builder Code at [base.dev](https://base.dev). Keep suffixes small — larger means more gas.
