---
name: deploy-b20-token
description: >
  Deploy and operate B20 tokens on Base — Base's native ERC-20-superset precompile (roles, supply
  caps, pausing, policy gating, memos, permit). Covers setup (base-foundryup, base-std), checking
  Activation Registry status before deploying (avoids FeatureNotActivated), createB20 for
  ASSET/STABLECOIN variants including the abi.encode(struct) single-tuple encoding gotcha for
  JS/TS clients, the full roles and admin model (MINT_ROLE, BURN_ROLE, PAUSE_ROLE,
  renounceLastAdmin), the PolicyRegistry allowlist/blocklist compliance model and its
  open-by-default trap, post-deploy minting/supply-cap/memo operations, ASSET-only features
  (multiplier, announce, batchMint), metadata/permit (ERC-2612, ERC-7572), and the full custom-error
  catalog with fixes. Use when deploying, minting, configuring roles/policies on, or debugging
  errors from a B20 token.
---

# Deploy B20 Tokens on Base

Playbook for deploying and operating B20 — Base's native ERC-20-superset precompile — covering the
Foundry CLI path and the client-side (viem/wagmi) encoding path for building a UI around it.

## What B20 Is

B20 is an ERC-20 superset that runs as a **precompile**, not a deployed contract. There's no
bytecode to verify on an explorer — the logic lives at the protocol level. Two variants:

| Variant | Decimals | Identity |
|---------|----------|----------|
| `ASSET` | Configurable, 6–18 | General-purpose: in-game currencies, loyalty points, reward tokens |
| `STABLECOIN` | Fixed at 6 | Immutable self-declared ISO-style currency code (e.g. `USD`) |

## Safety Guardrails

- **Never assume a network has B20 live.** Check the Activation Registry first (see
  [references/activation-check.md](references/activation-check.md)) — attempting `createB20`
  before activation reverts with `FeatureNotActivated`, and as of writing this is true on Base
  Mainnet even though the precompile addresses already respond to calls.
- **Never hand-roll `abi.encode(struct)` as a flat parameter list in JS/TS.** Solidity wraps a
  single struct argument as one dynamic tuple (an outer offset slot + the tuple's own head/tail),
  not a flat field sequence. Getting this wrong produces calldata that looks plausible but reverts
  with `AbiDecodeFailed` or similar. See [references/encoding.md](references/encoding.md).
- **Never reuse a `salt` for the same `(variant, sender)` pair** — it deterministically derives the
  same address and reverts `TokenAlreadyExists` on the second attempt. Derive a fresh salt per
  deploy (e.g. hash of symbol + timestamp + randomness).
- **Deploying never mints.** `createB20` only creates the token and runs `initCalls` (role grants,
  supply cap). Minting is a separate `mint()` call requiring `MINT_ROLE`.
- **Use `base-forge`/`base-cast`/`base-anvil`, never vanilla `forge`/`cast`/`anvil`** — standard
  Foundry can't simulate the precompile and aborts with "call to non-contract address."
- **Don't assume a deployed token is compliance-gated just because it's B20.** Every policy scope
  defaults to `ALWAYS_ALLOW` — an unattended deployment is fully open. See
  [references/policy.md](references/policy.md).
- **`renounceLastAdmin()` is irreversible.** Walk the user through final role/policy assignments
  before suggesting it. See [references/roles-and-admin.md](references/roles-and-admin.md).

## Task Routing

| Task | When to Use | Reference |
|------|-------------|-----------|
| **Setup** | Install `base-foundryup`, add `base-std`, configure `foundry.toml` | [references/setup.md](references/setup.md) |
| **Check activation** | Verify a network's Activation Registry has B20 live before deploying | [references/activation-check.md](references/activation-check.md) |
| **Encode params (JS/TS)** | Building a wallet-signed UI (viem/wagmi) instead of a Foundry script | [references/encoding.md](references/encoding.md) |
| **Deploy** | `createB20` call, address derivation, ASSET vs STABLECOIN params, salt, Foundry script | [references/deploy.md](references/deploy.md) |
| **Roles & admin** | Role list, custom roles, `renounceLastAdmin`, admin-less behavior, pause | [references/roles-and-admin.md](references/roles-and-admin.md) |
| **Policy / compliance gating** | PolicyRegistry, allowlist/blocklist, the 4 policy scopes, defaults | [references/policy.md](references/policy.md) |
| **Mint / supply cap / memo transfers** | Post-deploy token operations | [references/post-deploy.md](references/post-deploy.md) |
| **ASSET-only features** | Multiplier/rebase, `announce()`, `batchMint`, extra metadata | [references/asset-variant.md](references/asset-variant.md) |
| **Metadata & permit** | `updateName`/`updateSymbol`, `contractURI`, ERC-2612 permit, EIP-712 | [references/metadata-and-permit.md](references/metadata-and-permit.md) |
| **Errors** | Decode a revert into what actually went wrong | [references/errors.md](references/errors.md) |

## Operating Procedure

1. **Check activation** on the target network first — don't waste a transaction finding out.
2. **Classify the task** using the table above and read the relevant reference before implementing.
3. **Confirm the path** with the user: Foundry CLI script vs a wallet-signed web UI (viem/wagmi) —
   they need different encoding helpers (Solidity vs JS).
4. **Implement** with explicit network, unique salt, and the correct param encoding for the chosen
   path.
5. **Deliver** the script/code, the exact deploy command, and a note on what `initCalls` (if any)
   will run automatically — most users expect minting to happen on deploy; it doesn't.

## For Edge Cases and Latest API Changes

- **B20 token standard**: [docs.base.org/get-started/launch-b20-token](https://docs.base.org/get-started/launch-b20-token)
- **Accepting B20 payments (memos)**: [docs.base.org/apps/guides/accept-b20-payments](https://docs.base.org/apps/guides/accept-b20-payments)
- **AI-optimized docs index**: [docs.base.org/llms.txt](https://docs.base.org/llms.txt)

## Installation

```bash
npx skills add base/skills --skill deploy-b20-token
```
