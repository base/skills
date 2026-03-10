# Provider Migration: OnchainKitProvider to WagmiProvider

Replace `OnchainKitProvider` from `@coinbase/onchainkit` with direct `WagmiProvider` + `QueryClientProvider` setup.

## What OnchainKitProvider Does Internally

OnchainKitProvider is a wrapper that:
1. Creates a wagmi config with `base` + `baseSepolia` chains
2. Uses `cookieStorage` for persistence and `ssr: true`
3. Default connector: `baseAccount()` from `wagmi/connectors`
4. Sets up CDP RPC URLs if `apiKey` is provided
5. Creates a default `QueryClient` from `@tanstack/react-query`
6. Applies theme/appearance settings via CSS custom properties

The provider detects if `WagmiProvider` or `QueryClientProvider` already exist in the React tree and skips creating them if so.

## Prerequisites

Ensure these packages are installed. They are likely already present since OnchainKit depends on them:

```bash
npm install wagmi viem @tanstack/react-query
```

If the project uses Tailwind CSS and it's not yet installed:

```bash
npm install tailwindcss @tailwindcss/postcss postcss
```

## Step-by-Step Migration

### 1. Create wagmi-config.ts

Create a new file for the wagmi configuration. Place it alongside the existing provider file (typically `app/wagmi-config.ts`).

```typescript
import { http, cookieStorage, createConfig, createStorage } from "wagmi";
import { base } from "wagmi/chains";
import { coinbaseWallet, metaMask } from "wagmi/connectors";

export const wagmiConfig = createConfig({
  chains: [base],
  connectors: [
    coinbaseWallet({ appName: "My App", preference: "all" }),
    metaMask(),
  ],
  storage: createStorage({ storage: cookieStorage }),
  ssr: true,
  transports: {
    [base.id]: http(),
  },
});
```

**Adapt based on the existing OnchainKitProvider config:**
- If `chain` prop was set to something other than `base`, use that chain instead
- If `apiKey` was set, you can use CDP RPC URLs: `http(\`https://api.developer.coinbase.com/rpc/v1/base/${apiKey}\`)`
- If `config.wallet.preference` was `"smartWalletOnly"`, adjust the coinbaseWallet connector accordingly
- Add additional chains to the `chains` array and `transports` object as needed

### 2. Rewrite the Provider Component

Replace the existing provider file (typically `rootProvider.tsx` or `providers.tsx`).

**Before (OnchainKit):**
```typescript
"use client";
import { ReactNode } from "react";
import { base } from "wagmi/chains";
import { OnchainKitProvider } from "@coinbase/onchainkit";
import "@coinbase/onchainkit/styles.css";

export function RootProvider({ children }: { children: ReactNode }) {
  return (
    <OnchainKitProvider
      apiKey={process.env.NEXT_PUBLIC_ONCHAINKIT_API_KEY}
      chain={base}
      config={{
        appearance: { mode: "auto" },
        wallet: { display: "modal", preference: "all" },
      }}
    >
      {children}
    </OnchainKitProvider>
  );
}
```

**After (wagmi/viem):**
```typescript
"use client";
import { type ReactNode, useState } from "react";
import { WagmiProvider } from "wagmi";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { wagmiConfig } from "./wagmi-config";

export function RootProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <WagmiProvider config={wagmiConfig}>
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    </WagmiProvider>
  );
}
```

Key changes:
- Remove `@coinbase/onchainkit` import
- Remove `@coinbase/onchainkit/styles.css` import
- `QueryClient` is created with `useState` to avoid re-creation on re-renders
- `WagmiProvider` must wrap `QueryClientProvider`

### 3. Update Layout File

Remove any OnchainKit-specific imports from the layout:

- Remove `SafeArea` from `@coinbase/onchainkit/minikit`
- Remove `minikitConfig` imports
- Remove MiniKit-related metadata generation
- Move `<RootProvider>` inside `<body>` (wagmi provider must be a client component, so it should wrap the content, not the `<html>` tag)

**Before:**
```typescript
import { SafeArea } from "@coinbase/onchainkit/minikit";

export default function RootLayout({ children }) {
  return (
    <RootProvider>
      <html lang="en">
        <body>
          <SafeArea>{children}</SafeArea>
        </body>
      </html>
    </RootProvider>
  );
}
```

**After:**
```typescript
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <RootProvider>{children}</RootProvider>
      </body>
    </html>
  );
}
```

### 4. Verify

Run the build command:
```bash
npm run build
```

Expected: Build succeeds. The MetaMask SDK warning about `@react-native-async-storage/async-storage` is harmless and can be ignored.

## Edge Cases

### Project already has a WagmiProvider
If the project wraps with its own `WagmiProvider` outside of OnchainKit, simply remove the `OnchainKitProvider` wrapper. Update the existing wagmi config to include any connectors that were configured via OnchainKit.

### Project uses CDP API key for RPC
If the existing setup relied on `apiKey` for RPC access, add the CDP RPC URL to the transport:

```typescript
transports: {
  [base.id]: http(`https://api.developer.coinbase.com/rpc/v1/base/${process.env.NEXT_PUBLIC_ONCHAINKIT_API_KEY}`),
},
```

### Project uses multiple chains
Add all needed chains to both the `chains` array and `transports` object:

```typescript
import { base, baseSepolia } from "wagmi/chains";

export const wagmiConfig = createConfig({
  chains: [base, baseSepolia],
  transports: {
    [base.id]: http(),
    [baseSepolia.id]: http(),
  },
  // ...rest
});
```
