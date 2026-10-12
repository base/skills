---
name: vibenet
description: >-
  Build on vibenet — Base's devnet for native account abstraction (EIP-8130),
  payer gas sponsorship (ERC-8168), and Cobalt 200ms native blocks. Use
  whenever the user mentions vibenet, EIP-8130, ERC-8168, 8130 accounts, native
  account abstraction, session keys, actors, policies, payers, gas sponsorship
  on Base, 200ms blocks, Cobalt, BaseTime, timestampMs / blockTimestampMs,
  sub-second or millisecond block timestamps, migrating from Flashblocks, or
  newHeads / WebSocket streaming on vibenet — or is writing code that creates
  or operates 8130 smart accounts, authorizes session-key actors, sends batched
  calls, sponsors gas with a payer, queries or streams vibenet blocks, times a
  transaction's inclusion, or wires a frontend/script against the vibenet
  devnet or Base Sepolia.
---

# Vibenet

Vibenet is Base's devnet for **EIP-8130 native account abstraction**: account
abstraction in the protocol itself. Accounts are portable across EVM chains,
support multiple signer types (secp256k1, P-256, WebAuthn), key rotation
without changing address, scoped session-key actors, on-chain policies, and
native **ERC-8168** gas sponsorship. The tooling lives in viem's `eip8130`
module (fork branch — not yet in npm `viem`). Vibenet is also the first Base
network running **Cobalt 200ms native blocks** (five canonical blocks per
second, with a millisecond `timestampMs` on every block) — that part needs no
fork, stock `viem` works. See
[references/200ms-blocks.md](references/200ms-blocks.md).

## Network

| Endpoint | Value |
|----------|-------|
| Chain ID | `84538453` |
| Public execution RPC | `https://rpc.vibes.base.org` — 8130-capable (`AA_TX_TYPE` / `0x79`), serves `access-control-allow-origin: *` |
| WebSocket RPC | `wss://rpc.vibes.base.org/ws` — `newHeads`, `logs`, `transactionReceipts` subscriptions (the `/ws` path is required) |
| Block time | **200ms** (Cobalt); blocks carry `timestampMs`, BaseTime predeploy at `0x4200000000000000000000000000000000000030` |
| Browser RPC proxy | `https://api.vibes.base.org/api/vibenet/account/rpc` — passes through all `eth_*`, including `0x79` broadcasts and receipt polling |
| Hosted payer (ERC-8168) | `https://api.vibes.base.org/api/vibenet/account/payer` |
| Faucet | `POST https://api.vibes.base.org/api/vibenet/faucet/drip` with `{ "address": "0x…" }` |
| Faucet status | `GET https://api.vibes.base.org/api/vibenet/faucet/status` — drip size, cooldowns, USDV/NFV token addresses |
| Chain health | `GET https://api.vibes.base.org/api/vibenet/chain-health` — key off `healthy` + `headAgeSecs`; `stuckSecs` is not actionable on its own (seen at 19000 on a healthy chain) |
| Landing page / explorer | `https://chain.base.org/vibenet`, `https://chain.base.org/vibenet/explorer` |
| Base Sepolia (also 8130-enabled) | `https://sepolia.base.org`, chain id `84532` |

**The API host is `api.vibes.base.org`, not `vibes.base.org`.** The bare host
302-redirects to the `chain.base.org/vibenet` HTML page; viem's HTTP transport
then tries to parse that as JSON and throws `Unrecognized token '<'`, which
reads like a code bug rather than a wrong URL.

All `api.vibes.base.org` endpoints (RPC proxy, payer, faucet) send permissive
CORS headers, and so does `rpc.vibes.base.org` — so browser apps can talk to
either. Prefer `rpc.vibes.base.org` for execution and reserve the `account/rpc`
proxy for when you specifically want the hosted path. The public RPC is
method-allowlisted: `eth_getHeaderBy*`, `eth_getBlockReceipts`,
`eth_sendRawTransactionSync`, `eth_simulateV1` and `txpool_*` answer
`rpc method is not whitelisted`.

**Only 8130 / 8168 code needs the fork below.** Querying blocks, streaming
`newHeads`, and sending plain EOA transactions on vibenet work with stock
`npm install viem`.

The 8130 modules are additive to viem itself, proposed upstream in
[wevm/viem#5004](https://github.com/wevm/viem/pull/5004) (open, out of draft —
not yet merged or released to npm). Until it ships, they have to be built from the fork
branch the PR is opened from: `chunter-cb/viem` `feat/eip-8130-production`.

**Use the bundled installer** — it does the whole clone→build→link dance, which
is error-prone by hand:

```bash
scripts/setup-viem-8130.sh [APP_DIR] [BUILD_DIR]   # APP_DIR defaults to the current directory
```

`BUILD_DIR` defaults to `<APP_DIR>/.viem-8130-src` — a full viem monorepo
checkout with its own `node_modules` (~500 MB). The script appends
`.viem-8130-src/` to the app's `.gitignore` so a `git add .` can't commit it;
for several apps, pass one shared `BUILD_DIR` outside them (npm records the
`file:` path in `package.json`). Node 22 works despite the fork's
`node >=24.5` engine warning.

When PR #5004 merges and a viem release ships the modules, this collapses to
`npm install viem@latest` — the imports (`viem/eip8130`, `viem/eip8168`) and
APIs are unchanged, so no code moves.

<details><summary>What the script does, and why each step is needed</summary>

The tooling is **not installable from git directly**: viem's workspace uses
pnpm's `catalog:` protocol, so `npm install "viem@github:…"` fails outright, and
`bun add "viem@github:…"` "succeeds" but leaves you an unbuilt monorepo with no
`exports` field. So you clone, build, then depend on the built package (which
lives in viem's `src/`):

```bash
git clone -b feat/eip-8130-production https://github.com/chunter-cb/viem viem-fork
cd viem-fork && npx pnpm install --ignore-scripts && npx pnpm run build

# then in your app — --install-links is required:
npm install --install-links "viem@file:../viem-fork/src"
```

**`--install-links` is required.** Without it npm symlinks `node_modules/viem`
to a path outside the project root, and Turbopack/Next.js then fails with
`Module not found: Can't resolve 'viem'` for a package that is plainly there
(`tsc` resolves it fine, which makes it look like a bundler bug).
</details>

Then import from `viem/eip8130` (and `viem/eip8168` for payers). Core helpers
like `createPublicClient` / `parseEther` come from plain `viem` — the 8130
module does not re-export them.

Set `"target": "ES2020"` or later in `tsconfig.json`. BigInt literals (`0n`)
trigger TS2737 on any lower `target` — the check depends on `target`, not
`lib`, and many generated configs still default to an older target.

## Accounts Have No Deploy Step

Creating an account derives a CREATE2 address locally — synchronous, zero RPC,
`eth_getCode` still `0x`. It becomes real as a **side effect of its first
transaction**, which carries `account.createChange` alongside your actual calls.
There is nothing else to call. The shortest path from nothing to a deployed
account is a *sponsored* first tx (no faucet, no funding — for a zero-value
first tx; sponsorship covers gas, never value); the self-paid route needs the
address funded first. Read deployment state from `eth_getCode`, never
from optimistic local state — it decides whether the next tx carries
`createChange`. Full lifecycle:
[references/eip8130-accounts.md](references/eip8130-accounts.md).

## Safety Guardrails

- **Never commit private keys** — generate throwaway keys for devnet scripts,
  read real ones from env vars.
- **`key.k1(...)` builds an actor identity, not a signer** — passing it (or a
  raw private-key hex) as `signer` fails with an opaque `pad()` TypeError. Use
  `privateKeyToAccount(pk)`.
- **Verify config changes by on-chain read-back** (`isActor` /
  `getConfigSequence`), never by receipt logs or `status: success` — a
  skipped authorize is silent.
- **Read the live config sequence right before signing** — a hardcoded
  sequence causes silent no-ops.

## Task Routing

Read the reference for your task:

| Task | When to Use | Reference |
|------|-------------|-----------|
| **Accounts & transactions** | Create an 8130 smart account, the counterfactual→deployed lifecycle, send batched calls, attribution metadata, gas estimation, reading account state, locking, gotchas | [references/eip8130-accounts.md](references/eip8130-accounts.md) |
| **Session keys & policies** | Authorize/revoke actors, scopes, SessionPolicy spend limits, config sequences, verifying "silent" changes | [references/session-keys-and-policies.md](references/session-keys-and-policies.md) |
| **Gas sponsorship** | Sponsor gas with a payer (ERC-8168), gasless onboarding, `send` vs `sign` modes | [references/payer-sponsorship.md](references/payer-sponsorship.md) |
| **200ms blocks & timing** | Read a block's millisecond timestamp (`timestampMs`), decode the BaseTime deposit / predeploy, stream `newHeads` over WebSocket, send a tx and see which 200ms block it landed in, fix viem polling, migrate from Flashblocks | [references/200ms-blocks.md](references/200ms-blocks.md) |

## Operating Procedure

1. **Classify the task** using the table above and read the relevant reference
   before implementing.
2. **Pick the right RPC**: `rpc.vibes.base.org` works from both Node and the
   browser; `wss://rpc.vibes.base.org/ws` for subscriptions;
   `api.vibes.base.org/api/vibenet/account/rpc` is the hosted proxy to the same
   chain. Never `vibes.base.org` — that host is not an API.
3. **Implement** with explicit chain id, the `scripts/setup-viem-8130.sh`
   install (8130/8168 only), read-back verification for any account-config
   change, and an explicit `pollingInterval` (≈100ms) on every receipt wait or
   block watch — viem's defaults (4000ms, or a 500ms floor) hide the 200ms
   cadence.
4. **Deliver** runnable code, install commands, and any manual steps (env
   vars, faucet funding).

## For Edge Cases and Latest API Changes

- **EIP-8130 spec**: [eip.tools/eip/8130](https://eip.tools/eip/8130)
  (payer standard: [eip.tools/eip/8168](https://eip.tools/eip/8168))
- **viem fork**: [`chunter-cb/viem` `feat/eip-8130-production`](https://github.com/chunter-cb/viem/tree/feat/eip-8130-production)
  (upstream PR: [wevm/viem#5004](https://github.com/wevm/viem/pull/5004); API
  surface: `src/eip8130/index.ts`; docs: `site/pages/eip8130`)
- **Deep guide (chaptered)**: `github.com/chunter-cb/eip-8130-web` (`/guide/*`)
- **Session-key walkthrough** (names are stale — map `to8130Account` →
  `toAccount`, `isActor8130` → `isActor`, `sendCalls` → `sendTransaction`; its
  `managerActor` step is the PolicyManager-as-operator authorize in the session
  reference):
  [gist.github.com/chunter-cb/bf70c53a5ab6d8361ce7f4215b776114](https://gist.github.com/chunter-cb/bf70c53a5ab6d8361ce7f4215b776114)
- **200ms blocks (Cobalt)**:
  [docs.base.org/upgrades/cobalt/200ms-blocks](https://docs.base.org/upgrades/cobalt/200ms-blocks),
  [migrate-from-flashblocks](https://docs.base.org/upgrades/cobalt/migrate-from-flashblocks),
  [test-on-vibenet](https://docs.base.org/build-on-base/test-on-vibenet)

## Installation

```bash
npx skills add base/skills --skill vibenet
```
