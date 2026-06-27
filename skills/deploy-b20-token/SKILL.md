---
name: deploy-b20-token
description: >
  Deploy and operate B20 tokens on Base — Base's native ERC-20-superset precompile (roles, supply
  caps, pausing, policy gating, memos, permit — no contract to write or audit). Covers: (1) Setup —
  base-foundryup, base-std library, why vanilla forge/cast/anvil fail against the precompile;
  (2) Activation check — verifying the Activation Registry has the ASSET/STABLECOIN feature live
  on a given network before attempting a deploy, avoiding FeatureNotActivated reverts;
  (3) Deploy — B20Factory.createB20, ASSET vs STABLECOIN params, the B20FactoryLib param-encoding
  gotcha (abi.encode(struct) wraps as a single dynamic tuple, not a flat field list — gets this
  wrong silently if hand-rolled in JS/TS), salt uniqueness, TokenAlreadyExists; (4) Post-deploy —
  minting (deploy alone never mints), grantRole(MINT_ROLE), supply cap math by decimals,
  transferWithMemo for payment references; (5) Common errors — FeatureNotActivated,
  AccessControlUnauthorizedAccount, SupplyCapExceeded, InsufficientBalance, PolicyForbids, and what
  each actually means.
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

## Task Routing

| Task | When to Use | Reference |
|------|-------------|-----------|
| **Setup** | Install `base-foundryup`, add `base-std`, configure `foundry.toml` | [references/setup.md](references/setup.md) |
| **Check activation** | Verify a network's Activation Registry has B20 live before deploying | [references/activation-check.md](references/activation-check.md) |
| **Encode params (JS/TS)** | Building a wallet-signed UI (viem/wagmi) instead of a Foundry script | [references/encoding.md](references/encoding.md) |
| **Deploy** | `createB20` call, ASSET vs STABLECOIN params, salt, Foundry script | [references/deploy.md](references/deploy.md) |
| **Mint / grant roles / supply cap / memo transfers** | Post-deploy operations | [references/post-deploy.md](references/post-deploy.md) |
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
