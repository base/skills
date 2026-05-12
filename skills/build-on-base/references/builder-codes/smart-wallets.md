# Smart Wallets (EIP-5792 / ERC-4337)

For smart wallet transactions using `sendCalls` (EIP-5792), pass the `dataSuffix` via the `capabilities` object.

## Wagmi useSendCalls

```tsx
import { useSendCalls } from "wagmi";
import { parseEther } from "viem";
import { Attribution } from "ox/erc8021";

const DATA_SUFFIX = Attribution.toDataSuffix({
  codes: ["YOUR-BUILDER-CODE"],
});

function App() {
  const { sendCalls } = useSendCalls();

  return (
    <button onClick={() => sendCalls({
      calls: [
        {
          to: "0x...",
          value: parseEther("1"),
        },
        {
          data: "0xdeadbeef",
          to: "0x...",
        },
      ],
      capabilities: {
        dataSuffix: {
          value: DATA_SUFFIX,
          optional: true, // wallet proceeds even if it doesn't support dataSuffix
        },
      },
    })}>
      Send calls
    </button>
  );
}
```

## Where the Suffix Goes

| Wallet Type | Appended To |
|---|---|
| EOA (`sendTransaction`) | `transaction.data` |
| Smart Wallet (`sendCalls`) | `userOp.callData` (not individual call data) |

**Important**: For ERC-4337 user operations, the suffix is appended to the outer `callData` field of the UserOperation, not to individual call data within batched calls.

## Wallet Support

The connected wallet must support the `dataSuffix` capability via ERC-5792 `wallet_sendCalls`. Setting `optional: true` means the transaction proceeds even if the wallet doesn't support it.

Currently supported by: Base Smart Wallet, Coinbase Wallet, and other ERC-5792 compliant wallets.

## Client-Level Alternative

If using Wagmi with `dataSuffix` in the config (see [wagmi.md](wagmi.md)), `useSendCalls` transactions are also attributed automatically without needing to pass `capabilities`.

## Privy Smart Wallets

If using Privy's embedded smart wallets, the `dataSuffix` plugin handles everything automatically. See [privy.md](privy.md). No need to manually pass capabilities.
