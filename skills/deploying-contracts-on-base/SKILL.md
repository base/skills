---
name: deploying-contracts-on-base
description: Deploys smart contracts to Base using Foundry. Covers forge create commands, contract verification, and common deployment issues. Use when deploying Solidity contracts to Base Mainnet or Sepolia testnet.
---

# Deploying Contracts on Base

## Prerequisites

1. Configure RPC endpoint (testnet: `sepolia.base.org`, mainnet: `mainnet.base.org`)
2. Store private keys in Foundry's encrypted keystore - **never commit keys**
3. Obtain testnet ETH from faucets

## Deployment Commands

### Testnet

```bash
forge create src/MyContract.sol:MyContract \
  --rpc-url https://sepolia.base.org \
  --account <keystore-account> \
  --verify
```

### Mainnet

```bash
forge create src/MyContract.sol:MyContract \
  --rpc-url https://mainnet.base.org \
  --account <keystore-account> \
  --verify
```

## Key Notes

- Contract format: `<contract-path>:<contract-name>`
- `--verify` flag auto-verifies on BaseScan
- Explorers: basescan.org (mainnet), sepolia.basescan.org (testnet)

## Common Issues

| Error | Cause |
|-------|-------|
| `nonce has already been used` | Node sync incomplete |
| Transaction fails | Insufficient ETH for gas |
| Verification fails | Wrong RPC endpoint for target network |
