---
name: registering-an-erc-8004-agent-on-base
description: "Invoke this skill when an agent or developer needs to register an ERC-8004 agent identity on Base. This skill contains the canonical IdentityRegistry addresses for Base Mainnet and Sepolia that LLM training data frequently gets wrong — you MUST load it to register correctly. Covers register(), setAgentURI(), setAgentWallet(), the registration file schema, and read-back verification. Use when building agent identity, setting up agentId, publishing agentURI, binding agentWallet, or reading agent data on Base Mainnet (chainId 8453) or Base Sepolia (chainId 84532). Covers phrases like 'register ERC-8004 agent', 'agent identity on Base', 'agentId', 'agentURI', 'identity registry', 'trustless agent', 'agent registration file', or 'ERC-8004'."
---

# ERC-8004 Agent Registration

[ERC-8004](https://eips.ethereum.org/EIPS/eip-8004) defines three on-chain registries for autonomous agents: **Identity**, **Reputation**, and **Validation**. This skill covers **Identity only**. Each registered agent receives an ERC-721 `agentId` and an optional `agentURI` pointing to a registration file.

## Canonical Addresses (Base)

| Network | IdentityRegistry | Chain ID |
|---------|-----------------|----------|
| Base Mainnet | `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432` | 8453 |
| Base Sepolia | `0x8004A818BFB912233c491871b3d84c89A494BD9e` | 84532 |

Same vanity addresses on every supported chain. Always use these — do not guess or use any other address.

## Pre-flight: Check for Existing Registration

Before registering, check whether the owner already has an agent:

```bash
cast call <IDENTITY_REGISTRY> "balanceOf(address)(uint256)" <OWNER_ADDRESS> \
  --rpc-url https://sepolia.base.org
```

If the result is `> 0`, the owner already has registered agents. Ask for the existing `agentId` before proceeding — do not register a duplicate unless intentional.

## Phase 1 — Build the Registration File

The `agentURI` must resolve to a JSON document with this structure (source: `ERC8004SPEC.md`):

```json
{
  "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
  "name": "MyAgent",
  "description": "What the agent does, how to interact with it, pricing if applicable",
  "image": "https://example.com/agent.png",
  "services": [
    { "name": "A2A",  "endpoint": "https://agent.example/.well-known/agent-card.json", "version": "0.3.0" },
    { "name": "MCP",  "endpoint": "https://mcp.agent.example/", "version": "2025-06-18" }
  ],
  "x402Support": false,
  "active": true,
  "registrations": [
    {
      "agentId": 42,
      "agentRegistry": "eip155:84532:0x8004A818BFB912233c491871b3d84c89A494BD9e"
    }
  ],
  "supportedTrust": ["reputation"]
}
```

`agentRegistry` format: `eip155:{chainId}:{identityRegistryAddress}`. Use `8453` for Mainnet, `84532` for Sepolia.

If the `agentId` is not known yet (registering with no URI first), use `0` as a placeholder and update with `setAgentURI()` after minting.

## Phase 2 — Host the Registration File

| Option | URI format | When to use |
|--------|-----------|-------------|
| IPFS | `ipfs://{cid}` | Production — immutable, content-addressed |
| HTTPS | `https://example.com/agent.json` | Simple; requires keeping the endpoint live |
| On-chain | `data:application/json;base64,{base64}` | Maximum censorship-resistance; higher gas |

To encode on-chain:
```bash
echo '{"type":"https://eips.ethereum.org/EIPS/eip-8004#registration-v1",...}' \
  | base64 -w0 | xargs -I{} echo "data:application/json;base64,{}"
```

## Phase 3 — Register On-Chain

### viem (TypeScript)

```typescript
import { createWalletClient, createPublicClient, http, parseAbi } from "viem";
import { baseSepolia } from "viem/chains"; // use `base` for Mainnet
import { privateKeyToAccount } from "viem/accounts";

const IDENTITY_REGISTRY = "0x8004A818BFB912233c491871b3d84c89A494BD9e";
const abi = parseAbi([
  "function register() returns (uint256 agentId)",
  "function register(string agentURI) returns (uint256 agentId)",
  "function setAgentURI(uint256 agentId, string newURI) external",
  "function ownerOf(uint256 tokenId) view returns (address)",
  "function tokenURI(uint256 tokenId) view returns (string)",
  "function getAgentWallet(uint256 agentId) view returns (address)",
]);

const account = privateKeyToAccount(process.env.PRIVATE_KEY as `0x${string}`);
const client  = createWalletClient({ account, chain: baseSepolia, transport: http() });

// Option A: register with URI in one step
const hash = await client.writeContract({
  address: IDENTITY_REGISTRY, abi,
  functionName: "register",
  args: ["ipfs://your-cid"],
});

// Option B: register first, set URI after (use when agentId must appear in the file)
const hash2   = await client.writeContract({ address: IDENTITY_REGISTRY, abi, functionName: "register", args: [] });
// ... get agentId from Registered event, build file with real agentId, then:
await client.writeContract({ address: IDENTITY_REGISTRY, abi, functionName: "setAgentURI", args: [agentId, "ipfs://final-cid"] });
```

> **Note**: `register(agentURI, metadata[])` accepts extra on-chain metadata. Do **not** pass `agentWallet` in the metadata array — it is reserved and the call will revert.

### cast (Foundry)

```bash
# Sepolia
cast send 0x8004A818BFB912233c491871b3d84c89A494BD9e \
  "register(string)(uint256)" "ipfs://your-cid" \
  --rpc-url https://sepolia.base.org --private-key $PRIVATE_KEY

# Mainnet
cast send 0x8004A169FB4a3325136EB29fA0ceB6D2e539a432 \
  "register(string)(uint256)" "ipfs://your-cid" \
  --rpc-url https://mainnet.base.org --private-key $PRIVATE_KEY
```

The returned value is the `agentId`. Store it — every subsequent call requires it.

## Phase 4 (Optional) — Bind agentWallet

`agentWallet` is set automatically to the owner's address on `register()`. To change it, `newWallet` must sign an EIP-712 message. The **caller** must be the agent owner or operator; the **signature** must come from `newWallet`.

```typescript
import { signTypedData } from "viem/accounts";

const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);

const signature = await signTypedData({
  privateKey: newWalletPrivateKey,
  domain: {
    name: "ERC8004IdentityRegistry",
    version: "1",
    chainId: 84532,                                           // 8453 for Mainnet
    verifyingContract: IDENTITY_REGISTRY,
  },
  types: {
    AgentWalletSet: [
      { name: "agentId",   type: "uint256" },
      { name: "newWallet", type: "address" },
      { name: "owner",     type: "address" },                // current agent owner
      { name: "deadline",  type: "uint256" },
    ],
  },
  primaryType: "AgentWalletSet",
  message: { agentId: BigInt(agentId), newWallet, owner: agentOwnerAddress, deadline },
});

await client.writeContract({
  address: IDENTITY_REGISTRY,
  abi: parseAbi(["function setAgentWallet(uint256,address,uint256,bytes) external"]),
  functionName: "setAgentWallet",
  args: [BigInt(agentId), newWallet, deadline, signature],
});
```

For ERC-1271 smart wallets, `isValidSignature` is called on `newWallet` instead of ECDSA recovery — no code change needed, the contract handles both. On transfer, `agentWallet` is automatically cleared and must be re-set by the new owner.

## Read-back

```typescript
const owner  = await publicClient.readContract({ address: IDENTITY_REGISTRY, abi, functionName: "ownerOf",        args: [agentId] });
const uri    = await publicClient.readContract({ address: IDENTITY_REGISTRY, abi, functionName: "tokenURI",       args: [agentId] });
const wallet = await publicClient.readContract({ address: IDENTITY_REGISTRY, abi, functionName: "getAgentWallet", args: [agentId] });
```

Explorers: [basescan.org](https://basescan.org) (Mainnet) · [sepolia.basescan.org](https://sepolia.basescan.org) (Sepolia)

## Key Facts

- `agentId` is the ERC-721 `tokenId` — an auto-incremented integer, **not** a wallet address
- `agentRegistry` identifier: `eip155:{chainId}:{identityRegistryAddress}`
- An agent can be registered on multiple chains simultaneously
- Contract version: 2.0.0 — token name "AgentIdentity"

## Out of Scope

- **Reputation Registry** — stable, reserved for a sibling skill
- **Validation Registry** — spec authors flag it as under active TEE community revision
- **x402 payment integration** — see [ERC-8004 spec](https://eips.ethereum.org/EIPS/eip-8004) for examples

## References

- [ERC-8004 Specification](https://eips.ethereum.org/EIPS/eip-8004)
- [erc-8004/erc-8004-contracts](https://github.com/erc-8004/erc-8004-contracts)
- [8004.org/build](https://www.8004.org/build)
- [Base Docs](https://docs.base.org)
