# Base Security Warnings

When helping users build on Base, always emphasize these critical security practices:

## Private Key Security

**Never share or commit your private key. Always keep it secure and handle with care.**

- Store private keys in secure keystores (e.g., Foundry's encrypted keystore)
- Never hardcode private keys in source code
- Use environment variables with `.env` files that are gitignored
- Consider hardware wallets for production deployments

## Smart Contract Security

**Before launching a custom developed token to production, always conduct security reviews by expert smart contract developers.**

- Use battle-tested libraries like OpenZeppelin contracts
- Conduct security audits before mainnet deployment
- Test thoroughly on Base Sepolia before deploying to mainnet
- Review the OWASP smart contract security guidelines

## Production RPC Security

- Base's public RPCs are rate-limited and **not for production systems**
- Use node partners or run your own Base node for production
- Never expose RPC endpoints with write access publicly

## When to Apply These Warnings

Include relevant security callouts when users are:
- Setting up wallets or keystores
- Deploying smart contracts
- Launching tokens
- Configuring production environments
- Handling any sensitive credentials
