---
name: using-cdp-sdk
description: "Integrates the Coinbase Developer Platform (CDP) SDK for server-side wallet management, transactions, smart accounts, token swaps, and testnet faucet on Base. Use when building backends, bots, or AI agents that need programmatic wallet creation, server-side signing, ERC-4337 smart accounts, token transfers, testnet faucet access, or policy management. Covers phrases like 'CDP SDK setup', 'create server wallet', 'server-side signing on Base', 'smart account on Base', 'CDP faucet', 'token swap on Base', 'send transaction with CDP', 'coinbase developer platform', 'EIP-7702 delegation', or 'gasless transactions on Base'."
---

# Using CDP SDK on Base

The Coinbase Developer Platform (CDP) SDK provides server-side wallet management, transaction signing, smart accounts, token swaps, and faucet access for Base. Use it when building backends, bots, or AI agents that interact with Base programmatically.

## Prerequisites

1. **Node.js 20.19+** (required for ESM support)
2. Install the SDK:

```bash
npm install @coinbase/cdp-sdk dotenv
```

3. Obtain credentials from the [CDP Portal](https://portal.cdp.coinbase.com/projects/api-keys):
   - **API Key ID** and **API Key Secret**
   - **Wallet Secret** (required for signing transactions)

4. Create a `.env` file:

```bash
CDP_API_KEY_ID=your-api-key-id
CDP_API_KEY_SECRET=your-api-key-secret
CDP_WALLET_SECRET=your-wallet-secret
```

## Security

- **Never commit CDP credentials** to version control — use environment variables or `.env` files
- **Never expose credentials client-side** — CDP SDK is server-side only
- **Add `.env` to `.gitignore`** immediately
- **Use policies** to restrict what accounts can do (allowlists, value limits)
- **Rotate API keys** regularly via the CDP Portal
- **Set `DISABLE_CDP_ERROR_REPORTING=true`** if you don't want error telemetry sent to CDP

## Quick Start

Initialize the client — it reads credentials from environment variables automatically:

```typescript
import { CdpClient } from "@coinbase/cdp-sdk";
import dotenv from "dotenv";

dotenv.config();

const cdp = new CdpClient();
```

**Important:** Create the client once and reuse it. It handles connection pooling internally.

## Creating Accounts

### EVM Account (EOA)

```typescript
// Create a new account
const account = await cdp.evm.createAccount();
console.log(`Address: ${account.address}`);

// Get or create by name (idempotent)
const named = await cdp.evm.getOrCreateAccount({ name: "my-bot-wallet" });
```

### Smart Account (ERC-4337)

Smart accounts support batched calls, gas sponsorship via paymasters, and user operations. Supported on Base and Base Sepolia.

```typescript
const owner = await cdp.evm.createAccount();
const smart = await cdp.evm.createSmartAccount({ owner });
console.log(`Smart account: ${smart.address}`);

// Or get/create idempotently
const smartNamed = await cdp.evm.getOrCreateSmartAccount({
  name: "my-agent-smart-wallet",
  owner,
});
```

## Testnet Faucet

Claim testnet ETH or USDC on Base Sepolia. Capped at 0.0001 ETH per claim.

```typescript
const account = await cdp.evm.createAccount();

const faucet = await cdp.evm.requestFaucet({
  address: account.address,
  network: "base-sepolia",
  token: "eth", // or "usdc", "eurc", "cbbtc"
});

console.log(`Funded: https://sepolia.basescan.org/tx/${faucet.transactionHash}`);
```

## Sending Transactions

### EOA Transaction

```typescript
import { parseEther, createPublicClient, http } from "viem";
import { baseSepolia } from "viem/chains";

const publicClient = createPublicClient({
  chain: baseSepolia,
  transport: http(),
});

const { transactionHash } = await cdp.evm.sendTransaction({
  address: account.address,
  network: "base-sepolia",
  transaction: {
    to: "0x4252e0c9A3da5A2700e7d91cb50aEf522D0C6Fe8",
    value: parseEther("0.000001"),
  },
});

await publicClient.waitForTransactionReceipt({ hash: transactionHash });
```

### Smart Account User Operation (Gasless on Base Sepolia)

```typescript
import { parseEther } from "viem";

const userOp = await cdp.evm.sendUserOperation({
  smartAccount: smart,
  network: "base-sepolia",
  calls: [
    {
      to: "0x4252e0c9A3da5A2700e7d91cb50aEf522D0C6Fe8",
      value: parseEther("0.000001"),
      data: "0x",
    },
  ],
});

// Optionally specify a paymaster for mainnet gas sponsorship:
// paymasterUrl: "https://your-paymaster.com"
```

## Token Transfers

The SDK provides a convenience `transfer` method on account objects:

```typescript
import { parseUnits } from "viem";

const sender = await cdp.evm.getOrCreateAccount({ name: "sender" });

// Transfer USDC
const { transactionHash } = await sender.transfer({
  to: "0x9F663335Cd6Ad02a37B633602E98866CF944124d",
  amount: parseUnits("10", 6), // 10 USDC (6 decimals)
  token: "usdc",
  network: "base-sepolia",
});

// Smart accounts use userOpHash instead of transactionHash
const smartSender = await cdp.evm.getOrCreateSmartAccount({
  name: "smart-sender",
  owner: sender,
});

const { userOpHash } = await smartSender.transfer({
  to: "0x9F663335Cd6Ad02a37B633602E98866CF944124d",
  amount: parseUnits("10", 6),
  token: "usdc",
  network: "base-sepolia",
});

const receipt = await smartSender.waitForUserOperation({ hash: userOpHash });
```

## Token Swaps

Swap tokens on Base using the built-in DEX integration:

```typescript
const account = await cdp.evm.getOrCreateAccount({ name: "swap-account" });

// All-in-one swap (recommended)
const { transactionHash } = await account.swap({
  network: "base",
  fromToken: "0x4200000000000000000000000000000000000006", // WETH
  toToken: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",   // USDC
  fromAmount: BigInt("1000000000000000000"), // 1 WETH
  slippageBps: 100, // 1% slippage
});

// Or get a price quote first
const price = await cdp.evm.getSwapPrice({
  network: "base",
  fromToken: "0x4200000000000000000000000000000000000006",
  toToken: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  fromAmount: BigInt("1000000000000000000"),
  taker: account.address,
});

if (price.liquidityAvailable) {
  console.log(`You'll receive: ${price.toAmount} USDC`);
}
```

## EIP-7702 Delegation

Upgrade an EOA with smart account capabilities (batched transactions, gas sponsorship):

```typescript
const account = await cdp.evm.getOrCreateAccount({ name: "my-eoa" });

const { delegationOperationId } = await cdp.evm.createEvmEip7702Delegation({
  address: account.address,
  network: "base-sepolia",
});

const result = await cdp.evm.waitForEvmEip7702DelegationOperationStatus({
  delegationOperationId,
});
console.log(`Delegation status: ${result.status}`);
```

## viem Integration

CDP SDK is fully viem-compatible. Create a viem wallet client backed by a CDP server wallet:

```typescript
import { createWalletClient, http, toAccount } from "viem";
import { baseSepolia } from "viem/chains";

const serverAccount = await cdp.evm.createAccount();

const walletClient = createWalletClient({
  account: toAccount(serverAccount),
  chain: baseSepolia,
  transport: http(),
});

// Now use standard viem methods
const hash = await walletClient.sendTransaction({
  to: "0x4252e0c9A3da5A2700e7d91cb50aEf522D0C6Fe8",
  value: parseEther("0.000001"),
});
```

## Policy Management

Restrict what accounts can do using policies:

```typescript
// Create a policy that only allows transactions <= 1 ETH to a specific address
const policy = await cdp.policies.createPolicy({
  policy: {
    scope: "project", // applies to all accounts
    description: "Allowlist with value limit",
    rules: [
      {
        action: "accept",
        operation: "signEvmTransaction",
        criteria: [
          {
            type: "ethValue",
            ethValue: "1000000000000000000", // 1 ETH max
            operator: "<=",
          },
          {
            type: "evmAddress",
            addresses: ["0x000000000000000000000000000000000000dEaD"],
            operator: "in",
          },
        ],
      },
    ],
  },
});

// Attach policy to an account at creation time
const restricted = await cdp.evm.createAccount({
  name: "restricted-account",
  accountPolicy: policy.id,
});
```

## Common Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `AggregateError [ETIMEDOUT]` | Node.js DNS resolution bug | Set `NODE_OPTIONS="--network-family-autoselection-attempt-timeout=500"` |
| `ERR_REQUIRE_ESM` | Node version too old | Upgrade to Node.js 20.19+ |
| `moduleResolution` TypeScript errors | Legacy tsconfig | Set `"moduleResolution": "node16"` in `tsconfig.json` |
| `Failed to initialize CDP client` | Missing credentials | Verify `CDP_API_KEY_ID`, `CDP_API_KEY_SECRET`, `CDP_WALLET_SECRET` in `.env` |
| Smart account operations fail | Wrong network | Smart accounts only work on Base and Base Sepolia |

## Key Links

- [CDP Portal](https://portal.cdp.coinbase.com) — API keys and wallet secrets
- [CDP SDK npm](https://www.npmjs.com/package/@coinbase/cdp-sdk) — Package and API docs
- [CDP SDK GitHub](https://github.com/coinbase/cdp-sdk) — Source code and examples
- [CDP API Reference](https://docs.cdp.coinbase.com/api-v2/docs/welcome) — REST API docs
