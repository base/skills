# Troubleshooting

## Table of Contents

- [Quick Fixes](#quick-fixes)
- [Popup Issues](#popup-issues)
- [Gas Usage](#gas-usage)
- [Unsupported Operations](#unsupported-operations)
- [Wallet Library Compatibility](#wallet-library-compatibility)
- [Migration from Coinbase Wallet SDK](#migration-from-coinbase-wallet-sdk)
- [Transaction Simulation Debugging](#transaction-simulation-debugging)
- [When to Consult the Docs](#when-to-consult-the-docs)

## Quick Fixes

| Issue | Solution |
|-------|----------|
| Peer dependency error during install | Use `--legacy-peer-deps` flag |
| Popup shows infinite spinner | Set COOP header to `same-origin-allow-popups` (not `same-origin`) |
| Signature verification fails pre-deploy | Use viem — it handles ERC-6492 automatically |
| `wallet_connect` throws `4100` | Wallet doesn't support it; fall back to `eth_requestAccounts` + `personal_sign` |
| Payment status returns `not_found` | Ensure `testnet` param in `getPaymentStatus()` matches `pay()` |
| Sub account operations fail | Call `wallet_addSubAccount` at the start of each session |
| Balance appears insufficient | Check `auxiliaryFunds` capability — user may have Coinbase balances available |

## Popup Issues

Base Account uses a popup window at `keys.coinbase.com` for user approvals.

### Cross-Origin-Opener-Policy (COOP)

| COOP Value | Works? |
|------------|--------|
| `unsafe-none` (browser default) | Yes |
| `same-origin-allow-popups` | Yes (recommended) |
| `same-origin` | **No** — breaks the popup entirely |

If using `same-origin`, the popup either errors or shows an infinite spinner. Switch to `same-origin-allow-popups`.

### Popup Blockers

Browsers block popups unless triggered by a direct user click. To avoid blocking:

- Generate nonces and do any async work **before** the user clicks the sign-in button
- Keep zero or minimal logic between the button click handler and the SDK call
- Test across all target browsers — popup blocking behavior varies

### Popup "Linger" Behavior

After responding to a request, the popup stays open for **200ms** before closing. If a second SDK request arrives within that window, it's handled in the same popup (no new popup needed).

If the second request arrives **after** 200ms (popup already closed), the browser will block the new programmatic popup. Design flows to either:
- Chain requests quickly (< 200ms gap)
- Require a new user click for the second request

## Gas Usage

Base Accounts use more gas than traditional Ethereum accounts (EOAs) because they're smart contracts processed through ERC-4337 bundling.

| Operation | EOA | Base Account |
|-----------|-----|-------------|
| Native token transfer | ~21,000 gas | ~100,000 gas |
| ERC-20 token transfer | ~65,000 gas | ~150,000 gas |
| First-time deployment | N/A | ~300,000+ gas (one-time) |

On L2 networks like Base, the cost difference is typically just a few cents. Use a paymaster to sponsor gas entirely (see [capabilities reference](capabilities.md#capability-paymasterservice)).

## Unsupported Operations

Base Account is an ERC-4337 smart wallet. Some operations behave differently:

### Self-Calls

Apps **cannot** make calls to the user's own Base Account address. This is a security measure to prevent changing owners, upgrading the account, or other admin operations.

### CREATE Opcode

Not supported due to ERC-4337 limitations. Workarounds:
- Use a **factory contract** that deploys on behalf of the user
- Use the `CREATE2` opcode instead

### Solidity `transfer` Function

Base Account wallets **cannot receive ETH** via Solidity's built-in `transfer` function because it only forwards 2,300 gas — insufficient for smart contract `receive`/`fallback` functions.

Use `call` instead:

```solidity
// Won't work with Base Account
payable(baseAccountAddress).transfer(amount);

// Use this instead
(bool success, ) = payable(baseAccountAddress).call{value: amount}("");
require(success, "Transfer failed");
```

Known affected contract: **WETH9 on Base** (`0x4200000000000000000000000000000000000006`) — Base Accounts cannot directly unwrap ETH from it.

## Wallet Library Compatibility

These wallet aggregation libraries have day-1 Base Account support:

| Library | Supported |
|---------|-----------|
| Dynamic | Yes |
| Privy | Yes |
| ThirdWeb | Yes |
| ConnectKit | Yes |
| Web3Modal / Reown | Yes |
| Web3-Onboard | Yes |
| RainbowKit | Yes |

## Migration from Coinbase Wallet SDK

The Coinbase Wallet app is transitioning to the Base app. To migrate:

1. **Don't immediately replace** the existing "Coinbase Wallet" button
2. **Add** a "Sign in with Base" button as a new option alongside it
3. Over time, existing Coinbase Wallet users will be migrated to Base Accounts

Code change:

```typescript
// New: add Base Account SDK
import { createBaseAccountSDK } from '@base-org/account';
const baseAccount = createBaseAccountSDK({ appName: 'My App' });
```

As of Coinbase Wallet SDK v4.0, users without the extension see a popup with options (mobile WalletLink or passkey-powered Smart Wallet). To avoid any popup window, use Coinbase Wallet SDK version < 4.0.

## Transaction Simulation Debugging

Hidden feature in the Base Account popup: click the transaction simulation area **five times** to copy the simulation request/response data to your clipboard. Paste into a text editor to inspect.

## When to Consult the Docs

This skill covers the most common patterns. For edge cases, advanced configurations, or the latest API changes, consult:

- **AI-optimized docs**: [docs.base.org/llms.txt](https://docs.base.org/llms.txt) — feed this to your agent for comprehensive context
- **Base Account reference**: [docs.base.org/base-account](https://docs.base.org/base-account) — full API reference, all RPC methods, all capabilities
- **Base Account SDK source**: [github.com/base/account-sdk](https://github.com/base/account-sdk)
- **Smart Wallet contracts**: [github.com/coinbase/smart-wallet](https://github.com/coinbase/smart-wallet)
- **Spend Permissions contracts**: [github.com/coinbase/spend-permissions](https://github.com/coinbase/spend-permissions)
- **Coinbase Developer Platform**: [portal.cdp.coinbase.com](https://portal.cdp.coinbase.com) — paymaster setup, API keys, wallet management

For standard Ethereum RPC methods (`eth_getBalance`, `eth_sendTransaction`, `eth_getTransactionReceipt`, etc.), Base Account's provider supports all standard methods. See the [provider RPC methods reference](https://docs.base.org/base-account/reference/core/provider-rpc-methods/sdk-overview) for the full list.
