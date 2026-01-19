# Dependency Changes

How to update package.json when converting from MiniKit to Farcaster SDK.

## Quick Migration Command

Run this single command to uninstall MiniKit and install all Farcaster SDK dependencies:

```bash
npm uninstall @coinbase/onchainkit && npm install @farcaster/miniapp-sdk @farcaster/miniapp-wagmi-connector wagmi viem @tanstack/react-query
```

Or with yarn:
```bash
yarn remove @coinbase/onchainkit && yarn add @farcaster/miniapp-sdk @farcaster/miniapp-wagmi-connector wagmi viem @tanstack/react-query
```

Or with pnpm:
```bash
pnpm remove @coinbase/onchainkit && pnpm add @farcaster/miniapp-sdk @farcaster/miniapp-wagmi-connector wagmi viem @tanstack/react-query
```

## What Each Package Does

| Package | Purpose |
|---------|---------|
| `@farcaster/miniapp-sdk` | Core SDK for Farcaster actions (ready, composeCast, etc.) |
| `@farcaster/miniapp-wagmi-connector` | Wagmi connector for Farcaster wallet |
| `wagmi` | React hooks for Ethereum |
| `viem` | TypeScript Ethereum library (wagmi peer dep) |
| `@tanstack/react-query` | Async state management (wagmi peer dep) |

## Step-by-Step

### Step 1: Uninstall OnchainKit

```bash
npm uninstall @coinbase/onchainkit
```

### Step 2: Install Farcaster SDK

```bash
npm install @farcaster/miniapp-sdk
```

### Step 3: Install Wagmi Stack

```bash
npm install @farcaster/miniapp-wagmi-connector wagmi viem @tanstack/react-query
```

## package.json Diff

### Before (OnchainKit)
```json
{
  "dependencies": {
    "@coinbase/onchainkit": "^0.35.0",
    "next": "14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0"
  }
}
```

### After (Farcaster SDK)
```json
{
  "dependencies": {
    "@farcaster/miniapp-sdk": "^0.3.0",
    "@farcaster/miniapp-wagmi-connector": "^0.0.15",
    "@tanstack/react-query": "^5.50.0",
    "next": "14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "viem": "^2.17.0",
    "wagmi": "^2.12.0"
  }
}
```

## Version Compatibility

| Package | Minimum Version | Notes |
|---------|----------------|-------|
| `@farcaster/miniapp-sdk` | `0.3.0` | Latest stable |
| `react` | `18.0.0` | Hooks support |
| `next` | `13.0.0` | App router support |
| `node` | `22.11.0` | Required by SDK |

## Node.js Version

The Farcaster SDK requires Node.js 22.11.0 or higher:

```bash
# Check your version
node --version

# Update if needed (using nvm)
nvm install 22
nvm use 22
```

Update your `package.json` engines field:

```json
{
  "engines": {
    "node": ">=22.11.0"
  }
}
```

## TypeScript Types

The Farcaster SDK includes TypeScript types. Import them as needed:

```typescript
import { 
  sdk,
  type MiniAppContext,
  type MiniAppUser,
  type SafeAreaInsets
} from '@farcaster/miniapp-sdk';
```

## CDN Alternative

If not using a bundler, you can use the SDK via CDN:

```html
<script type="module">
  import { sdk } from 'https://esm.sh/@farcaster/miniapp-sdk';
  
  await sdk.actions.ready();
</script>
```

Or the UMD build:

```html
<script src="https://cdn.jsdelivr.net/npm/@farcaster/miniapp-sdk/dist/index.min.js"></script>
<script>
  miniapp.sdk.actions.ready();
</script>
```

## Install Command Summary

```bash
# Full migration
npm uninstall @coinbase/onchainkit
npm install @farcaster/miniapp-sdk

# With wallet support
npm install @farcaster/frame-wagmi-connector wagmi viem @tanstack/react-query
```
