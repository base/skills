# Sub Accounts

## Table of Contents

- [Overview](#overview)
- [Key Concepts](#key-concepts)
- [SDK Configuration](#sdk-configuration)
- [Key Management](#key-management)
- [Creating Sub Accounts](#creating-sub-accounts)
- [Retrieving Sub Accounts](#retrieving-sub-accounts)
- [Adding Owners](#adding-owners)
- [wallet_addSubAccount RPC](#wallet_addsubaccount-rpc)
- [wallet_getSubAccounts RPC](#wallet_getsubaccounts-rpc)
- [Funding Sub Accounts](#funding-sub-accounts)
- [Session Management](#session-management)

## Overview

Sub accounts are app-specific embedded wallets created under a user's Base Account. They let your app perform transactions on behalf of the user without requiring approval popups for every action — useful for gaming, DeFi automation, or any UX that needs low-friction transactions.

Each sub account is a separate smart wallet owned by the parent Base Account.

## Key Concepts

- Sub accounts are **app-scoped** — each app gets its own sub account(s)
- The parent Base Account is the **owner** of each sub account
- Sub accounts can be funded via **spend permissions** or **manual transfers**
- Ownership may change across devices/browsers — always call `wallet_addSubAccount` each session
- Only **Coinbase Smart Wallet** contracts are supported for importing existing sub accounts

## SDK Configuration

Configure sub accounts when creating the SDK:

```typescript
import { createBaseAccountSDK, getCryptoKeyAccount } from '@base-org/account';

const sdk = createBaseAccountSDK({
  appName: 'My App',
  appLogoUrl: 'https://example.com/logo.png',
  appChainIds: [8453],
  subAccounts: {
    creation: 'on-connect',
    defaultAccount: 'sub',
    funding: 'spend-permissions',
    toOwnerAccount: async () => {
      const { account } = await getCryptoKeyAccount();
      return { account };
    },
  },
});
```

`SubAccountOptions`:

| Property | Type | Values | Description |
|----------|------|--------|-------------|
| `creation` | `string` | `'on-connect'`, `'manual'` | When to create sub accounts |
| `defaultAccount` | `string` | `'sub'`, `'universal'` | Which account is default (first in accounts array) |
| `funding` | `string` | `'spend-permissions'`, `'manual'` | How sub accounts are funded |
| `toOwnerAccount` | `function` | — | Returns `{ account: LocalAccount \| WebAuthnAccount \| null }` |

## Key Management

Sub accounts require a key pair for signing. The SDK provides utilities for P256 key management.

### `generateKeyPair()`

```typescript
import { generateKeyPair } from '@base-org/account';

const keyPair = await generateKeyPair();
// keyPair.publicKey → hex string
// keyPair.privateKey → hex string
```

### `getKeypair()`

Retrieves an existing key pair from secure storage (returns `null` if none).

```typescript
import { getKeypair } from '@base-org/account';

let keyPair = await getKeypair();
if (!keyPair) {
  keyPair = await generateKeyPair();
}
```

### `getCryptoKeyAccount()`

Gets the current crypto key account info.

```typescript
import { getCryptoKeyAccount } from '@base-org/account';

const { account } = await getCryptoKeyAccount();
// account.publicKey → hex string
// account.type → 'webauthn' | 'local'
// account.address → (for LocalAccount only)
```

Returns `{ account }` where `account` is one of:
- `WebAuthnAccount`: `{ publicKey, type: 'webauthn' }`
- `LocalAccount`: `{ address, publicKey, type: 'local' }`
- `null`: No account available

## Creating Sub Accounts

### Via SDK Helper

```typescript
const subAccount = await sdk.subAccount.create({
  type: 'webauthn-p256',
  publicKey: keyPair.publicKey,
});
// subAccount.address → the sub account address
```

### Via RPC (wallet_addSubAccount)

```typescript
const result = await provider.request({
  method: 'wallet_addSubAccount',
  params: [{
    account: {
      type: 'create',
      keys: [{
        type: 'webauthn-p256',
        publicKey: keyPair.publicKey,
      }],
    },
  }],
});
// result.address → the sub account address
```

Key types for the `keys` array:

| Type | Description |
|------|-------------|
| `'address'` | Raw Ethereum address |
| `'p256'` | P256 public key |
| `'webcrypto-p256'` | WebCrypto P256 key |
| `'webauthn-p256'` | WebAuthn P256 key (recommended) |

## Retrieving Sub Accounts

```typescript
const subAccount = await sdk.subAccount.get();
// Returns the current sub account or null
```

Or via RPC:

```typescript
const subAccounts = await provider.request({
  method: 'wallet_getSubAccounts',
});
// Array of { address, factory?, factoryData? }
```

## Adding Owners

```typescript
await sdk.subAccount.addOwner({
  address: newOwnerAddress,
  chainId: 8453,
});
```

## wallet_addSubAccount RPC

Two modes of operation:

### Create a New Sub Account

```typescript
await provider.request({
  method: 'wallet_addSubAccount',
  params: [{
    account: {
      type: 'create',
      keys: [{ type: 'webauthn-p256', publicKey: '0x...' }],
    },
  }],
});
```

### Import an Existing Deployed Account

```typescript
await provider.request({
  method: 'wallet_addSubAccount',
  params: [{
    account: {
      type: 'deployed',
      address: '0xExistingSubAccount',
      chainId: 8453,
    },
  }],
});
```

Returns: `{ address, factory?, factoryData? }`

## wallet_getSubAccounts RPC

```typescript
const accounts = await provider.request({
  method: 'wallet_getSubAccounts',
});
```

Returns an array of sub account objects.

## Funding Sub Accounts

Two strategies:

### Spend Permissions (Recommended)

Set `funding: 'spend-permissions'` in SDK config. The parent Base Account grants a spend permission to the sub account, which can then spend tokens within the allowed limit.

### Manual

Set `funding: 'manual'`. You transfer tokens directly to the sub account address.

## Session Management

**Call `wallet_addSubAccount` at the start of each session** before using the sub account. This is necessary because:

- Ownership may change when users switch devices or browsers
- The sub account needs to be re-registered with the current session
- Without this call, sub account operations may fail silently

```typescript
async function initSession() {
  const keyPair = await getKeypair() || await generateKeyPair();
  await provider.request({
    method: 'wallet_addSubAccount',
    params: [{
      account: {
        type: 'create',
        keys: [{ type: 'webauthn-p256', publicKey: keyPair.publicKey }],
      },
    }],
  });
}
```
