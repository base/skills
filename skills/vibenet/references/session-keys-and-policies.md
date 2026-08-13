# Session keys, actors, and policies (EIP-8130)

Authorizing scoped session-key actors with on-chain policies, and verifying
config changes correctly. For account creation and core concepts, read
[eip8130-accounts.md](eip8130-accounts.md) first.

## Authorize a policy-gated session actor

```ts
import {
  key, authorizeActor, actorScope,
  defineSessionPolicy, encodeSessionPolicyConfig, getEip8130Deployment,
} from "viem/eip8130";

const dep = getEip8130Deployment(chainId);
const policyConfig = encodeSessionPolicyConfig({
  tokenLimits: [{ token: usdv, limit: 100_000_000n, period: 604_800n }], // 100 USDV / week
  callScopes: [{ target: usdv, selectorRules: [{ selector: "0xa9059cbb" }] }], // transfer only
});
const session = defineSessionPolicy({
  account: account.address, policy: dep.policies.sessionPolicy,
  policyConfig, manager: dep.policies.manager, validUntil: 1_900_000_000n,
});

// There is no install step. Every execute carries the full PolicyBinding and
// the manager recomputes its authorized commitment.
const call = session.executeCall({ target, value: 0n, data });

// Actor identity for authorize (not a LocalAccount). SCOPE_POLICY is set
// automatically when `policy` is present.
const sessionActor = key.p256({ x: "0x…", y: "0x…" });
const change = authorizeActor(sessionActor, {
  scope: actorScope.sender,
  expiry: 1_900_000_000n,
  policy: session.actorPolicy,
});
// `change` is an unsigned change object. Apply it via account.change([change],
// { chainId, sequence }) with a LIVE-read sequence — see Sequence correctness
// below — then include the result in a sendCalls signed by an admin actor.
// Don't hand-build accountChanges with a hardcoded sequence; that is the #1
// cause of a silently skipped authorize.
```

A policy actor must have a non-zero scope; admin (scope 0) + policy is
rejected by `authorizeActor`.

## Verifying a config change (and why it can look "silent")

Account changes (authorize/revoke) do **not** surface success the way calls do.
Check them by **reading back on-chain state**, not by the receipt:

- **`receipt.logs` is empty even on a successful authorize.** `ActorAuthorized`
  is not surfaced as a normal EVM log here — "no events" is NOT a failure. Do
  not gate success on scanning logs.
- **`allPhasesSucceeded` / `phaseStatuses` only cover CALL phases**, not the
  account-change application. On a change-only transaction (no calls)
  `phaseStatuses` is absent entirely and `allPhasesSucceeded` returns `true`
  vacuously — it is reporting on nothing.
- **A wrong sequence is rejected at broadcast, not silently applied.** Signing a
  change over a stale *or* future sequence makes `eth_sendRawTransaction` fail
  with `EIP-8130 validation failed: config change sequence mismatch` (surfaced
  by viem as `InvalidInputRpcError: Missing or invalid parameters`). The tx
  never lands, so there is no receipt to inspect — the failure is loud, but the
  error text names neither the sequence you used nor the one expected.
- **The real trap is the inverse: a config change can apply on a transaction
  that reports failure.** Live-confirmed — a tx carrying an authorize plus a
  reverting call came back `status: 0x0` with `phaseStatuses: ["0x0"]`, yet the
  actor was bound and the config sequence had bumped. Account changes are not
  atomic with the calls they ride along with, in either direction. **Never infer
  config state from `receipt.status`.**
- **The only reliable check is a read-back:** `isActor`,
  `getActorConfig`, or a bumped `getConfigSequence` — after a failed tx
  as much as a successful one.
- **Reads lag ~1 block (~2s)** behind the receipt — poll the read-back.

## Sequence correctness

The usual cause of a silent no-op: the digest binds
`(account, chainId, sequence)`. Always read the **live** counter for the channel
right before signing — never hardcode it. Session-key auth uses the **local**
channel (`chainId = chain.id`); owner changes use the **multichain** channel
(`chainId = 0`). The first-authorize sequence depends on the deploy path:

| Deploy path | First local sequence |
|---|---|
| CREATE2 smart account (`newSmartAccount` + `account.createChange`) | `1` (create bumps local 0→1) |
| Configured account on an existing address (`toAccount({ address })`) | `1` |
| Bare 7702 delegation (`toEoaAccount` + `account.delegate`) | `0` (delegation does not initialize state) |

```ts
import { getConfigSequence, isActor } from "viem/eip8130";

const { local } = await getConfigSequence(client, {
  accountConfiguration: dep.accountConfiguration,
  account: account.address,
}); // read live — do not assume 0 or 1
const change = await account.change([authorizeActor(/* … */)], {
  chainId, // local channel for session keys
  sequence: Number(local),
});
// … send the tx, then verify by read-back (polled for ~1 block of lag):
const bound = await isActor(client, {
  account: account.address, actorId, accountConfiguration: dep.accountConfiguration,
});
if (!bound) throw new Error("authorize was skipped — check sequence/channel");
```

## Reference

- Session-key end-to-end walkthrough (create → register PolicyManager +
  session key → drive a call through the session key, with read-back
  verification at each step):
  https://gist.github.com/chunter-cb/bf70c53a5ab6d8361ce7f4215b776114
