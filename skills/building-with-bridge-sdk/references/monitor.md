# Monitoring Reference

## `monitor(messageRef, options)`

Polls a `MessageRef` until a terminal state is reached or the timeout expires.

```typescript
for await (const s of client.monitor(messageRef, { timeoutMs: 60_000 })) {
  console.log(s.type, s.at);
}
```

### Terminal States

| State | Meaning |
|-------|---------|
| `Executed` | Message executed successfully — done |
| `Failed` | Execution failed — done |
| `Expired` | Message expired before execution — done |

Non-terminal states (`Initiated`, `InitiatedTxConfirmed`, `Proven`, `ProvenTxConfirmed`) keep the loop running.

### Timeout

```typescript
client.monitor(messageRef, { timeoutMs: 120_000 });
```

- If timeout is reached without a terminal state, the loop ends cleanly (no error)
- Always follow the loop with `client.status(messageRef)` to determine final state

## `status(messageRef)`

Reads current state without polling:

```typescript
const s = await client.status(messageRef);
console.log(s.type); // "Initiated" | "InitiatedTxConfirmed" | "Proven" | "ProvenTxConfirmed" | "Executed" | "Failed" | "Expired"
```

## `capabilities(route)`

Checks whether a route supports `transfer`/`call` and auto-relay:

```typescript
const caps = client.capabilities({
  route: { sourceChain: solanaMainnet.id, destinationChain: base.id },
});
// { supportsTransfer, supportsCall, supportsAutoRelay }
```

## Key Rules

- **Always `prove` before `execute`** — calling `execute` on an unproven message reverts
- **Wait for `InitiatedTxConfirmed`** before calling `prove` — otherwise the proof will be submitted for a non-finalized message
- **`monitor` is polled locally** — it calls `status` in a loop; be mindful of RPC rate limits
