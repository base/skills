---
name: verifying-contracts-on-basescan
description: Verifies smart contracts on Base Mainnet and Base Sepolia using the unified Etherscan V2 API (chainid 8453/84532). Use when verifying deployed contracts, configuring etherscan API keys, or troubleshooting verification failures across Foundry, Hardhat, and Basescan UI. Covers phrases like "verify contract on Base", "basescan verification", "forge verify-contract", "etherscan API key Base", "contract not verified", "hardhat verify Base", "sourcify verification", "bytecode mismatch", "constructor args verification", "proxy contract verification", or "already verified".
---

# Verifying Contracts on Basescan

## Critical: Etherscan V2 API (V1 was sunset August 15, 2025)

The Basescan V1 API (`api.basescan.org/api`) was fully deactivated on **August 15, 2025**. Always use the unified Etherscan V2 API.

| | V1 (deprecated — do not use) | V2 (current) |
|---|---|---|
| Mainnet endpoint | `https://api.basescan.org/api` | `https://api.etherscan.io/v2/api?chainid=8453` |
| Sepolia endpoint | `https://api-sepolia.basescan.org/api` | `https://api.etherscan.io/v2/api?chainid=84532` |
| API key source | basescan.org | etherscan.io (one key for all chains) |

Typical V1 error: `"You are using a deprecated V1 endpoint, switch to Etherscan API V2"`

## Prerequisites

1. Get an API key at [etherscan.io/apidashboard](https://etherscan.io/apidashboard) — a free account covers all chains including Base
2. Export it:

```bash
export ETHERSCAN_API_KEY=your_etherscan_api_key
```

3. Note the deployed contract address and the exact compiler/optimizer settings used at deploy time

## Security

- **Never commit API keys** — use environment variables or `foundry.toml` with `${ENV_VAR}` references
- **Never expose `.env` files** — add `.env` to `.gitignore`
- **Match deployment settings exactly** — compiler version, optimizer runs, and EVM version must match the original deployment; mismatches cause bytecode verification failures

## Foundry

### Verify an already-deployed contract

**Mainnet (chainid 8453):**

```bash
forge verify-contract \
  --chain 8453 \
  --etherscan-api-key $ETHERSCAN_API_KEY \
  --verifier-url "https://api.etherscan.io/v2/api?chainid=8453" \
  <deployed-address> \
  src/MyContract.sol:MyContract
```

**Sepolia (chainid 84532):**

```bash
forge verify-contract \
  --chain 84532 \
  --etherscan-api-key $ETHERSCAN_API_KEY \
  --verifier-url "https://api.etherscan.io/v2/api?chainid=84532" \
  <deployed-address> \
  src/MyContract.sol:MyContract
```

Add `--watch` to poll until verification completes:

```bash
forge verify-contract ... --watch
```

### Constructor arguments

Encode with `cast abi-encode`, then pass the result to `--constructor-args`:

```bash
ARGS=$(cast abi-encode "constructor(uint256,address)" 1000 0xYourAddress)

forge verify-contract \
  --chain 8453 \
  --etherscan-api-key $ETHERSCAN_API_KEY \
  --verifier-url "https://api.etherscan.io/v2/api?chainid=8453" \
  --constructor-args $ARGS \
  <deployed-address> \
  src/MyContract.sol:MyContract
```

### Deploy and verify in one step

For `forge create --verify` and `forge script --verify`, see [Deploying Contracts on Base](../deploying-contracts-on-base/SKILL.md). Configure `foundry.toml` to use the V2 endpoint instead of the deprecated per-chain basescan URLs:

```toml
[etherscan]
base = { key = "${ETHERSCAN_API_KEY}", chain = 8453, url = "https://api.etherscan.io/v2/api?chainid=8453" }
base-sepolia = { key = "${ETHERSCAN_API_KEY}", chain = 84532, url = "https://api.etherscan.io/v2/api?chainid=84532" }
```

### Linked libraries

Verify the library first, then verify the contract with `--libraries`:

```bash
forge verify-contract \
  --chain 8453 \
  --etherscan-api-key $ETHERSCAN_API_KEY \
  --verifier-url "https://api.etherscan.io/v2/api?chainid=8453" \
  --libraries src/lib/MyLib.sol:MyLib:<lib-deployed-address> \
  <deployed-address> \
  src/MyContract.sol:MyContract
```

## Hardhat

Install the plugin:

```bash
npm install --save-dev @nomicfoundation/hardhat-verify
```

Configure `hardhat.config.ts`. Use `apiKey` as a **single string** — not an object keyed by network, which is the deprecated V1 pattern that breaks with V2:

```typescript
import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-verify";

const config: HardhatUserConfig = {
  networks: {
    base: {
      url: "https://mainnet.base.org",
      chainId: 8453,
    },
    baseSepolia: {
      url: "https://sepolia.base.org",
      chainId: 84532,
    },
  },
  etherscan: {
    apiKey: process.env.ETHERSCAN_API_KEY as string,
    customChains: [
      {
        network: "base",
        chainId: 8453,
        urls: {
          apiURL: "https://api.etherscan.io/v2/api?chainid=8453",
          browserURL: "https://basescan.org",
        },
      },
      {
        network: "baseSepolia",
        chainId: 84532,
        urls: {
          apiURL: "https://api.etherscan.io/v2/api?chainid=84532",
          browserURL: "https://sepolia.basescan.org",
        },
      },
    ],
  },
};

export default config;
```

Verify:

```bash
# No constructor args
npx hardhat verify --network base <deployed-address>

# With constructor args (pass values directly)
npx hardhat verify --network base <deployed-address> "arg1" "arg2"

# Sepolia
npx hardhat verify --network baseSepolia <deployed-address>
```

## Manual UI Verification (basescan.org)

Use when tooling is unavailable, the contract was deployed without `--verify`, or for a quick single-file contract.

1. Open [basescan.org](https://basescan.org) (Mainnet) or [sepolia.basescan.org](https://sepolia.basescan.org) (Sepolia)
2. Search the contract address → **Contract** tab → **Verify and Publish**
3. Choose compiler type:
   - **Solidity (Single file)**: flatten first with `forge flatten src/MyContract.sol > flat.sol`
   - **Solidity (Standard JSON input)**: use the `input` field from the compilation artifact — most reliable for multi-file contracts and imports
4. Match compiler version and optimizer settings exactly to the deployment
5. Enter ABI-encoded constructor arguments if the contract constructor takes parameters

## Sourcify (Decentralized Alternative)

[Sourcify](https://sourcify.dev) verifies against IPFS-stored metadata with no centralized API key. Basescan displays a separate badge for Sourcify-verified contracts.

```bash
forge verify-contract \
  --chain 8453 \
  --verifier sourcify \
  <deployed-address> \
  src/MyContract.sol:MyContract
```

For Sepolia, replace `--chain 8453` with `--chain 84532`. No `--etherscan-api-key` required.

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `deprecated V1 endpoint` | Using `api.basescan.org/api` | Add `--verifier-url "https://api.etherscan.io/v2/api?chainid=8453"` or update `foundry.toml` |
| `Invalid API Key` | Wrong key or key from basescan.org only | Use an Etherscan key from etherscan.io |
| `Missing or invalid chainid` | V2 endpoint called without `chainid` param | Include `?chainid=8453` or `?chainid=84532` in the verifier URL |
| `Bytecode does not match` | Compiler version, optimizer runs, or EVM version differs from deployment | Re-verify with exact original settings; inspect `foundry.toml` or Hardhat config |
| `Constructor arguments not matching` | Args absent or incorrectly encoded | Re-encode with `cast abi-encode "constructor(...)" ...` |
| `already verified. Skipping verification` | Contract is already verified | Not an error — Foundry skips automatically; check Basescan to confirm source is visible |
| Library not linked | Linked library not verified or wrong address | Verify the library first, then re-run with `--libraries` |
| Proxy shows unverified implementation | Implementation contract not marked as proxy | Verify the implementation address, then use the "Is this a Proxy?" button on Basescan |

## References

- [Etherscan V2 Migration Guide](https://docs.etherscan.io/v2-migration)
- [Etherscan V2 Supported Chains](https://docs.etherscan.io/etherscan-v2/getting-started/supported-chains)
- [Foundry — forge verify-contract](https://book.getfoundry.sh/reference/forge/forge-verify-contract)
- [Foundry — Deploying and Verifying](https://book.getfoundry.sh/forge/deploying)
- [Hardhat Verify Plugin](https://hardhat.org/hardhat-runner/plugins/nomicfoundation-hardhat-verify)
- [Base Docs — Block Explorers](https://docs.base.org/docs/tools/block-explorers)
