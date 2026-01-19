# Base Smart Contract Deployment Guide

Guide users through deploying smart contracts on Base using Foundry.

## Prerequisites

1. **Node Connection**: Configure RPC endpoint
   - Testnet: `https://sepolia.base.org`
   - Mainnet: `https://mainnet.base.org`

2. **Private Key Security**:
   - **Never share or commit your private key. Always keep it secure and handle with care.**
   - Use Foundry's encrypted keystore for secure storage

3. **Test ETH**: Obtain Base Sepolia ETH from faucets for testing

## Deployment Commands

### Deploy to Base Sepolia (Testnet)

```bash
forge create src/MyContract.sol:MyContract \
  --rpc-url https://sepolia.base.org \
  --account <keystore-account> \
  --verify
```

### Deploy to Base Mainnet

```bash
forge create src/MyContract.sol:MyContract \
  --rpc-url https://mainnet.base.org \
  --account <keystore-account> \
  --verify
```

**Note:** The `--verify` flag automatically verifies your contract on BaseScan, making it easier for users to interact with your contract.

## Contract Path Format

**Note:** The format of the contract being deployed is `<contract-path>:<contract-name>`.

## Verification

After deployment, verify on the appropriate explorer:
- Testnet: https://sepolia.basescan.org
- Mainnet: https://basescan.org

## Success Indicator

**Congratulations!** When you see the deployment transaction hash and contract address, your smart contract has been successfully deployed to Base.

## Common Issues

- "nonce has already been used" error indicates sync hasn't completed if using your own node
- Ensure sufficient ETH for gas fees
- Verify RPC endpoint is correct for target network
