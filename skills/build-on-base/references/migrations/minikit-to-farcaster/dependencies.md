# Dependencies

## Requirements

- Node.js 22.11.0+
- Farcaster SDK 0.2.0+ (breaking changes from 0.1.x)

## Quick Install

```bash
npm uninstall @coinbase/onchainkit && \
npm install @farcaster/miniapp-sdk @farcaster/miniapp-wagmi-connector wagmi viem @tanstack/react-query
```

## package.json

```json
{
  "engines": { "node": ">=22.11.0" },
  "dependencies": {
    "@farcaster/miniapp-sdk": "^0.3.0",
    "@farcaster/miniapp-wagmi-connector": "^0.0.15",
    "@tanstack/react-query": "^5.50.0",
    "viem": "^2.17.0",
    "wagmi": "^2.12.0"
  }
}
```

## Check Version

```bash
npm list @farcaster/miniapp-sdk
```

## Common Errors

**Peer dependency conflict:**
```bash
npm install @farcaster/miniapp-sdk@^0.3.0 @farcaster/miniapp-wagmi-connector@^0.0.15
```

**Node.js too old:**
```bash
nvm install 22 && nvm use 22
```

## Optional: Server Auth

```bash
npm install @farcaster/quick-auth
```

See [AUTH.md](AUTH.md) for server-side token verification.
