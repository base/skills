# Provider Migration

**You must CREATE these provider components — they are NOT exported from `@farcaster/miniapp-sdk`.**

## Contents

- [Complete Provider Transformation](#complete-provider-transformation)
- [Step 1: Create MiniAppProvider](#step-1-create-miniappprovider)
- [Step 2: Create Wagmi Provider](#step-2-create-wagmi-provider)
- [Step 3: Combine Providers](#step-3-combine-providers)
- [Step 4: Use in Layout](#step-4-use-in-layout)
- [Using the Context](#using-the-context)
- [Remove Old Providers](#remove-old-providers)

---

## Complete Provider Transformation

Remove `OnchainKitProvider` and `MiniKitProvider` entirely. Replace with custom MiniAppProvider and WagmiProvider components that you create.

**BEFORE (MiniKit with OnchainKit):**
```typescript
import { OnchainKitProvider } from '@coinbase/onchainkit';

export function RootProvider({ children }) {
  return (
    <OnchainKitProvider apiKey={...} chain={base}>
      {children}
    </OnchainKitProvider>
  );
}
```

**AFTER (Farcaster SDK):**
```typescript
import MiniAppProvider from '@/components/providers/MiniAppProvider';
import WagmiProvider from '@/components/providers/WagmiProvider';

export function RootProvider({ children }) {
  return (
    <MiniAppProvider>
      <WagmiProvider>
        {children}
      </WagmiProvider>
    </MiniAppProvider>
  );
}
```

**OnchainKitProvider is completely removed. Do NOT wrap it or keep it.**

---

## Step 1: Create MiniAppProvider

`src/components/providers/MiniAppProvider.tsx`:

```typescript
'use client'

import { sdk, type MiniAppContext } from '@farcaster/miniapp-sdk';
import { createContext, useContext, useEffect, useState, ReactNode } from "react";

type MiniAppContextType = {
  context: MiniAppContext | null;
  isInMiniApp: boolean;
} | null;

const MiniAppContextProvider = createContext<MiniAppContextType>(null);

export const useMiniAppContext = () => useContext(MiniAppContextProvider);

export default function MiniAppProvider({ children }: { children: ReactNode }) {
  const [miniAppContext, setMiniAppContext] = useState<MiniAppContextType>(null);

  useEffect(() => {
    const init = async () => {
      try {
        // No parameters in v0.2.0+
        const isInMiniApp = await sdk.isInMiniApp();

        if (isInMiniApp) {
          // Must await - context is a Promise
          const context = await sdk.context;
          setMiniAppContext({ context, isInMiniApp: true });
        } else {
          setMiniAppContext({ context: null, isInMiniApp: false });
        }
      } catch (error) {
        console.error('MiniAppProvider init error:', error);
        setMiniAppContext({ context: null, isInMiniApp: false });
      }
    };
    init();
  }, []);

  return (
    <MiniAppContextProvider.Provider value={miniAppContext}>
      {children}
    </MiniAppContextProvider.Provider>
  );
}
```

---

## Step 2: Create Wagmi Provider

`src/components/providers/WagmiProvider.tsx`:

```typescript
'use client'

import { createConfig, http, WagmiProvider as WagmiBase } from 'wagmi';
import { base } from 'wagmi/chains';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { farcasterMiniApp } from '@farcaster/miniapp-wagmi-connector';
import { ReactNode, useState } from 'react';

const config = createConfig({
  chains: [base],
  transports: { [base.id]: http() },
  connectors: [farcasterMiniApp()],
});

export default function WagmiProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <WagmiBase config={config}>
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    </WagmiBase>
  );
}
```

---

## Step 3: Combine Providers

`src/app/providers.tsx`:

```typescript
'use client'

import { ReactNode } from 'react';
import MiniAppProvider from '@/components/providers/MiniAppProvider';
import WagmiProvider from '@/components/providers/WagmiProvider';

export function Providers({ children }: { children: ReactNode }) {
  return (
    <MiniAppProvider>
      <WagmiProvider>
        {children}
      </WagmiProvider>
    </MiniAppProvider>
  );
}
```

---

## Step 4: Use in Layout

`src/app/layout.tsx`:

```typescript
import { Providers } from './providers';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

---

## Using the Context

```typescript
import { useMiniAppContext } from '@/components/providers/MiniAppProvider';

function MyComponent() {
  const miniAppContext = useMiniAppContext();

  if (!miniAppContext) return <div>Loading...</div>;
  if (!miniAppContext.isInMiniApp) return <div>Open in Farcaster</div>;

  return <div>Welcome {miniAppContext.context?.user?.displayName}</div>;
}
```

---

## Remove Old Providers

```typescript
// Delete all OnchainKit imports
import { OnchainKitProvider } from '@coinbase/onchainkit';
import { MiniKitProvider } from '@coinbase/onchainkit/minikit';
import '@coinbase/onchainkit/styles.css';

// Delete from .env
NEXT_PUBLIC_ONCHAINKIT_API_KEY=xxx
```

**Important**: Remove the entire `OnchainKitProvider` wrapper, not just `MiniKitProvider`. The Farcaster SDK does not use OnchainKit.
