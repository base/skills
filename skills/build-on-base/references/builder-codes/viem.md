# Viem Integration

Configure `dataSuffix` on your wallet client to automatically append your Builder Code to all transactions.

## Requirements

- `viem >= 2.45.0`
- `ox` library installed

## Client-Level Setup

```typescript
// client.ts
import { createWalletClient, http } from "viem";
import { base } from "viem/chains";
import { Attribution } from "ox/erc8021";

const DATA_SUFFIX = Attribution.toDataSuffix({
  codes: ["YOUR-BUILDER-CODE"],
});

export const walletClient = createWalletClient({
  chain: base,
  transport: http(),
  dataSuffix: DATA_SUFFIX,
});
```

All transactions through this client are automatically attributed:

```typescript
import { parseEther } from "viem";
import { walletClient } from "./client";

const hash = await walletClient.sendTransaction({
  to: "0x...",
  value: parseEther("0.01"),
});
```

## Per-Transaction Override

```typescript
const hash = await walletClient.sendTransaction({
  to: "0x...",
  value: parseEther("0.01"),
  dataSuffix: DATA_SUFFIX,
});
```

## Server-Side / Agent Usage

For backend agents or bots using viem directly with a private key:

```typescript
import { createWalletClient, http } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { base } from "viem/chains";
import { Attribution } from "ox/erc8021";

const DATA_SUFFIX = Attribution.toDataSuffix({
  codes: ["YOUR-BUILDER-CODE"],
});

const account = privateKeyToAccount("0x...");

const walletClient = createWalletClient({
  account,
  chain: base,
  transport: http(),
  dataSuffix: DATA_SUFFIX,
});
```

This is the typical pattern for AI agent wallets that transact on behalf of users.
