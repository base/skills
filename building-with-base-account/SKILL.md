---
name: building-with-base-account
description: Integrates Base Account SDK for authentication and payments. Covers Sign in with Base (SIWB), Base Pay, Paymasters, Sub Accounts, and Spend Permissions. Use when building apps with wallet authentication, USDC payments, sponsored transactions, or smart wallet features on Base.
---

# Building with Base Account

Base Account is an ERC-4337 Smart Wallet providing universal sign-on, one-tap USDC payments, and multi-chain support (Base, Arbitrum, Optimism, Zora, Polygon, BNB, Avalanche, Lordchain, Ethereum Mainnet).

## Quick Start

```bash
npm install @base-org/account @base-org/account-ui
```

```tsx
import { createBaseAccountSDK } from '@base-org/account';

const sdk = createBaseAccountSDK({
  appName: 'My App',
  appLogoUrl: 'https://example.com/logo.png',
  appChainIds: [8453], // Base Mainnet
});

const provider = sdk.getProvider();
```

## Core Features

| Feature | Description |
|---------|-------------|
| Sign in with Base | Wallet auth using SIWE (EIP-4361) |
| Base Pay | One-tap USDC payments, gas handled automatically |
| Paymasters | Sponsor gas for users (ERC-7677) |
| Sub Accounts | App-specific embedded wallets |
| Spend Permissions | Delegate asset spending to trusted spenders |
| Batch Transactions | Multiple calls in one transaction (EIP-5792) |
| Magic Spend | Access Coinbase balances onchain |

## Critical Requirements

### Security

- **Track transaction IDs** to prevent replay attacks
- **Verify sender matches authenticated user** to prevent impersonation
- **Use a proxy** to protect Paymaster URLs from frontend exposure
- **Paymaster providers must be ERC-7677-compliant**

### Popup Handling

- Generate nonces **before** user clicks "Sign in" to avoid popup blockers
- Use `Cross-Origin-Opener-Policy: same-origin-allow-popups`
- `same-origin` breaks the Base Account popup

### Base Pay

- Base Pay works independently from SIWB - no auth required for `pay()`
- `testnet` param in `getPaymentStatus()` must match `pay()` call
- Never disable actions based on onchain balance alone - check `auxiliaryFunds` capability

### Sub Accounts

- Call `wallet_addSubAccount` each session before use
- Ownership changes expected on new devices/browsers
- Only Coinbase Smart Wallet contracts supported for import

### Spend Permissions

- `spendCalls` array has 2 calls first time, 1 call after registration
- Limited to first token when multiple transfers needed

### Smart Wallets

- ERC-6492 wrapper enables signature verification before wallet deployment
- Viem's `verifyMessage`/`verifyTypedData` handle this automatically

## Brand Guidelines

Follow brand guidelines when using `SignInWithBaseButton` or `BasePayButton`.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Peer dependency error | Use `--legacy-peer-deps` flag |
| Popup infinite spinner | Check `Cross-Origin-Opener-Policy` header |
| Signature fails pre-deploy | Viem handles ERC-6492 automatically |
