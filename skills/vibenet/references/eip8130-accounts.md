# EIP-8130 accounts and transactions (viem)

Creating 8130 smart accounts and sending batched calls on vibenet / Base
Sepolia with viem's `experimental/eip8130` module. For network endpoints and
install, see the [skill root](../SKILL.md).

## Core concepts

- **Account** — a viem-style account object with `.address` (deterministic,
  CREATE2-derived), `.create()` / `.createChange` (first-tx deploy change), and
  `signTransaction`. Create via `newSmartAccount8130` / `to8130Account` /
  `toEoa8130Account`.
- **Signer** — a signing object that can produce `sender_auth`. For K1, use
  `privateKeyToAccount(pk)` (a viem `LocalAccount`). For P-256 / WebAuthn use
  `toP256Signer` / `toWebAuthnSigner`.
- **Actor** — an on-chain identity (`{ actorId, authenticator }`), built with
  `key.k1(address)` / `key.p256(...)` / `key.webAuthn(...)`. Used for
  `initialActors`, `authorizeActor`, `revokeActor` — **not** as the `signer`
  passed to `newSmartAccount8130`.
- **Scope** (`actorScope`) — `scopeUnrestricted` (0x00) is admin. Bits:
  `sender` `policy` `nonce` `selfPayer` `sponsorPayer`. A policy-bearing actor
  must be restricted (non-zero scope), or `authorizeActor` throws.
- **Nonce mode** — admin (`0x00`) or an actor with the `nonce` bit
  (`SCOPE_NONCE`) may use **ordered** (sequenced, expiry-free) *or* nonce-free
  (expiring) nonces; sends default to ordered. Only a restricted actor
  **without** `SCOPE_NONCE` is confined to nonce-free.
- **Policy** — on-chain rules (e.g. `SessionPolicy`: per-token spend limits +
  call scopes). See
  [session-keys-and-policies.md](session-keys-and-policies.md).
- **Calls** — a batch of `{ to, value?, data? }` executed atomically, with
  optional signed top-level `metadata` (set via `dataSuffix` on send).
- **Payer (ERC-8168)** — a service that co-signs `payer_auth` to pay gas. See
  [payer-sponsorship.md](payer-sponsorship.md).

## Minimal end-to-end: create a smart account and send a batch

```ts
import { privateKeyToAccount, generatePrivateKey } from "viem/accounts";
import {
  createPublicClient, http, parseEther, toHex,
  newSmartAccount8130, sendCalls8130, estimateGas8130, encodeWalletCalls,
  waitForTransactionReceipt8130, allPhasesSucceeded,
} from "viem/experimental/eip8130";

const chainId = 84538453; // vibenet (Base Sepolia = 84532)
const RPC_URL = "https://rpc.vibes.base.org"; // 8130-capable public RPC
const chain = {
  id: chainId,
  name: "vibenet",
  nativeCurrency: { name: "Ether", symbol: "ETH", decimals: 18 },
  rpcUrls: { default: { http: [RPC_URL] } },
};
const client = createPublicClient({ chain, transport: http(RPC_URL) });
// Browser apps: use https://vibes.base.org/api/vibenet/account/rpc instead
// (same chain, CORS-safe proxy).

// 1) Signer = LocalAccount (NOT key.k1 — that builds an actor identity).
const signer = privateKeyToAccount(generatePrivateKey());
//    P-256: toP256Signer({ privateKey }) · WebAuthn: toWebAuthnSigner(...)

// 2) Deterministic account — address exists before any tx. The owner is an
//    admin actor (scope 0x00), so sends default to ORDERED (sequenced) nonces,
//    which are expiry-free. (Nonce-free/expiring mode is opt-in via
//    `nonceKey: nonceKeyMax` — see Gotchas for its current known bug.)
//    key.k1(signer.address) is what newSmartAccount8130 uses internally for
//    the primary actor — you only call key.* when authorizing extra actors.
const account = newSmartAccount8130({ signer }); // synchronous — no await
// (The fork's TS types may require casting a K1 LocalAccount when passing
// it as `signer`.)

// 3) Fund account.address (faucet), then estimate + send. The drip responds
//    with { tx_hash, amount_wei, to } and grants 0.1 ETH, usually landing in
//    ~2s — but treat the shape as unstable: confirm funding by polling
//    eth_getBalance until non-zero (allow ~60s and handle rate limits).
await fetch("https://vibes.base.org/api/vibenet/faucet/drip", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({ address: account.address }),
});

const calls = [{ to: "0x…recipient", value: parseEther("0.001") }];
const wire = encodeWalletCalls({ account: account.address, calls: [calls] });
const gas = await estimateGas8130(client, {
  sender: account.address,
  accountChanges: [account.createChange],
  calls: wire,
});

const hash = await sendCalls8130(client, {
  account,
  accountChanges: [account.createChange], // omit on subsequent txs
  calls,
  dataSuffix: toHex("invoice #4242"), // maps to signed metadata
  gas: (gas * 120n) / 100n,
});

// 4) Wait and check every phase succeeded.
const receipt = await waitForTransactionReceipt8130(client, { hash });
if (!allPhasesSucceeded(receipt)) throw new Error("a phase reverted");
```

An 8130 receipt executes in **phases** (one per call batch). `phaseStatuses`
on the receipt reports per-phase success for CALL phases only —
account-change application is not covered (see
[session-keys-and-policies.md](session-keys-and-policies.md) for why config
changes need a read-back instead). UIs that display per-phase results should
render `phaseStatuses` and treat `allPhasesSucceeded(receipt)` as the overall
verdict; don't rely on `receipt.status` alone. For the exact field shape,
check `src/experimental/eip8130` on the fork branch — it is experimental and
may shift.

## Canonical deployment

Canonical contract addresses per chain come from `getEip8130Deployment(chainId)`
(or `canonicalEip8130Deployment`): `accountConfiguration`, `accounts.*`,
`authenticators.*`, `policies.{manager,sessionPolicy}`.

The current canonical deployment uses AccountConfiguration
`0x53648Cf00356fbAA1F2B531715c6B64AaBDE1555`, DefaultAccount
`0x58da469ef71Dd4B092B010CdA37DE124C926EebD`, PolicyManager
`0x6e9E627770C1c90371A2E4CB9474A7Af577a4306`, and SessionPolicy
`0x58ef2d572a1bC528f0B9121d686B2618809604Dc`.

## Account creation modes

- `newSmartAccount8130({ signer })` — new CREATE2 smart account (most common).
  `signer` must be a signing account (`privateKeyToAccount(pk)`, `toP256Signer`,
  or `toWebAuthnSigner`) — **not** `key.k1(...)`.
- `to8130Account({ signer, userSalt, code, initialActors, authenticator, accountConfigAddress })`
  — full control over salt / initial actors.
- `to8130Account({ signer, address, authenticator })` — a configured (non-default)
  actor on an existing/delegated account.
- `toEoa8130Account(signer)` — an EOA acting as its own default K1 actor
  (raw 65-byte sig, EIP-7702 delegation via `account.delegate(impl)`).

## Reading account state (viem actions)

All take `(client, params)` and read the on-chain `AccountConfiguration`:
`getActorConfig8130`, `isActor8130`, `getPolicy8130`, `getSessionSpend8130`,
`getLockStatus8130` / `isLocked8130`, `getConfigSequence8130`,
`getTransactionCount8130`, `getTransaction8130`, `getTransactionReceipt8130`,
`waitForTransactionReceipt8130`.

## Locking

`lockCall` / `initiateUnlockCall` build `applySignedLockChanges` calls; hash the
change to sign with `hashLockChange8130` (`lockChangeTypehash`). `lockCall`
requires `unlockDelay >= 1`.

## Gotchas

- **`key.k1` ≠ signer.** `key.k1(address)` builds an actor id for authorize /
  `initialActors`. Passing it (or a raw private-key hex) as `signer` to
  `newSmartAccount8130` fails with an opaque `pad()` TypeError — use
  `privateKeyToAccount(pk)`.
- Fund `account.address` **before** a self-paid first tx — the deploy+batch pays
  gas from the account (unless a payer sponsors it).
- Only the **first** tx includes `account.createChange`; later txs omit it.
- After a successful create, `eth_getCode` on the account returns an EIP-1167
  minimal proxy delegating to the canonical DefaultAccount — but the read
  lags ~1 block behind the receipt, so an immediate getCode can return `0x`
  on a tx that succeeded. Poll before concluding the deploy failed (same lag
  as config-change read-backs).
- Attribution goes in `dataSuffix` on `sendCalls8130` (maps to signed `metadata`).
- **Always pass explicit `gas`** to `sendCalls8130` (estimate with
  `estimateGas8130`, add ~20% headroom, as in the example above). Omitting it
  gets the tx rejected with the misleading error
  `transaction type not supported` — live-confirmed, and easy to misread as
  an RPC capability problem.
- `rpc.vibes.base.org` **is** fine for `0x79` broadcasts (Node/scripts). The
  `account/rpc` URL is only required in the browser (CORS proxy to the same
  chain).
- **Nonce-free (expiring) sends have a known bug (planned fix July 22, 2026):**
  the node can intermittently reject a valid `0x79` with a misleading
  `transaction type not supported` (the short `expiry` lapses before
  validation). Until then, prefer **ordered (expiry-free)** sends — the default
  for admin and `SCOPE_NONCE` actors — which are unaffected.
- Contract addresses are bytecode-derived — the deployed system must be compiled
  with the same solc as `canonicalEip8130Deployment`, or account creation fails
  with "create address mismatch".
- Chains must be 8130-aware: use `register8130Chains` / `is8130Enabled` when
  operating outside the built-in `eip8130ChainIds`.
