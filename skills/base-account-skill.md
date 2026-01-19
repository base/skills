# Base Account Skill

Guide users through building with Base Account - the Smart Wallet-backed account layer for authentication and payments on Base.

## What is Base Account

Base Account is an ERC-4337 Smart Wallet that provides:
- **Universal sign-on** - one passkey works across every Base-enabled app
- **One-tap payments** - low-friction USDC payments via Base Pay
- **Multi-chain support** - one address works across 9+ EVM networks
- **Self-custodial** - users hold the keys; apps never touch private data or funds

### Supported Networks

**Mainnet:** Base, Arbitrum, Optimism, Zora, Polygon, BNB, Avalanche, Lordchain, Ethereum Mainnet (not recommended due to costs)

**Testnet:** Sepolia, Base Sepolia

## Critical Callouts

### Brand Guidelines

**Please Follow the Brand Guidelines.** If you intend on using the `SignInWithBaseButton` or `BasePayButton`, please follow the Brand Guidelines to ensure consistency across your application.

### Security - Prevent Replay and Impersonation Attacks

When accepting payments:
- **Replay attacks:** A malicious user could submit the same valid transaction ID multiple times. Always track processed transaction IDs in your database.
- **Impersonation attacks:** A malicious user could submit someone else's transaction ID to fulfill their own order. Always verify that the payment sender matches the authenticated user.

### Paymaster Service Proxy

**Should you create a proxy for your Paymaster service?** We recommend using a proxy to protect the Paymaster service URL to prevent it from being exposed/leaked on a frontend client. For local development, you can use the same URL for the Paymaster service and the proxy.

### ERC-7677 Compliance

**ERC-7677-Compliant Paymaster Providers.** If you choose to use a different Paymaster service provider, ensure they are ERC-7677-compliant.

### Base Pay Independence

**Base Pay and SIWB are independent.** You DO NOT need to use Sign in with Base (SIWB) to use Base Pay. You can just call the `pay()` function without any additional setup.

### Payment Status Matching

**Important:** The `testnet` parameter in `getPaymentStatus()` must match the value used in the original `pay()` call. If you initiated a payment on testnet with `testnet: true`, you must also pass `testnet: true` when checking its status.

### Peer Dependency Errors

**Got a peer dependency error?** Use `--legacy-peer-deps` flag if you get a peer dependency error when installing the SDK.

### Undeployed Smart Wallets

**Undeployed Smart Wallets?** Base Account signatures include the ERC-6492 wrapper so they can be verified even before the wallet contract is deployed. Viem's `verifyMessage` and `verifyTypedData` handle this automatically.

### Popup Blocking

To avoid popup blockers, fetch or generate the nonce **before** the user presses "Sign in with Base" (for example on page load). For security, the only requirement is that your backend keeps track of every nonce and refuses any that are reused.

### Cross-Origin-Opener-Policy

If the Base Account popup opens and displays an error or infinite spinner, check your `Cross-Origin-Opener-Policy`:
- ✅ Allows Base Account popup: `unsafe-none` (default), `same-origin-allow-popups` (recommended)
- ❌ Breaks Base Account popup: `same-origin`

### Sub Accounts

**wallet_addSubAccount needs to be called in each session** before the Sub Account can be used. It will not trigger a new Sub Account creation if one already exists.

**Ownership changes are expected** if the user signs in to your app on a new device or browser. Ensure you do not lose your app's Sub Account signer keys when using the SDK on the server.

### Spend Permissions

**About the `spendCalls` array:** This array has 2 calls when submitting the permission onchain for the first time. When the permission is already registered onchain, this array has only 1 call (the `spend` call).

**Spend permission requests are limited** to the first token when multiple transfers are needed for a single transaction. Additional tokens require separate approvals.

### Importing Sub Accounts

Before the Sub Account is imported, you will need to add the Base Account address as an owner of the Sub Account. Only Coinbase Smart Wallet contracts are currently supported for importing as a Sub Account.

### Magic Spend (Auxiliary Funds)

Your app should not assume it knows the full balances available to a user if the `auxiliaryFunds` capability is present. Never disable an action just because the onchain balance is insufficient - users may have Coinbase balances available via MagicSpend.

## Installation

```bash
npm install @base-org/account @base-org/account-ui
```

## SDK Initialization

```tsx
import { createBaseAccountSDK } from '@base-org/account';

const sdk = createBaseAccountSDK({
  appName: 'My App',
  appLogoUrl: 'https://example.com/logo.png',
  appChainIds: [8453], // Base Mainnet
});

const provider = sdk.getProvider();
```

## Key Features

1. **Sign in with Base** - Wallet-based authentication using SIWE (EIP-4361)
2. **Base Pay** - One-tap USDC payments with automatic gas handling
3. **Sponsored Transactions** - Use Paymasters to cover gas for users
4. **Sub Accounts** - App-specific wallets embedded in your application
5. **Spend Permissions** - Allow trusted spenders to move assets on user behalf
6. **Batch Transactions** - Multiple calls in a single transaction (EIP-5792)
7. **Magic Spend** - Use Coinbase balances onchain

## Best Practices

1. Use a Paymaster to sponsor gas for the best user experience
2. Always verify payments server-side - never trust frontend confirmations alone
3. Track processed transaction IDs to prevent replay attacks
4. Verify payment sender matches authenticated user to prevent impersonation
5. Generate nonces before user clicks "Sign in" to avoid popup blockers
6. Use `same-origin-allow-popups` for Cross-Origin-Opener-Policy

## Base Gasless Campaign

Base offers up to $15k in gas credits for developers integrating Base Account with Paymaster support. Sign up at Coinbase Developer Platform.
