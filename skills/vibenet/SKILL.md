---
name: vibenet
description: >-
  Build on vibenet — Base's devnet for native account abstraction (EIP-8130)
  and payer gas sponsorship (ERC-8168) using the viem experimental module. Use
  whenever the user mentions vibenet, EIP-8130, ERC-8168, 8130 accounts, native
  account abstraction, session keys, actors, policies, payers, or gas
  sponsorship on Base — or is writing code that creates or operates 8130 smart
  accounts, authorizes session-key actors, sends batched calls, sponsors gas
  with a payer, or wires a frontend/script against the vibenet devnet or Base
  Sepolia.
---

# Vibenet

Vibenet is Base's devnet for **EIP-8130 native account abstraction**: account
abstraction in the protocol itself. Accounts are portable across EVM chains,
support multiple signer types (secp256k1, P-256, WebAuthn), key rotation
without changing address, scoped session-key actors, on-chain policies, and
native **ERC-8168** gas sponsorship. The tooling lives in viem's
`experimental/eip8130` module (fork branch — not yet in npm `viem`).

## Network

| Endpoint | Value |
|----------|-------|
| Chain ID | `84538453` |
| Public execution RPC (Node/scripts) | `https://rpc.vibes.base.org` — 8130-capable (`AA_TX_TYPE` / `0x79`) |
| Browser RPC proxy (CORS-safe) | `https://vibes.base.org/api/vibenet/account/rpc` — passes through all `eth_*`, including `0x79` broadcasts and receipt polling |
| Hosted payer (ERC-8168) | `https://vibes.base.org/api/vibenet/account/payer` |
| Faucet | `POST https://vibes.base.org/api/vibenet/faucet/drip` with `{ "address": "0x…" }` |
| Base Sepolia (also 8130-enabled) | `https://sepolia.base.org`, chain id `84532` |

Install viem from the fork branch, then import from
`viem/experimental/eip8130` (and `viem/experimental/eip8168` for payers):

```bash
bun add "viem@github:chunter-cb/viem#feat/eip-8130"
```

**npm cannot install this branch directly from git** — the fork's workspace
uses pnpm's `catalog:` protocol, so `npm install "viem@github:…"` fails, and
even the bun git install yields an unbuilt monorepo. The reliable path for
npm projects is clone → build → depend on the built package (which lives in
the fork's `src/` directory):

```bash
git clone -b feat/eip-8130 https://github.com/chunter-cb/viem viem-fork
cd viem-fork && npx pnpm install --ignore-scripts && npx pnpm run build
# then in your app: npm install "viem@file:../viem-fork/src"
```

In TypeScript projects, set `"target": "ES2020"` (or later) in
`tsconfig.json` — the 8130 module uses BigInt literals, which the common
ES2017 default rejects at build time.

## Safety Guardrails

- **Never commit private keys** — generate throwaway keys for devnet scripts,
  read real ones from env vars.
- **`key.k1(...)` builds an actor identity, not a signer** — passing it (or a
  raw private-key hex) as `signer` fails with an opaque `pad()` TypeError. Use
  `privateKeyToAccount(pk)`.
- **Verify config changes by on-chain read-back** (`isActor8130` /
  `getConfigSequence8130`), never by receipt logs or `status: success` — a
  skipped authorize is silent.
- **Read the live config sequence right before signing** — a hardcoded
  sequence causes silent no-ops.

## Task Routing

Read the reference for your task:

| Task | When to Use | Reference |
|------|-------------|-----------|
| **Accounts & transactions** | Create an 8130 smart account, send batched calls, attribution metadata, gas estimation, reading account state, locking, gotchas | [references/eip8130-accounts.md](references/eip8130-accounts.md) |
| **Session keys & policies** | Authorize/revoke actors, scopes, SessionPolicy spend limits, config sequences, verifying "silent" changes | [references/session-keys-and-policies.md](references/session-keys-and-policies.md) |
| **Gas sponsorship** | Sponsor gas with a payer (ERC-8168), gasless onboarding, `send` vs `sign` modes | [references/payer-sponsorship.md](references/payer-sponsorship.md) |

## Operating Procedure

1. **Classify the task** using the table above and read the relevant reference
   before implementing.
2. **Pick the right RPC**: `rpc.vibes.base.org` from Node/scripts; the
   `account/rpc` browser proxy from web UIs (same chain, CORS-safe).
3. **Implement** with explicit chain id, the fork-branch install, and read-back
   verification for any account-config change.
4. **Deliver** runnable code, install commands, and any manual steps (env
   vars, faucet funding).

## For Edge Cases and Latest API Changes

- **EIP-8130 spec**: [eip.tools/eip/8130](https://eip.tools/eip/8130)
  (payer standard: [eip.tools/eip/8168](https://eip.tools/eip/8168))
- **viem fork**: `github.com/chunter-cb/viem`, branch `feat/eip-8130`
  (API surface: `src/experimental/eip8130/index.ts`; docs:
  `site/pages/experimental/eip8130`)
- **Deep guide (chaptered)**: `github.com/chunter-cb/eip-8130-web` (`/guide/*`)
- **Session-key walkthrough**:
  [gist.github.com/chunter-cb/bf70c53a5ab6d8361ce7f4215b776114](https://gist.github.com/chunter-cb/bf70c53a5ab6d8361ce7f4215b776114)

## Installation

```bash
npx skills add base/skills --skill vibenet
```
