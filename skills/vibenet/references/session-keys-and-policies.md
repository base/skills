# Session keys, actors, and policies (EIP-8130)

Authorizing scoped session-key actors with on-chain policies, and verifying
config changes correctly. For account creation and core concepts, read
[eip8130-accounts.md](eip8130-accounts.md) first.

## Authorize a policy-gated session actor

```ts
import {
  key, authorizeActor, actorScope,
  defineSessionPolicy, encodeSessionPolicyConfig, encodeSessionPolicyAction,
} from "viem/eip8130";

const policyConfig = encodeSessionPolicyConfig({
  tokenLimits: [{ token: usdv, limit: 100_000_000n, period: 604_800n }], // 100 USDV / week
  callScopes: [{ target: usdv, selectorRules: [{ selector: "0xa9059cbb" }] }], // transfer only
});
// `manager` / `policy` default to the canonical PolicyManager / SessionPolicy
// (same addresses on every chain — verified equal to
// getEip8130Deployment(84538453).policies on vibenet). Override only for your
// own contracts.
const session = defineSessionPolicy({
  account: account.address,
  policyConfig,
  validUntil: 1_900_000_000n,
});

// There is no install step. Every execute carries the full PolicyBinding and
// the manager recomputes its authorized commitment.
const call = session.executeCall(encodeSessionPolicyAction({ target, value: 0n, data }));

// Actor identity for authorize (not a LocalAccount). SCOPE_POLICY is set
// automatically when `policy` is present.
const sessionActor = key.p256({ x: "0x…", y: "0x…" }); // or key.p256(p256Signer.publicKey)
const change = authorizeActor(sessionActor, {
  // POLICY gates every call to the manager; SELF_PAYER lets the key pay gas
  // from the account (needed for self-paid session sends — see "Use the
  // session key"). Adding `operator` would bypass the gate.
  scope: actorScope.policy | actorScope.selfPayer,
  expiry: 1_900_000_000n,
  policy: session.actorPolicy,
});
// `change` is an unsigned change object. Apply it via account.change([change],
// { chainId, sequence }) with a LIVE-read sequence — see Sequence correctness
// below — then include the result in a sendTransaction signed by an admin
// actor. Don't hand-build accountChanges with a hardcoded sequence; that is
// the #1 cause of a silently skipped authorize.
```

A policy actor must have a non-zero scope; admin (scope 0) + policy is
rejected by `authorizeActor`.

**Scope names changed on the fork (Aug 2026).** `actorScope` is now
`{ operator: 1, selfPayer: 2, sponsorPayer: 4, policy: 8, nonce: 16 }` —
there is no `actorScope.sender` any more (it is `operator`), so old examples
that pass `scope: actorScope.sender` send `undefined` and fail. OR the bits
you need:

| Bit | Grants | Add it when |
|---|---|---|
| `policy` (8) | initiation gated to the PolicyManager | always, for a session key — it is set for you when `policy` is passed |
| `selfPayer` (2) | the key may pay gas from the account | the session key sends self-paid txs (live-confirmed required) |
| `sponsorPayer` (4) | the key's txs may be payer-sponsored | the session key sends through an ERC-8168 payer |
| `nonce` (16) | ordered (expiry-free) nonces | you don't want to be confined to nonce-free (expiring) sends |
| `operator` (1) | ungated initiation | never on a policy key — it bypasses the gate |

**Native ETH is fail-closed.** A session key may attach `value` only if the
config has a `tokenLimits` entry for the zero address; without one every
value-bearing call reverts. ERC-20s differ: an absent token limit is unbounded,
because the `callScopes` allowlist is the gate.

**Register the PolicyManager as an operator too** (`authorizeActor(key.k1(session.manager),
{ scope: actorScope.operator })`) so its forwarded `executeBatch` can land on the
account — the upstream `fulfillGrantPermissions` helper folds this in
automatically; when hand-rolling, ride it in the same change batch as the
session-key authorize (live-confirmed: both bind in one tx).

## Use the session key (live-confirmed on vibenet, 2026-09-09)

Two things the upstream docs don't spell out, both learned from
`EIP-8130 validation failed: actor scope insufficient`:

- **A self-paying session key needs `selfPayer` as well.** Scope
  `actorScope.policy` alone (`0x8`) authorizes fine but the node rejects the
  key's own sends; `actorScope.policy | actorScope.selfPayer` (`0xa`) works.
  (Sponsored session sends would use `sponsorPayer` instead.)
- **A restricted actor without the `nonce` bit must send nonce-free**
  (`nonceKey: nonceKeyMax`); the default ordered nonce is rejected.

```ts
import { toAccount, toP256Signer, sendTransaction, estimateGas, waitForTransactionReceipt,
  canonicalAuthenticators, nonceKeyMax, encodeSessionPolicyAction } from "viem/eip8130";

// A second handle on the SAME address, driven by the session signer. Don't
// pass `scope` here — the handle reads it on-chain, and a declared value that
// disagrees fails with `Declared signing scope 0x8 does not match on-chain
// actor scope 0xa`.
const sessionAccount = toAccount({
  signer: toP256Signer({ privateKey: sessionPrivateKey }),
  address: account.address,
  authenticator: canonicalAuthenticators.p256,
});

const action = session.executeCall(
  encodeSessionPolicyAction({ target: recipient, value: parseEther("0.001"), data: "0x" }),
); // → a call to the PolicyManager; the manager enforces the committed policy

const gas = await estimateGas(client, {
  sender: account.address,
  calls: [[action]],
  senderAuthAuthenticator: canonicalAuthenticators.p256,
  senderActorId: sessionKey.actorId,
});
const { timestamp } = await client.getBlock();
const hash = await sendTransaction(client, {
  account: sessionAccount,
  calls: [action],
  gas: (gas * 120n) / 100n,
  nonceKey: nonceKeyMax,   // nonce-free: required without the `nonce` scope bit
  now: timestamp * 1000n,  // anchor the 20s expiry to chain time, not the laptop clock
});
const receipt = await waitForTransactionReceipt(client, { hash, pollingInterval: 100 });
// status 0x1, phaseStatuses ['0x1'], and the recipient's balance moved by exactly 0.001 ETH.
```

### The binding must be byte-identical at use time

The commitment stored on the actor is
`keccak256(abi.encode(account, policy, keccak256(policyConfig), validAfter,
validUntil, salt))`, and `session.executeCall` passes the full binding on-chain
for the manager to recompute and compare. So the `defineSessionPolicy` inputs
at **use** time must equal the ones at **authorize** time to the byte — a
wall-clock `validUntil` computed at authorize time and recomputed later
silently produces a different commitment and the manager rejects the call.
Either persist the whole `session.binding`, or pin `validAfter` / `validUntil`
/ `salt` to their `0n` defaults (deterministic binding) and put the time bound
on the actor's `expiry` instead.

### Failure signature: the session tx lands but its phase reverts

If a session-key transaction broadcasts fine but comes back `status: 0x0`,
`phaseStatuses: ["0x0"]` with no error text, check (in this order) that the
PolicyManager is bound as an operator actor
(`isActor(client, { account, actorId: key.k1(session.manager).actorId })`),
that the binding is byte-identical (above), and that a value-bearing call has
a zero-address `tokenLimits` entry. `EIP-8130 validation failed: actor scope
insufficient` at broadcast means the key lacks `selfPayer` (self-paid) or
`sponsorPayer` (sponsored).

### Reading the spend meter

`getSessionSpend` is keyed by the **commitment and the exact committed limit**,
not by account: `getSessionSpend(client, { commitment: session.commitment,
tokenLimit: { token, limit, period }, sessionPolicy? })` — re-supply the very
`{ token, limit, period }` you encoded (zero address = native ETH).

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
- **Reads can lag ~1 block** behind the receipt (200ms on vibenet today, 2s
  on Base Sepolia) — poll the read-back.

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

// The Keystore address is built in (`keystoreAddress`) — no per-chain
// `accountConfiguration` argument any more.
const { local } = await getConfigSequence(client, { account: account.address });
// `local` is the NEXT local-channel sequence word (epoch<<32 | seq), read
// live — do not assume 0 or 1. Live-observed on vibenet: 0 before the create
// tx, 1 right after it, 2 after one authorize.
const change = await account.change([authorizeActor(/* … */)], {
  chainId, // local channel for session keys
  sequence: local,
});
// … send the tx, then verify by read-back (polled for ~1 block of lag):
const bound = await isActor(client, { account: account.address, actorId });
if (!bound) throw new Error("authorize was skipped — check sequence/channel");
// getActorConfig(client, { account, actorId }) → { authenticator, scope, expiry, hasPolicy }
```

To authorize a session key **in the same transaction that creates the
account**, use `sequence: 1n` (the create bumps local 0→1 before the change
applies) and pass `accountChanges: [account.createChange, change]` —
live-confirmed on vibenet.

## Reference

- Session-key end-to-end walkthrough (create → register PolicyManager +
  session key → drive a call through the session key, with read-back
  verification at each step):
  https://gist.github.com/chunter-cb/bf70c53a5ab6d8361ce7f4215b776114
