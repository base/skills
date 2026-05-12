# Privy Integration

Privy provides a `dataSuffix` plugin that automatically appends your Builder Code to **all** transactions, including EOA and ERC-4337 smart wallet user operations.

## Requirements

- `@privy-io/react-auth` >= v3.13.0
- `ox` library installed

## Setup

Import the `dataSuffix` plugin and configure it in your `PrivyProvider`:

```tsx
import { PrivyProvider, dataSuffix } from "@privy-io/react-auth";
import { Attribution } from "ox/erc8021";

const ERC_8021_ATTRIBUTION_SUFFIX = Attribution.toDataSuffix({
  codes: ["YOUR-BUILDER-CODE"],
});

function App() {
  return (
    <PrivyProvider
      appId="your-privy-app-id"
      config={{
        // ...your existing config
        plugins: [dataSuffix(ERC_8021_ATTRIBUTION_SUFFIX)],
      }}
    >
      {/* your app */}
    </PrivyProvider>
  );
}
```

Once configured, **no changes** to individual transaction calls are needed.

## How It Appends

| Transaction Type | Where Suffix Goes |
|---|---|
| EOA transactions | `transaction.data` field |
| Smart wallets (ERC-4337) | `userOp.callData` field |

## Limitations

- Appends suffix on **all chains**, not just Base. Contact Privy for chain-specific behavior.
- NOT yet supported with the `@privy-io/wagmi` adapter. Use the native Privy provider instead.
- If your project uses `@privy-io/wagmi`, you must either switch to the native Privy transaction flow or use the Wagmi client-level approach from [wagmi.md](wagmi.md).

## Upgrading Privy

If the project is on an older version:

```bash
npm install @privy-io/react-auth@latest
```

Verify version >= 3.13.0 before using the `dataSuffix` plugin.
