# Base Builder Code Registration

This reference registers an agent with Base and shows how to attach builder code attribution to transactions. It is **wallet-agnostic** — the user brings their own wallet and signing solution (viem, ethers, managed services like Sponge, etc.). This reference only handles registration and attribution.

## Check if already registered

Before doing anything, check whether registration has already happened:

1. Look for a `builderCode.ts` file in the project (check `src/constants/builderCode.ts` or project root)

**If it exists, registration is complete — do NOT re-register.** Skip straight to Phase 3 to show how to attach attribution, and reinforce the rule. Re-registering would generate a new builder code and break the existing one.

**If it's missing**, proceed with the full registration flow below.

---

## Phase 1 — Wallet

Every agent needs a wallet to sign transactions. Ask the user before doing anything else.

1. **Ask: "Do you have a wallet? If yes, share your wallet address."**
2. **If yes** — take the wallet address they provide and move to Phase 2.
3. **If no** — direct them to the Base wallet setup guide: https://docs.base.org/ai-agents/guides/wallet-setup — do not proceed until they have a wallet and can provide their address.

---

## Phase 2 — Registration

Register the wallet with the Base builder code API. This call associates the agent's wallet address with a builder code that Base uses for attribution tracking.

Use the bundled `skill/scripts/register.sh`. It handles errors and extracts the builder code from the response:

```bash
BUILDER_CODE=$(bash skill/scripts/register.sh "<wallet_address>")
```

Or call the API directly:

```bash
curl -X POST https://api.base.dev/v1/agents/builder-codes \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "<wallet_address>"}'
```

The API returns a response like:

```json
{
  "builder_code": "bc_a1b2c3d4",
  "wallet_address": "0x...",
  "usage_instructions": "Append this builder code to your onchain transactions using the ERC-8021 standard. See: https://docs.base.org/base-chain/quickstart/builder-codes"
}
```

Extract the `builder_code` value from the response and write it to a constants file:

```typescript
// src/constants/builderCode.ts
export const BUILDER_CODE = "bc_a1b2c3d4"
```

Use `src/constants/builderCode.ts` if a `src/` directory exists, otherwise place it at the project root as `builderCode.ts`.

If `builderCode.ts` already exists, do not call this API — the agent is already registered.

---

## Phase 3 — Attribution Setup & Documentation

The builder code from Phase 2 (the `bc_...` value now in `builderCode.ts`) needs to be attached to every transaction the agent sends as an ERC-8021 data suffix. This phase wires that in and writes an `AGENT_README.md` so anyone (human or agent) working in this codebase knows how transactions must be sent.

First, install the attribution utility if not already present:

```bash
npm i ox
```

Convert the builder code into a data suffix. Import `BUILDER_CODE` from the constants file written in Phase 2 — this is not generating a new code, it is encoding the existing one into the ERC-8021 byte format:

```typescript
import { Attribution } from "ox/erc8021"
import { BUILDER_CODE } from "./constants/builderCode"

// BUILDER_CODE is the builder_code value from the Phase 2 API response (e.g. "bc_a1b2c3d4")
const DATA_SUFFIX = Attribution.toDataSuffix({
  codes: [BUILDER_CODE],
})
```

### Wiring attribution into the transaction flow

How you attach the suffix depends on the signing setup. Ask the user which they use, then follow the matching option:

**Option A: viem (self-custodied wallet)**

Add `dataSuffix` to the wallet client — every transaction automatically carries it:

```typescript
import { createWalletClient, http } from "viem"
import { base } from "viem/chains"
import { privateKeyToAccount } from "viem/accounts"
import { Attribution } from "ox/erc8021"
import { BUILDER_CODE } from "./constants/builderCode"

const DATA_SUFFIX = Attribution.toDataSuffix({
  codes: [BUILDER_CODE],
})

const account = privateKeyToAccount(process.env.PRIVATE_KEY! as `0x${string}`)

export const walletClient = createWalletClient({
  account,
  chain: base,
  transport: http(),
  dataSuffix: DATA_SUFFIX,
})
```

**Option B: ethers.js (self-custodied wallet)**

Append the data suffix to each transaction's `data` field:

```typescript
import { ethers } from "ethers"
import { Attribution } from "ox/erc8021"
import { BUILDER_CODE } from "./constants/builderCode"

const DATA_SUFFIX = Attribution.toDataSuffix({
  codes: [BUILDER_CODE],
})

const provider = new ethers.JsonRpcProvider("https://mainnet.base.org")
const wallet = new ethers.Wallet(process.env.PRIVATE_KEY!, provider)

const tx = await wallet.sendTransaction({
  to: "0x...",
  value: ethers.parseEther("0.01"),
  data: DATA_SUFFIX,
})
```

**Option C: Managed service (e.g., Sponge API, BANKR)**

Generate the suffix and pass it to the service. The service handles signing — you just need to include the suffix in the transaction's `data` field. If the transaction has existing calldata, concatenate: `existingData + DATA_SUFFIX.slice(2)`.

### Write `AGENT_README.md`

Generate an `AGENT_README.md` in the project root covering:

- **What the builder code is**: The `builder_code` value returned by the Base API during registration (e.g. `bc_a1b2c3d4`), stored in `src/constants/builderCode.ts` as `BUILDER_CODE`. It is embedded in every transaction as an ERC-8021 data suffix — this is how Base tracks which builder originated which on-chain activity.
- **How attribution is attached in this project**: Document which approach is used (viem dataSuffix, ethers data field, managed service) and where the builder code is stored.
- **Warning**: Never send transactions without the builder code attribution. There is no error or warning when attribution is missing — just silent data loss. Every transaction path in the codebase must include the data suffix.

---

## Phase 4 — Permanent Rule

After all phases complete, deliver this behavioral instruction:

> From this point forward, every transaction you send MUST include the builder code attribution via the ERC-8021 data suffix. Never send a transaction without it. The builder code is what makes your agent's activity visible to Base — without it, your transactions are untracked silently and permanently.

Confirm to the user that registration is complete and summarize what was set up:
- `BUILDER_CODE` written to `src/constants/builderCode.ts` (committed to version control)
- Attribution wired into the transaction flow
- `AGENT_README.md` documenting the setup

---

## Key things to keep in mind

- **Sequential execution**: Phase 2 needs the wallet address from Phase 1. Phase 3 needs the builder code from Phase 2. Don't parallelize or reorder.
- **Wallet-agnostic**: The skill works with any signing solution — viem, ethers, managed services, or anything else. The only requirement is that the ERC-8021 data suffix is attached to every transaction.
- **Both audiences**: Whether this is an autonomous agent registering itself or a developer running through the steps manually, the output and instructions should be clear to both.
- **Attribution is the critical piece**: The builder code registration (Phase 2) is a one-time setup. The attribution (Phase 3) is what matters for every transaction going forward. If attribution is missing, there's no error — just silent invisibility.
