# Provider Migration Guide

How to migrate from `OnchainKitProvider` with `miniKit` config to native Wagmi + Farcaster SDK.

## Overview

MiniKit uses `OnchainKitProvider` with a `miniKit` prop that auto-configures wagmi, react-query, and the Farcaster connector. When migrating to the native Farcaster SDK, you need to set these up manually.

## Before (OnchainKitProvider with MiniKit)

```typescript
// app/providers.tsx
"use client";
import { ReactNode } from "react";
import { base } from "wagmi/chains";
import { OnchainKitProvider } from "@coinbase/onchainkit";
import "@coinbase/onchainkit/styles.css";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <OnchainKitProvider
      apiKey={process.env.NEXT_PUBLIC_ONCHAINKIT_API_KEY}
      chain={base}
      config={{
        appearance: {
          mode: "auto",
        },
        wallet: {
          display: "modal",
          preference: "all",
        },
      }}
      miniKit={{
        enabled: true,
        autoConnect: true,
        notificationProxyUrl: undefined,
      }}
    >
      {children}
    </OnchainKitProvider>
  );
}
```

## After (Wagmi + Farcaster Connector)

```typescript
// app/providers.tsx
"use client";
import { ReactNode } from "react";
import { createConfig, http, WagmiProvider } from "wagmi";
import { base, optimism } from "wagmi/chains";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { farcasterMiniApp } from "@farcaster/miniapp-wagmi-connector";

// Create wagmi config with Farcaster connector
export const config = createConfig({
  chains: [base, optimism],
  transports: {
    [base.id]: http(),
    [optimism.id]: http(),
  },
  connectors: [
    farcasterMiniApp(),
  ],
});

const queryClient = new QueryClient();

export function Providers({ children }: { children: ReactNode }) {
  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    </WagmiProvider>
  );
}
```

## Step-by-Step Migration

### Step 1: Install Required Dependencies

```bash
npm uninstall @coinbase/onchainkit
npm install @farcaster/miniapp-sdk @farcaster/miniapp-wagmi-connector wagmi viem @tanstack/react-query
```

Or in one command:
```bash
npm uninstall @coinbase/onchainkit && npm install @farcaster/miniapp-sdk @farcaster/miniapp-wagmi-connector wagmi viem @tanstack/react-query
```

### Step 2: Update providers.tsx

Replace `OnchainKitProvider` with manual Wagmi setup:

```typescript
"use client";
import { ReactNode } from "react";
import { createConfig, http, WagmiProvider } from "wagmi";
import { base } from "wagmi/chains";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { farcasterMiniApp } from "@farcaster/miniapp-wagmi-connector";

const config = createConfig({
  chains: [base],
  transports: {
    [base.id]: http(),
  },
  connectors: [
    farcasterMiniApp(),
  ],
});

const queryClient = new QueryClient();

export function Providers({ children }: { children: ReactNode }) {
  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    </WagmiProvider>
  );
}
```

### Step 3: Remove OnchainKit CSS Import

Delete this line from your providers or layout:
```typescript
// DELETE THIS
import "@coinbase/onchainkit/styles.css";
```

### Step 4: Add SDK Ready Call

In your main page component, add the SDK ready call:

```typescript
// app/page.tsx
"use client";
import { useEffect, useState } from "react";
import { sdk } from "@farcaster/miniapp-sdk";

export default function Home() {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const init = async () => {
      await sdk.actions.ready();
      setIsReady(true);
    };
    init();
  }, []);

  if (!isReady) return null;

  return <main>Your app</main>;
}
```

## Adding Multiple Connectors

If you want to support both Farcaster wallet and Base Account (smart wallet):

```typescript
import { farcasterMiniApp } from "@farcaster/miniapp-wagmi-connector";
import { baseAccount } from "wagmi/connectors";

const config = createConfig({
  chains: [base, optimism],
  transports: {
    [base.id]: http(),
    [optimism.id]: http(),
  },
  connectors: [
    farcasterMiniApp(),
    baseAccount({
      appName: "My Mini App",
      appLogoUrl: "https://myapp.com/icon.png",
    }),
  ],
});
```

## Config Mapping

| OnchainKitProvider Config | Wagmi Equivalent |
|--------------------------|------------------|
| `chain={base}` | `chains: [base]` in createConfig |
| `miniKit.enabled: true` | `farcasterMiniApp()` connector |
| `miniKit.autoConnect: true` | Wagmi handles this automatically |
| `config.appearance` | Not needed (use your own CSS) |
| `config.wallet.display` | Not applicable |
| `apiKey` | Not needed for Farcaster SDK |

## Environment Variables

### Remove These
```env
# DELETE - not needed for Farcaster SDK
NEXT_PUBLIC_ONCHAINKIT_API_KEY=xxx
```

### Keep These
```env
# Keep for manifest
NEXT_PUBLIC_URL=https://yourapp.com
FARCASTER_HEADER=xxx
FARCASTER_PAYLOAD=xxx
FARCASTER_SIGNATURE=xxx
```

## Checklist

- [ ] Uninstalled `@coinbase/onchainkit`
- [ ] Installed `@farcaster/miniapp-sdk`
- [ ] Installed `@farcaster/miniapp-wagmi-connector`
- [ ] Installed `wagmi`, `viem`, `@tanstack/react-query`
- [ ] Replaced `OnchainKitProvider` with `WagmiProvider` + `QueryClientProvider`
- [ ] Added `farcasterMiniApp()` connector to wagmi config
- [ ] Removed `@coinbase/onchainkit/styles.css` import
- [ ] Added `sdk.actions.ready()` call in main page
- [ ] Removed `NEXT_PUBLIC_ONCHAINKIT_API_KEY` from env
