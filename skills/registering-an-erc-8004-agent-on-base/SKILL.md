---
name: registering-an-erc-8004-agent-on-base
description: >
  Register an AI agent on the ERC-8004 Identity Registry (Base Mainnet or Sepolia).
  Covers: (1) agent registration file — JSON shape per ERC8004SPEC.md (name, description,
  image, services, registrations, supportedTrust); (2) host the file — IPFS, HTTPS, or
  data URI; (3) register on-chain — call register() on IdentityRegistry via viem or cast,
  get agentId (ERC-721 tokenId); (4) set agent URI — point tokenURI to the hosted file;
  (5) bind agent wallet — setAgentWallet() with EIP-712 signature; (6) read-back —
  ownerOf, tokenURI, getAgentWallet to confirm registration. Use this skill for
  ERC-8004 Trustless Agents identity registration, NOT for ERC-8021 builder codes
  (use build-on-base for that). Canonical contract addresses: Base Mainnet
  0x8004A169FB4a3325136EB29fA0ceB6D2e539a432, Base Sepolia
  0x8004A818BFB912233c491871b3d84c89A494BD9e. 256,000+ agents already registered.
---

# Registering an ERC-8004 Agent on Base

Step-by-step registration flow for AI agents on the ERC-8004 Identity Registry. Each agent gets an ERC-721 NFT (the `agentId`) whose `tokenURI` points to a registration file with metadata, service endpoints, and trust declarations.

## Prerequisites

- A wallet with ETH on Base Mainnet or Base Sepolia (for gas)
- viem + a private key, **or** Foundry (`cast`) for CLI one-liners

## Contract Addresses

| Network | IdentityRegistry |
|---------|-----------------|
| **Base Mainnet** (8453) | `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432` |
| **Base Sepolia** (84532) | `0x8004A818BFB912233c491871b3d84c89A494BD9e` |

> These are vanity-address singletons — identical across all 20+ supported EVM chains. Do NOT use any other address.

## Common Mistakes (avoid these)

| Mistake | Reality |
|---------|---------|
| Treating `agentId` as a wallet address | `agentId` is an ERC-721 **tokenId** (uint256), not an address |
| Using one contract for all registries | Identity, Reputation, and Validation are **three separate contracts** |
| Using stale contract addresses | Always use the addresses above — they are verified against the [erc-8004/erc-8004-contracts](https://github.com/erc-8004/erc-8004-contracts) repo |
| Confusing ERC-8004 with ERC-8021 | ERC-8021 = builder code attribution for transactions. ERC-8004 = agent identity registry. Completely different standards. |

---

## Pre-flight — Check if Already Registered

Before doing anything, check if the agent already has a registration:

1. Look for an `erc8004.ts` or `erc8004.json` config file in the project
2. If found, read the `agentId` from it
3. Verify on-chain:

```bash
cast call 0x8004A169FB4a3325136EB29fA0ceB6D2e539a432 \
  "ownerOf(uint256)(address)" <agentId> \
  --rpc-url https://mainnet.base.org
```

**If it returns an address**, registration is complete — skip to Phase 4 (read-back) to confirm everything is wired correctly.

**If it reverts or returns address(0))**, proceed with the full flow below.

---

## Phase 1 — Agent Registration File

Build a JSON file that describes the agent. This is what `tokenURI` will point to.

### Required Fields

```json
{
  "name": "MyAgent",
  "description": "An autonomous trading agent on Base",
  "image": "https://example.com/agent-avatar.png",
  "services": [
    {
      "name": "trade",
      "endpoint": "https://api.myagent.example.com/trade",
      "description": "Execute token swaps on Base"
    }
  ],
  "registrations": [],
  "supportedTrust": ["reputation"],
  "active": true
}
```

### All Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Human-readable agent name |
| `description` | string | ✅ | What the agent does |
| `image` | string | ✅ | URL to agent avatar/logo (NFT-friendly) |
| `services` | array | ✅ | List of service endpoints the agent exposes |
| `registrations` | array | ✅ | Other registry registrations (e.g., chain-specific) |
| `supportedTrust` | array | ✅ | Trust mechanisms: `"reputation"`, `"crypto-economic"`, `"tee-attestation"` |
| `active` | boolean | ✅ | Whether the agent is currently operational |
| `x402Support` | object | ❌ | Payment capabilities if the agent accepts x402 payments |

### Service Entry Shape

```json
{
  "name": "service-name",
  "endpoint": "https://...",
  "description": "What this service does"
}
```

---

## Phase 2 — Host the Registration File

Choose one hosting method:

### Option A: IPFS (recommended — censorship-resistant)

Pin the JSON to IPFS via Pinata, Infura, or any pinning service:

```bash
# Example with Pinata CLI
pinata pin-file-to-ipfs agent-registration.json
# Returns: Qm... (CID)
```

The `agentURI` will be: `ipfs://Qm...`

### Option B: HTTPS

Upload to any web server:

```
https://yourdomain.com/.well-known/agent-registration.json
```

The `agentURI` will be: `https://yourdomain.com/.well-known/agent-registration.json`

### Option C: Data URI (simplest — no hosting needed)

Encode inline:

```bash
AGENT_URI="data:application/json;base64,$(cat agent-registration.json | base64 -w0)"
```

---

## Phase 3 — Register On-Chain

Call `register()` on the IdentityRegistry. The function returns an `agentId` (uint256).

### With viem

```typescript
import { createWalletClient, http, parseEventLogs } from "viem"
import { base } from "viem/chains"        // use baseSepolia for testnet
import { privateKeyToAccount } from "viem/accounts"

const IDENTITY_REGISTRY = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
// For Sepolia: "0x8004A818BFB912233c491871b3d84c89A494BD9e"

const account = privateKeyToAccount(process.env.PRIVATE_KEY as `0x${string}`)

const client = createWalletClient({
  account,
  chain: base,
  transport: http(),
})

// Option 1: Register with URI in one call
const hash = await client.writeContract({
  address: IDENTITY_REGISTRY,
  abi: [{
    name: "register",
    type: "function",
    inputs: [{ name: "agentURI", type: "string" }],
    outputs: [{ name: "agentId", type: "uint256" }],
  }],
  functionName: "register",
  args: [AGENT_URI], // from Phase 2
})

// Wait for receipt and extract agentId from the Registered event
const receipt = await client.waitForTransactionReceipt({ hash })
const logs = parseEventLogs({
  abi: [{
    name: "Registered",
    type: "event",
    inputs: [
      { name: "agentId", type: "uint256", indexed: true },
      { name: "agentURI", type: "string", indexed: false },
      { name: "owner", type: "address", indexed: true },
    ],
  }],
  logs: receipt.logs,
})
const agentId = logs[0].args.agentId
console.log(`Registered! agentId: ${agentId}`)
```

### With cast (one-liner)

```bash
# Register with URI
cast send 0x8004A169FB4a3325136EB29fA0ceB6D2e539a432 \
  "register(string)(uint256)" "$AGENT_URI" \
  --rpc-url https://mainnet.base.org \
  --private-key $PRIVATE_KEY

# Parse agentId from the Registered event in the receipt
# Or call ownerOf with incremented token counter
```

### Register Without URI (set it later)

```bash
# Just register to get an agentId, set URI later
cast send 0x8004A169FB4a3325136EB29fA0ceB6D2e539a432 \
  "register()(uint256)" \
  --rpc-url https://mainnet.base.org \
  --private-key $PRIVATE_KEY
```

---

## Phase 4 — Set Agent URI (if not set in Phase 3)

If you registered without a URI:

```typescript
await client.writeContract({
  address: IDENTITY_REGISTRY,
  abi: [{
    name: "setAgentURI",
    type: "function",
    inputs: [
      { name: "agentId", type: "uint256" },
      { name: "newURI", type: "string" },
    ],
    outputs: [],
  }],
  functionName: "setAgentURI",
  args: [agentId, AGENT_URI],
})
```

```bash
cast send 0x8004A169FB4a3325136EB29fA0ceB6D2e539a432 \
  "setAgentURI(uint256,string)" $AGENT_ID "$AGENT_URI" \
  --rpc-url https://mainnet.base.org \
  --private-key $PRIVATE_KEY
```

---

## Phase 5 — Bind Agent Wallet (Optional)

If the agent operates from a different wallet than the NFT owner, bind it via `setAgentWallet()`. This requires an EIP-712 signature from the NFT owner.

### When to use

- NFT owner is a multisig or cold wallet
- Agent runs from a separate hot wallet for operational security
- You want to delegate management without transferring the NFT

### With viem

```typescript
import { signTypedData } from "viem/actions"

// Get EIP-712 domain from the contract
const domain = await client.readContract({
  address: IDENTITY_REGISTRY,
  abi: [{ name: "eip712Domain", type: "function", inputs: [], outputs: [
    { name: "fields", type: "bytes1" },
    { name: "name", type: "string" },
    { name: "version", type: "string" },
    { name: "chainId", type: "uint256" },
    { name: "verifyingContract", type: "address" },
    { name: "salt", type: "bytes32" },
    { name: "extensions", type: "uint256[]" },
  ] }],
  functionName: "eip712Domain",
})

const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600) // 1 hour

const signature = await signTypedData(client, {
  domain: {
    name: domain[1],
    version: domain[2],
    chainId: domain[3],
    verifyingContract: IDENTITY_REGISTRY,
  },
  types: {
    SetAgentWallet: [
      { name: "agentId", type: "uint256" },
      { name: "newWallet", type: "address" },
      { name: "deadline", type: "uint256" },
    ],
  },
  primaryType: "SetAgentWallet",
  message: {
    agentId,
    newWallet: "0xNEW_WALLET_ADDRESS",
    deadline,
  },
})

// Submit the signed message
await client.writeContract({
  address: IDENTITY_REGISTRY,
  abi: [{
    name: "setAgentWallet",
    type: "function",
    inputs: [
      { name: "agentId", type: "uint256" },
      { name: "newWallet", type: "address" },
      { name: "deadline", type: "uint256" },
      { name: "signature", type: "bytes" },
    ],
  }],
  functionName: "setAgentWallet",
  args: [agentId, "0xNEW_WALLET_ADDRESS", deadline, signature],
})
```

---

## Read-Back — Verify Registration

Always confirm after registering:

```bash
# Who owns this agent?
cast call 0x8004A169FB4a3325136EB29fA0ceB6D2e539a432 \
  "ownerOf(uint256)(address)" $AGENT_ID \
  --rpc-url https://mainnet.base.org

# What URI is set?
cast call 0x8004A169FB4a3325136EB29fA0ceB6D2e539a432 \
  "tokenURI(uint256)(string)" $AGENT_ID \
  --rpc-url https://mainnet.base.org

# Is there a bound agent wallet?
cast call 0x8004A169FB4a3325136EB29fA0ceB6D2e539a432 \
  "getAgentWallet(uint256)(address)" $AGENT_ID \
  --rpc-url https://mainnet.base.org

# Get contract version
cast call 0x8004A169FB4a3325136EB29fA0ceB6D2e539a432 \
  "getVersion()(string)" \
  --rpc-url https://mainnet.base.org
```

---

## Save Config

After successful registration, save the agent identity to the project:

```typescript
// src/constants/erc8004.ts
export const ERC8004_AGENT_ID = 12345n // your agentId
export const ERC8004_IDENTITY_REGISTRY = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432" as const
export const ERC8004_CHAIN_ID = 8453 // Base Mainnet
```

```json
// erc8004.json (project root)
{
  "agentId": 12345,
  "chainId": 8453,
  "identityRegistry": "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432",
  "agentURI": "ipfs://Qm...",
  "owner": "0x...",
  "agentWallet": "0x...",
  "registeredAt": "2026-05-31T12:00:00Z"
}
```

---

## Agent Identifier Format

The canonical agent identifier in the ERC-8004 ecosystem is:

```
{namespace}:{chainId}:{identityRegistry}:{tokenId}
```

Example: `eip155:8453:0x8004A169FB4a3325136EB29fA0ceB6D2e539a432:12345`

Use this format when referencing the agent in cross-chain or cross-protocol contexts.

---

## Out of Scope

- **Reputation Registry** (`0x8004BAa17C55a88189AE136b182e5fdA19dE9b63` mainnet) — reserved for a sibling skill
- **Validation Registry** — spec authors flag it as under active revision with the TEE community
- **x402 payment integration** — cross-reference only; see agentkit docs for payment flows

---

## Resources

- [ERC-8004 EIP](https://eips.ethereum.org/EIPS/eip-8004)
- [erc-8004/erc-8004-contracts](https://github.com/erc-8004/erc-8004-contracts) — source code + ABIs
- [8004.org](https://www.8004.org) — ecosystem site
- [ERC8004SPEC.md](https://github.com/erc-8004/erc-8004-contracts/blob/main/ERC8004SPEC.md) — canonical spec
