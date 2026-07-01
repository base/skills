# Route Reference

## Supported Routes

| Source | Destination | `transfer` | `call` | Auto-relay |
|--------|-------------|------------|--------|-----------|
| Solana Mainnet | Base Mainnet | yes | yes | yes |
| Solana Devnet | Base Sepolia | yes | yes | yes |
| Base Mainnet | Solana Mainnet | yes | yes | **no** — manual `prove` + `execute` |
| Base Sepolia | Solana Devnet | yes | yes | **no** — manual `prove` + `execute` |
| EVM → EVM | — | not a target | — | — |

## Transfer

### Native asset (`kind: "native"`)

```typescript
client.transfer({
  route: { sourceChain, destinationChain },
  asset: { kind: "native" },
  amount: bigint,        // in source chain's smallest unit (wei / lamports)
  recipient: string,    // address on destination chain
  relay?: { mode: "auto" | "manual" },
});
```

### Token asset (`kind: "token"`)

```typescript
client.transfer({
  route: { sourceChain, destinationChain },
  asset: {
    kind: "token",
    address: "0x...",  // ERC20 address on source (EVM side)
  },
  amount: bigint,
  recipient: string,
  relay?: { mode: "auto" | "manual" },
});
```

### ERC20 → Solana mint mapping

Required when bridging ERC20s to Solana. Add to `bridgeConfig.tokenMappings` in `createBridgeClient()`:

```typescript
bridgeConfig: {
  tokenMappings: {
    [`${base.id}->${solanaMainnet.id}`]: {
      "0xERC20Address": "SolanaMintBase58",
    },
  },
}
```

## Call

### EVM call (`kind: "evm"`)

```typescript
client.call({
  route: { sourceChain: solanaMainnet.id, destinationChain: base.id },
  call: {
    kind: "evm",
    call: { to: "0x...", value: bigint, data: "0x..." },
  },
  relay?: { mode: "auto" },
});
```

### Solana call (`kind: "solana"`) — EVM → Solana only

```typescript
client.call({
  route: { sourceChain: base.id, destinationChain: solanaMainnet.id },
  call: {
    kind: "solana",
    call: {
      instructions: [{
        programId: "SolanaProgramId111111111111111111111111111111",
        accounts: [{
          pubkey: "AccountPubkey11111111111111111111111111111111",
          isWritable: boolean,
          isSigner: boolean,
        }],
        data: Uint8Array,
      }],
    },
  },
});
```

## Relay Modes

| Mode | Behavior |
|------|----------|
| `auto` | SDK submits the transaction on the destination automatically after initiation |
| `manual` | Caller must call `prove` then `execute` |

`auto` only works for **Solana → EVM**. EVM → Solana always requires manual `prove` + `execute`.

## Chain ID Constants

```typescript
import { base, baseSepolia, solanaMainnet, solanaDevnet } from "bridge-sdk";
// base.id         → "eip155:8453"
// baseSepolia.id  → "eip155:84532"
// solanaMainnet.id → "solana:mainnet"
// solanaDevnet.id  → "solana:devnet"
```

Always use `.id` from these constants in `route` objects.
