# Verifying Contracts on Base

## Critical: Basescan V1 API is Deactivated

The V1 endpoint (`api.basescan.org/api`, `api-sepolia.basescan.org/api`) was **permanently deactivated on August 15, 2025**. Using it returns:

    You are using a deprecated V1 endpoint, switch to Etherscan API V2
    using https://docs.etherscan.io/v2-migration

Use the **Etherscan V2 unified endpoint** instead:

| | V1 (deprecated) | V2 (correct) |
|---|---|---|
| Mainnet | `https://api.basescan.org/api` | `https://api.etherscan.io/v2/api?chainid=8453` |
| Sepolia | `https://api-sepolia.basescan.org/api` | `https://api.etherscan.io/v2/api?chainid=84532` |
| API Key | Per-chain Basescan key | Single Etherscan key |

## Prerequisites

- Deployed contract address
- Contract source code (must match deployed bytecode exactly)
- Etherscan API key (free account at etherscan.io/apidashboard)

## Foundry

### Basic verification

    # Mainnet
    forge verify-contract <contract-address> src/MyContract.sol:MyContract \
      --verifier-url "https://api.etherscan.io/v2/api?chainid=8453" \
      --etherscan-api-key $ETHERSCAN_API_KEY \
      --watch

    # Sepolia
    forge verify-contract <contract-address> src/MyContract.sol:MyContract \
      --verifier-url "https://api.etherscan.io/v2/api?chainid=84532" \
      --etherscan-api-key $ETHERSCAN_API_KEY \
      --watch

### With constructor arguments

    forge verify-contract <contract-address> src/MyContract.sol:MyContract \
      --verifier-url "https://api.etherscan.io/v2/api?chainid=8453" \
      --etherscan-api-key $ETHERSCAN_API_KEY \
      --constructor-args $(cast abi-encode "constructor(address,uint256)" 0xabc... 100) \
      --watch

### foundry.toml V2 config

    [etherscan]
    base = { key = "${ETHERSCAN_API_KEY}", url = "https://api.etherscan.io/v2/api?chainid=8453" }
    base-sepolia = { key = "${ETHERSCAN_API_KEY}", url = "https://api.etherscan.io/v2/api?chainid=84532" }

### Already verified

If the contract is already verified, forge exits cleanly with `Contract source code already verified`. This is not an error.

## Hardhat

### hardhat.config.ts

    import { HardhatUserConfig } from "hardhat/config";
    import "@nomicfoundation/hardhat-verify";

    const config: HardhatUserConfig = {
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
            network: "base-sepolia",
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

### Verify command

    npx hardhat verify --network base <contract-address>
    npx hardhat verify --network base-sepolia <contract-address> <constructor-arg>

## Sourcify — no API key required

    # Mainnet
    forge verify-contract <contract-address> src/MyContract.sol:MyContract \
      --verifier sourcify --chain 8453 --watch

    # Sepolia
    forge verify-contract <contract-address> src/MyContract.sol:MyContract \
      --verifier sourcify --chain 84532 --watch

Check status at sourcify.dev/#/lookup

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `deprecated V1 endpoint` | Using api.basescan.org | Switch to api.etherscan.io/v2/api?chainid=8453 |
| `Invalid API key` | Using Basescan key with V2 | Create Etherscan key at etherscan.io |
| `Bytecode does not match` | Source or compiler mismatch | Match foundry.toml optimizer settings exactly |
| `Already verified` | Already on BaseScan | Not an error |
| `Missing constructor args` | Constructor takes arguments | Add --constructor-args flag |

## Cross-reference

For deployment before verification, see deploy-contracts.md.
