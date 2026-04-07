---
name: building-with-bridge-sdk
description: >
  Use when bridging assets between Solana and EVM chains via the Base Bridge SDK.
  Invoke for: "bridge to Base from Solana", "bridge SOL to Base", "bridge assets from Solana
  to Ethereum", "cross-chain transfer Solana Base", "use the Base bridge SDK", or "bridge
  from EVM to Solana". Does not apply to L1 Ethereum <-> Base Standard Bridge bridging.
---

# Building with Bridge SDK

Integrate the Base Bridge SDK (`bridge-sdk`) for cross-chain transfers and calls between Solana and Base/Ethereum. Covers `createBridgeClient`, `transfer`, `call`, `prove`, `execute`, `status`, and `monitor`.

**SDK status: unaudited — not yet recommended for production use.**

## When to Use This Skill

Use this skill when a developer asks to:
- "Bridge SOL to Base"
- "Bridge assets from Solana to Ethereum"
- "Cross-chain transfer using the Base bridge SDK"
- "How do I use the bridge SDK?"
- "Bridge from Base to Solana"
- Set up Solana ↔ EVM bridging in an app

## Prerequisites

- Node.js 18+ or browser
- A keypair/wallet on the source chain
- `npm install bridge-sdk` (or `bun add bridge-sdk`)

## Quick Start

### Solana → Base (auto-relay)

```typescript
import { createBridgeClient, makeEvmAdapter, makeSolanaAdapter, base, solanaMainnet } from "bridge-sdk";
import { loadSolanaKeypair } from "bridge-sdk/node";

const payer = await loadSolanaKeypair("~/.config/solana/id.json");

const client = createBridgeClient({
  chains: {
    solana: makeSolanaAdapter({ rpcUrl: "https://api.mainnet-beta.solana.com", payer, chain: solanaMainnet }),
    base: makeEvmAdapter({ chain: base, rpcUrl: "https://mainnet.base.org", wallet: { type: "none" } }),
  },
});

const op = await client.transfer({
  route: { sourceChain: solanaMainnet.id, destinationChain: base.id },
  asset: { kind: "native" },
  amount: 1_000_000n, // lamports
  recipient: "0x644e3DedB0e4F83Bfcf8F9992964d240224B74dc",
  relay: { mode: "auto" },
});

for await (const s of client.monitor(op.messageRef, { timeoutMs: 60_000 })) {
  console.log(s.type);
}
```

### EVM → Solana (manual prove + execute)

No auto-relay for this direction. Manual `prove` then `execute` required:

```typescript
const op = await client.transfer({
  route: { sourceChain: base.id, destinationChain: solanaMainnet.id },
  asset: { kind: "native" },
  amount: 1n,
  recipient: "11111111111111111111111111111111",
});

await client.prove(op.messageRef);   // submit proof on Solana
await client.execute(op.messageRef); // execute the message
```

## Chain IDs

| Chain | ID |
|-------|-----|
| Base Mainnet | `eip155:8453` |
| Base Sepolia | `eip155:84532` |
| Solana Mainnet | `solana:mainnet` |
| Solana Devnet | `solana:devnet` |

## Supported Flows

| Direction | Primitive | Relay | Notes |
|-----------|-----------|-------|-------|
| Solana → EVM | `transfer`, `call` | `auto` supported | automatic prove + execute |
| EVM → Solana | `transfer`, `call` | not supported | manual `prove` + `execute` required |
| EVM → EVM | not a target | — | — |
| L1 Ethereum ↔ Base | not covered | — | use Standard Bridge |

**Important:** EVM → Solana always requires a separate `prove` call followed by `execute`. There is no auto-relay for this direction.

## Workflows

### Solana → EVM Transfer

1. Create `BridgeClient` with Solana + EVM adapters
2. `client.transfer({ route: { sourceChain, destinationChain }, asset, amount, recipient, relay: { mode: "auto" } })`
3. `client.monitor(op.messageRef, { timeoutMs })` to wait for terminal state
4. `client.status(op.messageRef)` to read final state

### EVM → Solana Transfer

1. Create `BridgeClient` with EVM + Solana adapters (EVM adapter needs a wallet)
2. `client.transfer({ route, asset, amount, recipient })` — no relay option
3. Wait for `InitiatedTxConfirmed` via monitor
4. `client.prove(op.messageRef)` — submit proof on Solana
5. `client.execute(op.messageRef)` — execute on Solana
6. `client.status(op.messageRef)` for final state

### Cross-Chain Call

```typescript
const op = await client.call({
  route: { sourceChain: solanaMainnet.id, destinationChain: base.id },
  call: {
    kind: "evm",
    call: { to: "0x...", value: 0n, data: "0xd09de08a" },
  },
  relay: { mode: "auto" },
});
```

For Solana→Solana calls via Base: use `kind: "solana"` with `instructions` array. See `examples/baseToSolanaCall.ts` in the SDK repo.

## Route Reference

See [references/routes.md](references/routes.md) for field schemas, token mappings, and relay mode details.

## Monitoring Reference

See [references/monitor.md](references/monitor.md) for terminal states and `status`/`capabilities` API details.

## Security Notes

- **SDK is unaudited** — do not overclaim production readiness
- Never hardcode private keys; use environment variables
- `loadSolanaKeypair` is Node.js-only (`bridge-sdk/node` subpath) — do not import in browser code
- **EVM → Solana prove/execute is irreversible** — a message that executes cannot be undone; always confirm the target address before initiating
- **Relayer operator risk**: If you operate a manual relayer that signs with its own key, do not sign transactions where the relayer pubkey appears as a signer in the instruction set — malicious users can craft txs that steal relayer funds

## Common Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `Transfer failed` / `Call failed` | Wrong `sourceChain`/`destinationChain` | Verify chain IDs match the intended direction |
| `prove` hangs forever | Source message not yet finalized | Wait for `InitiatedTxConfirmed` before calling `prove` |
| `execute` reverts | Message not yet proven | Always `prove` before `execute` |
| `wallet type "none"` errors | No EVM signing wallet configured | Set `wallet: { type: "privateKey", key: "0x..." }` on the EVM adapter |
| `tokenMappings` missing | Bridging ERC20 → Solana without mint mapping | Add `bridgeConfig.tokenMappings` to `createBridgeClient()` |

## Key References

- SDK repo: https://github.com/base/bridge-sdk
- Base Bridge docs: https://docs.base.org/base-chain/quickstart/base-solana-bridge
- Version: 0.1.0
