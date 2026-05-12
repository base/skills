# Subscriptions (Recurring Payments)

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Backend Setup: CDP Owner Wallet](#backend-setup-cdp-owner-wallet)
- [Frontend: Create a Subscription](#frontend-create-a-subscription)
- [Backend: Check Subscription Status](#backend-check-subscription-status)
- [Backend: Charge a Subscription](#backend-charge-a-subscription)
- [Backend: Cancel a Subscription](#backend-cancel-a-subscription)
- [Advanced: Manual Execution](#advanced-manual-execution)
- [Fund Routing Patterns](#fund-routing-patterns)
- [Testing](#testing)

## Overview

Recurring payments use **Spend Permissions** — an onchain primitive that lets a user grant revocable spending rights to your app. The user approves once, and your backend charges periodically without further user interaction.

Key properties:
- Spending limit auto-resets each period (no rollover between periods)
- User can cancel anytime from their wallet
- USDC only (on Base Mainnet and Base Sepolia)
- Requires both client-side (subscribe) and server-side (charge/revoke) code

## Architecture

```
Client (browser)                    Server (Node.js)
─────────────────                   ────────────────
subscribe() ──────────────────────> Store subscription ID
                                    ↓
                                    getStatus() → check if chargeable
                                    ↓
                                    charge() → execute periodic charge
                                    ↓
                                    revoke() → cancel when needed
```

The server uses a **CDP (Coinbase Developer Platform) smart wallet** to act as the subscription owner (the entity authorized to spend).

## Backend Setup: CDP Owner Wallet

### Environment Variables

```bash
CDP_API_KEY_ID=your-api-key-id
CDP_API_KEY_SECRET=your-api-key-secret
CDP_WALLET_SECRET=your-wallet-secret
PAYMASTER_URL=https://your-paymaster.xyz  # optional, for gasless transactions
```

Get these from [Coinbase Developer Platform](https://portal.cdp.coinbase.com).

### Create or Retrieve the Owner Wallet

```typescript
import { base } from '@base-org/account/node';

const wallet = await base.subscription.getOrCreateSubscriptionOwnerWallet({
  walletName: 'my-app-subscriptions',
});
// wallet.address → share this with the frontend as subscriptionOwner
// wallet.walletName → must match across charge() and revoke() calls
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `walletName` | `string` | No | Wallet identifier (default: `"subscription owner"`) |
| `cdpApiKeyId` | `string` | No | Falls back to `CDP_API_KEY_ID` env var |
| `cdpApiKeySecret` | `string` | No | Falls back to `CDP_API_KEY_SECRET` env var |
| `cdpWalletSecret` | `string` | No | Falls back to `CDP_WALLET_SECRET` env var |

Returns: `{ address, walletName, eoaAddress }`

This is **idempotent** — the same `walletName` always returns the same wallet. The `address` is the CDP smart wallet address (safe to share publicly as `subscriptionOwner`).

**Never expose CDP credentials client-side.** Only the wallet `address` is public.

## Frontend: Create a Subscription

```typescript
import { base } from '@base-org/account';

const subscription = await base.subscription.subscribe({
  recurringCharge: '9.99',
  subscriptionOwner: '0xYourCDPWalletAddress',
  periodInDays: 30,
  testnet: false,
});
// subscription.id → store this as the subscription identifier
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `recurringCharge` | `string` | Yes | USDC amount per period (max 6 decimals) |
| `subscriptionOwner` | `string` | Yes | Your CDP wallet address |
| `periodInDays` | `number` | No | Charge period in days (default: `30`) |
| `testnet` | `boolean` | No | Use testnet (default: `false`) |
| `requireBalance` | `boolean` | No | Check payer balance first (default: `true`) |

Returns `SubscriptionResult`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Permission hash (subscription identifier) |
| `subscriptionOwner` | `string` | Your app's wallet address |
| `subscriptionPayer` | `string` | The user's wallet address |
| `recurringCharge` | `string` | Amount in USD |
| `periodInDays` | `number` | Period length |

## Backend: Check Subscription Status

```typescript
import { base } from '@base-org/account';

const status = await base.subscription.getStatus({
  id: subscriptionId,
  testnet: false,
});
```

| Parameter | Type | Required |
|-----------|------|----------|
| `id` | `string` | Yes |
| `testnet` | `boolean` | No |

Returns `SubscriptionStatus`:

| Field | Type | Description |
|-------|------|-------------|
| `isSubscribed` | `boolean` | Whether subscription is active |
| `recurringCharge` | `string` | Charge amount |
| `remainingChargeInPeriod` | `string` | How much can still be charged this period |
| `currentPeriodStart` | `Date` | — |
| `nextPeriodStart` | `Date` | — |
| `periodInDays` | `number` | — |

Check before charging:

```typescript
const status = await base.subscription.getStatus({ id: subscriptionId });
if (status.isSubscribed && parseFloat(status.remainingChargeInPeriod!) > 0) {
  // safe to charge
}
```

## Backend: Charge a Subscription

```typescript
import { base } from '@base-org/account/node';

const result = await base.subscription.charge({
  id: subscriptionId,
  amount: 'max-remaining-charge',
  paymasterUrl: process.env.PAYMASTER_URL,
  testnet: false,
});
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | `string` | Yes | Subscription ID |
| `amount` | `string \| 'max-remaining-charge'` | Yes | USDC amount or `'max-remaining-charge'` |
| `paymasterUrl` | `string` | No | For gasless transactions |
| `recipient` | `string` | No | Send USDC to a different address (default: stays in CDP wallet) |
| `testnet` | `boolean` | No | Default: `false` |
| `walletName` | `string` | No | Must match the wallet used in setup |

Returns: `{ success, id, subscriptionId, amount, subscriptionOwner, recipient }`

`charge()` handles all transaction details: gas estimation, nonce management, and signing.

## Backend: Cancel a Subscription

```typescript
import { base } from '@base-org/account/node';

const result = await base.subscription.revoke({
  id: subscriptionId,
  paymasterUrl: process.env.PAYMASTER_URL,
  testnet: false,
});
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | `string` | Yes | Subscription ID |
| `paymasterUrl` | `string` | No | For gasless transactions |
| `testnet` | `boolean` | No | Default: `false` |
| `walletName` | `string` | No | Must match the wallet used in setup |

Returns: `{ success, id, subscriptionId, subscriptionOwner }`

Revoking is **permanent**. The user would need to create a new subscription.

## Advanced: Manual Execution

For custom wallet infrastructure (not using CDP wallets), use `prepareCharge` and `prepareRevoke` to get raw call data.

### `prepareCharge()`

```typescript
import { base } from '@base-org/account';

const calls = await base.subscription.prepareCharge({
  id: subscriptionId,
  amount: 'max-remaining-charge',
  testnet: false,
});
// calls → Array<{ to, data, value: '0x0' }>
// Execute via wallet_sendCalls or eth_sendTransaction
```

### `prepareRevoke()`

```typescript
const call = await base.subscription.prepareRevoke({
  id: subscriptionId,
  testnet: false,
});
// call → { to, data, value: '0x0' }
```

## Fund Routing Patterns

| Pattern | How | When |
|---------|-----|------|
| Default | Omit `recipient` | USDC stays in CDP wallet |
| Treasury | `recipient: '0xTreasury'` | Auto-transfer to treasury |
| Dynamic | Set `recipient` per charge | Route to different addresses based on plan type |

## Testing

- Use `testnet: true` in all calls (`subscribe`, `getStatus`, `charge`, `revoke`)
- Use `periodInDays: 1` for faster testing cycles
- Test on Base Sepolia (chain ID 84532)
- Get test USDC from the [Circle Faucet](https://faucet.circle.com/)
