# Payments (Base Pay)

## Table of Contents

- [Overview](#overview)
- [One-Time Payments](#one-time-payments)
- [Checking Payment Status](#checking-payment-status)
- [Collecting User Info (payerInfo)](#collecting-user-info-payerinfo)
- [Server-Side Verification](#server-side-verification)
- [Server-Side User Info Validation](#server-side-user-info-validation)
- [BasePayButton Component](#basepaybutton-component)
- [Framework Integration: Wagmi](#framework-integration-wagmi)
- [Testing](#testing)
- [Security Checklist](#security-checklist)

## Overview

Base Pay enables one-tap USDC payments on Base. Key facts:

- Currency is USDC (a digital dollar stablecoin), not ETH
- Gas is sponsored automatically — users don't pay gas fees
- Settles in under 2 seconds on Base
- No chargebacks, no FX fees, no merchant fees
- **Base Pay works independently from Sign in with Base** — no authentication required to call `pay()`
- Users can pay from their Base Account or Coinbase account

## One-Time Payments

### `pay()`

```typescript
import { pay } from '@base-org/account';

const payment = await pay({
  amount: '10.50',
  to: '0xRecipientAddress',
  testnet: false,
});
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `amount` | `string` | Yes | USDC amount (e.g., `"10.50"`) |
| `to` | `string` | Yes | Recipient Ethereum address (`0x...`) |
| `testnet` | `boolean` | No | Use Base Sepolia testnet (default: `false`) |
| `payerInfo` | `object` | No | Collect user info during payment — see [payerInfo section](#collecting-user-info-payerinfo) |

Returns `PayResult`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Transaction hash |
| `amount` | `string` | Amount sent |
| `to` | `string` | Recipient address |
| `payerInfoResponses` | `object` | Collected user info (if `payerInfo` was provided) |

## Checking Payment Status

### `getPaymentStatus()`

```typescript
import { getPaymentStatus } from '@base-org/account';

const status = await getPaymentStatus({
  id: payment.id,
  testnet: false,
});
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | `string` | Yes | Transaction hash from `pay()` |
| `testnet` | `boolean` | No | **Must match** the `testnet` value used in `pay()` |

Returns `PaymentStatus`:

| Field | Type | Present When |
|-------|------|-------------|
| `status` | `"completed" \| "pending" \| "failed" \| "not_found"` | Always |
| `id` | `string` | Always |
| `message` | `string` | Always |
| `sender` | `string` | `pending`, `completed`, `failed` |
| `amount` | `string` | `completed` |
| `recipient` | `string` | `completed` |
| `error` | `object` | `failed` |

## Collecting User Info (payerInfo)

Request user information (email, name, phone, address) during the payment flow.

```typescript
const payment = await pay({
  amount: '25.00',
  to: '0xRecipient',
  payerInfo: {
    requests: [
      { type: 'email' },
      { type: 'phoneNumber', optional: true },
      { type: 'physicalAddress', optional: true },
    ],
    callbackURL: 'https://your-api.com/validate',
  },
});
```

Supported `payerInfo` request types:

| Type | Response Shape |
|------|---------------|
| `email` | `string` |
| `name` | `{ firstName: string, familyName: string }` |
| `phoneNumber` | `{ number: string, country: string }` |
| `physicalAddress` | `{ address1, address2?, city, state, postalCode, country, name: { firstName, familyName } }` |
| `onchainAddress` | `string` |

Fields are **required by default**. Set `optional: true` to avoid aborting the payment if the user declines to share.

## Server-Side Verification

Never trust frontend payment confirmations alone. Always verify on your backend.

```typescript
import { getPaymentStatus } from '@base-org/account';

async function verifyPayment(txId: string, expectedAmount: string, expectedRecipient: string, authenticatedUser: string) {
  // 1. Check if already processed (dedup by txId)
  if (await isProcessed(txId)) throw new Error('Already processed');

  // 2. Verify payment status
  const { status, sender, amount, recipient } = await getPaymentStatus({ id: txId });
  if (status !== 'completed') throw new Error(`Payment not completed: ${status}`);

  // 3. Verify sender matches authenticated user (prevents impersonation)
  if (sender.toLowerCase() !== authenticatedUser.toLowerCase()) {
    throw new Error('Sender mismatch');
  }

  // 4. Validate amount and recipient
  if (amount !== expectedAmount || recipient.toLowerCase() !== expectedRecipient.toLowerCase()) {
    throw new Error('Payment details mismatch');
  }

  // 5. Mark processed BEFORE fulfilling
  await markProcessed(txId);
  await fulfillOrder(txId);
}
```

Key threats this prevents:
- **Replay attacks**: Track processed transaction IDs with unique constraints
- **Impersonation**: Verify `sender` matches the authenticated user
- **Amount tampering**: Validate `amount` and `recipient` server-side

## Server-Side User Info Validation

When you provide a `callbackURL` in `payerInfo`, your endpoint receives the user's data **before** the transaction is submitted. You can validate and accept or reject.

```typescript
// POST handler at your callbackURL
app.post('/validate', (req, res) => {
  const { requestData } = req.body;
  const info = requestData.capabilities.dataCallback.requestedInfo;

  // Reject with errors (shown to user)
  if (!isValidEmail(info.email)) {
    return res.json({ errors: { email: 'Invalid email address' } });
  }

  // Accept — return the original request data
  return res.json({ request: requestData });
});
```

## BasePayButton Component

Pre-built React button from `@base-org/account-ui`.

```tsx
import { BasePayButton } from '@base-org/account-ui/react';

<BasePayButton
  colorScheme="light"
  size="medium"
  onClick={handlePayment}
/>
```

| Prop | Type | Values | Default |
|------|------|--------|---------|
| `colorScheme` | `string` | `'light'`, `'dark'`, `'system'` | `'light'` |
| `size` | `string` | `'small'`, `'medium'`, `'large'` | `'medium'` |
| `variant` | `string` | `'solid'`, `'outline'` | `'solid'` |
| `disabled` | `boolean` | — | `false` |
| `onClick` | `() => void` | — | — |
| `onPaymentResult` | `(result) => void` | — | — |

Follow the [Brand Guidelines](https://docs.base.org/base-account/reference/ui-elements/brand-guidelines): always use the combination mark (never plain text "Base Pay"), pad the button with at least 1x height on all sides.

## Framework Integration: Wagmi

`pay()` and `getPaymentStatus()` are standalone functions — they don't require a provider or wagmi config. Call them directly:

```typescript
import { pay, getPaymentStatus } from '@base-org/account';

const { id } = await pay({ amount: '5.00', to: '0x...', testnet: true });
const status = await getPaymentStatus({ id, testnet: true });
```

If you're also using SIWB with wagmi, the `pay()` function still works independently alongside the wagmi provider setup.

## Testing

- Use `testnet: true` in both `pay()` and `getPaymentStatus()`
- Test on Base Sepolia (chain ID 84532)
- Get test USDC from the [Circle Faucet](https://faucet.circle.com/) on Base Sepolia

## Security Checklist

- Always verify payments server-side with `getPaymentStatus()`
- Track processed transaction IDs in a database with unique constraints
- Verify `sender` matches your authenticated user
- Validate `amount` and `recipient` match the expected order
- `testnet` param must match between `pay()` and `getPaymentStatus()`
- Never disable payment buttons based on onchain balance alone — check `auxiliaryFunds` capability (users may have Coinbase balances available via MagicSpend)
