# Authentication (Sign in with Base)

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [SDK Setup](#sdk-setup)
- [Sign-In Flow](#sign-in-flow)
- [Backend Verification](#backend-verification)
- [SignInWithBaseButton Component](#signinwithbasebutton-component)
- [Framework Integration: Wagmi](#framework-integration-wagmi)
- [Framework Integration: Privy](#framework-integration-privy)
- [Smart Wallet Signatures (ERC-6492)](#smart-wallet-signatures-erc-6492)
- [Security Checklist](#security-checklist)

## Overview

Sign in with Base (SIWB) provides passwordless authentication using wallet signatures. It builds on Sign-In with Ethereum (SIWE, EIP-4361) — the user signs a message with their wallet key, and the backend verifies it. No passwords, no seed phrases.

Base Accounts are ERC-4337 smart wallets. Unlike traditional wallets (EOAs), the user's key is a passkey — the wallet contract verifies signatures via `isValidSignature` (EIP-1271). Viem handles this automatically.

## How It Works

1. Generate a nonce **before** the user clicks sign-in (avoids popup blockers)
2. Call `wallet_connect` with the `signInWithEthereum` capability
3. User approves in the Base Account popup (`keys.coinbase.com`)
4. SDK returns `{ address, message, signature }`
5. Send `message` + `signature` to your backend
6. Backend verifies with viem and creates a session/JWT

## SDK Setup

```bash
npm install @base-org/account @base-org/account-ui
```

```typescript
import { createBaseAccountSDK } from '@base-org/account';

const sdk = createBaseAccountSDK({
  appName: 'My App',
  appLogoUrl: 'https://example.com/logo.png',
  appChainIds: [8453],
});

const provider = sdk.getProvider();
```

`createBaseAccountSDK` parameters:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `appName` | `string` | No | App name shown in wallet UI (default: `"App"`) |
| `appLogoUrl` | `string` | No | Logo URL for wallet UI |
| `appChainIds` | `number[]` | No | Supported chain IDs |
| `paymasterUrls` | `Record<number, string>` | No | Chain ID to paymaster URL mapping |

## Sign-In Flow

```typescript
const nonce = crypto.randomUUID().replace(/-/g, '');

const { accounts } = await provider.request({
  method: 'wallet_connect',
  params: [{
    version: '1',
    capabilities: {
      signInWithEthereum: {
        nonce,
        chainId: '0x2105', // Base Mainnet (8453)
      },
    },
  }],
});

const { address } = accounts[0];
const { message, signature } = accounts[0].capabilities.signInWithEthereum;
```

`signInWithEthereum` capability parameters:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `nonce` | `string` | Yes | Unique random string per auth attempt |
| `chainId` | `string` | Yes | Hex chain ID (`"0x2105"` = Base Mainnet 8453) |

Response shape:

| Field | Type | Description |
|-------|------|-------------|
| `accounts[0].address` | `string` | User's wallet address |
| `accounts[0].capabilities.signInWithEthereum.message` | `string` | SIWE-formatted message |
| `accounts[0].capabilities.signInWithEthereum.signature` | `string` | Cryptographic signature |

### Fallback for Non-Base Wallets

Not every wallet supports `wallet_connect`. Fall back to `eth_requestAccounts` + `personal_sign`:

```typescript
try {
  const { accounts } = await provider.request({
    method: 'wallet_connect',
    params: [{ version: '1', capabilities: { signInWithEthereum: { nonce, chainId: '0x2105' } } }],
  });
  // use accounts[0].capabilities.signInWithEthereum
} catch (err) {
  if (err.code === 4100) {
    const [address] = await provider.request({ method: 'eth_requestAccounts' });
    const signature = await provider.request({
      method: 'personal_sign',
      params: [siweMessage, address],
    });
  }
}
```

## Backend Verification

Use viem to verify the signature. It handles both EOA and smart wallet (EIP-1271/ERC-6492) signatures automatically.

```typescript
import { createPublicClient, http } from 'viem';
import { base } from 'viem/chains';

const client = createPublicClient({ chain: base, transport: http() });

const valid = await client.verifyMessage({
  address,
  message,
  signature,
});
```

### Full Express Server Example

```typescript
import express from 'express';
import { createPublicClient, http } from 'viem';
import { base } from 'viem/chains';

const app = express();
const client = createPublicClient({ chain: base, transport: http() });
const usedNonces = new Set<string>();

app.get('/auth/nonce', (req, res) => {
  const nonce = crypto.randomUUID().replace(/-/g, '');
  res.json({ nonce });
});

app.post('/auth/verify', async (req, res) => {
  const { address, message, signature } = req.body;
  const nonceMatch = message.match(/Nonce: (\w+)/);
  if (!nonceMatch || usedNonces.has(nonceMatch[1])) {
    return res.status(401).json({ error: 'Invalid or reused nonce' });
  }

  const valid = await client.verifyMessage({ address, message, signature });
  if (!valid) return res.status(401).json({ error: 'Invalid signature' });

  usedNonces.add(nonceMatch[1]);
  // Create session/JWT here
  res.json({ success: true, address });
});
```

## SignInWithBaseButton Component

Pre-built React button from `@base-org/account-ui`.

```tsx
import { SignInWithBaseButton } from '@base-org/account-ui/react';

<SignInWithBaseButton
  colorScheme="light"
  size="medium"
  variant="solid"
  onClick={handleSignIn}
/>
```

| Prop | Type | Values | Default |
|------|------|--------|---------|
| `align` | `string` | `'left'`, `'center'`, `'right'` | `'center'` |
| `variant` | `string` | `'solid'`, `'transparent'` | `'solid'` |
| `colorScheme` | `string` | `'light'`, `'dark'`, `'system'` | `'light'` |
| `size` | `string` | `'small'`, `'medium'`, `'large'` | `'medium'` |
| `disabled` | `boolean` | — | `false` |
| `onClick` | `() => void` | — | — |
| `onSignInResult` | `(result) => void` | — | — |

Follow the [Brand Guidelines](https://docs.base.org/base-account/reference/ui-elements/brand-guidelines): use Base blue (`#0000FF`) on light backgrounds, all-white lockup on dark backgrounds. Do not modify the Base Square color or corner radius.

## Framework Integration: Wagmi

```typescript
import { createConfig, http } from 'wagmi';
import { base } from 'wagmi/chains';
import { createBaseAccountSDK } from '@base-org/account';
import { custom } from 'viem';

const sdk = createBaseAccountSDK({
  appName: 'My App',
  appLogoUrl: 'https://example.com/logo.png',
  appChainIds: [8453],
});

const config = createConfig({
  chains: [base],
  transports: {
    [base.id]: custom(sdk.getProvider()),
  },
});
```

Then use wagmi hooks (`useConnect`, `useAccount`, `useSignMessage`) as usual.

## Framework Integration: Privy

Privy has day-1 Base Account support. Configure it as a wallet connector — see [Privy docs](https://docs.privy.io/) for the latest integration guide. Base Account appears as a wallet option in the Privy modal.

## Smart Wallet Signatures (ERC-6492)

Base Accounts may not be deployed onchain until the user's first transaction. Signatures from undeployed wallets include an ERC-6492 wrapper that lets verifiers deploy the contract in a simulation to validate the signature.

**You don't need to do anything special** — viem's `verifyMessage` and `verifyTypedData` handle ERC-6492 automatically. Just make sure you're using viem for verification.

## Security Checklist

- Generate nonces **before** the user clicks sign-in (avoids popup blockers)
- Track used nonces server-side — reject any reused nonce
- Verify signatures on your backend, never trust the frontend alone
- Use `Cross-Origin-Opener-Policy: same-origin-allow-popups` (NOT `same-origin`, which breaks the popup)
- Set appropriate session/JWT expiry times
- Include `chainId` in verification to prevent cross-chain replay
