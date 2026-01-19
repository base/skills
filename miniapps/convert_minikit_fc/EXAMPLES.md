# Conversion Examples

Complete before/after examples for common MiniKit patterns.

## Table of Contents

- [Basic Page Component](#basic-page-component)
- [Social Actions Component](#social-actions-component)
- [User Profile Display](#user-profile-display)
- [Share Flow](#share-flow)
- [Full App Structure](#full-app-structure)

---

## Basic Page Component

### Before (MiniKit)
```typescript
// app/page.tsx
'use client';

import { useEffect } from 'react';
import { useMiniKit } from '@coinbase/onchainkit/minikit';

export default function HomePage() {
  const { setFrameReady, isFrameReady, context } = useMiniKit();

  useEffect(() => {
    if (!isFrameReady) {
      setFrameReady();
    }
  }, [setFrameReady, isFrameReady]);

  return (
    <main style={{ 
      paddingTop: context?.client?.safeAreaInsets?.top ?? 0,
      paddingBottom: context?.client?.safeAreaInsets?.bottom ?? 0 
    }}>
      <h1>Welcome, {context?.user?.displayName || 'Guest'}</h1>
      <p>FID: {context?.user?.fid}</p>
    </main>
  );
}
```

### After (Farcaster SDK)
```typescript
// app/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { sdk } from '@farcaster/miniapp-sdk';

export default function HomePage() {
  const [isReady, setIsReady] = useState(false);
  const [context, setContext] = useState<typeof sdk.context>(null);

  useEffect(() => {
    const init = async () => {
      setContext(sdk.context);
      await sdk.actions.ready();
      setIsReady(true);
    };
    init();
  }, []);

  if (!isReady) {
    return null; // Or a loading state
  }

  return (
    <main style={{ 
      paddingTop: context?.client?.safeAreaInsets?.top ?? 0,
      paddingBottom: context?.client?.safeAreaInsets?.bottom ?? 0 
    }}>
      <h1>Welcome, {context?.user?.displayName || 'Guest'}</h1>
      <p>FID: {context?.user?.fid}</p>
    </main>
  );
}
```

---

## Social Actions Component

### Before (MiniKit)
```typescript
// components/SocialActions.tsx
'use client';

import {
  useClose,
  useOpenUrl,
  useViewProfile,
  useComposeCast
} from '@coinbase/onchainkit/minikit';

interface Props {
  authorFid: number;
}

export function SocialActions({ authorFid }: Props) {
  const close = useClose();
  const openUrl = useOpenUrl();
  const viewProfile = useViewProfile();
  const { composeCast } = useComposeCast();

  return (
    <div className="flex gap-2">
      <button onClick={() => viewProfile(authorFid)}>
        View Author
      </button>
      
      <button onClick={() => composeCast({
        text: 'Check this out!',
        embeds: [window.location.href]
      })}>
        Share
      </button>
      
      <button onClick={() => openUrl('https://docs.farcaster.xyz')}>
        Docs
      </button>
      
      <button onClick={close}>
        Close
      </button>
    </div>
  );
}
```

### After (Farcaster SDK)
```typescript
// components/SocialActions.tsx
'use client';

import { sdk } from '@farcaster/miniapp-sdk';

interface Props {
  authorFid: number;
}

export function SocialActions({ authorFid }: Props) {
  const handleViewProfile = async () => {
    await sdk.actions.viewProfile({ fid: authorFid });
  };

  const handleShare = async () => {
    await sdk.actions.composeCast({
      text: 'Check this out!',
      embeds: [window.location.href]
    });
  };

  const handleOpenDocs = async () => {
    await sdk.actions.openUrl('https://docs.farcaster.xyz');
  };

  const handleClose = async () => {
    await sdk.actions.close();
  };

  return (
    <div className="flex gap-2">
      <button onClick={handleViewProfile}>
        View Author
      </button>
      
      <button onClick={handleShare}>
        Share
      </button>
      
      <button onClick={handleOpenDocs}>
        Docs
      </button>
      
      <button onClick={handleClose}>
        Close
      </button>
    </div>
  );
}
```

---

## User Profile Display

### Before (MiniKit)
```typescript
// components/UserProfile.tsx
'use client';

import { useMiniKit } from '@coinbase/onchainkit/minikit';

export function UserProfile() {
  const { context } = useMiniKit();
  
  if (!context?.user) {
    return <div>Loading...</div>;
  }

  const { fid, username, displayName, pfpUrl } = context.user;
  const isAdded = context.client?.added;

  return (
    <div className="profile">
      {pfpUrl && <img src={pfpUrl} alt={displayName} />}
      <h2>{displayName}</h2>
      <p>@{username}</p>
      <p>FID: {fid}</p>
      {isAdded && <span className="badge">App Saved</span>}
    </div>
  );
}
```

### After (Farcaster SDK)
```typescript
// components/UserProfile.tsx
'use client';

import { useEffect, useState } from 'react';
import { sdk, type MiniAppContext } from '@farcaster/miniapp-sdk';

export function UserProfile() {
  const [context, setContext] = useState<MiniAppContext | null>(null);

  useEffect(() => {
    setContext(sdk.context);
  }, []);
  
  if (!context?.user) {
    return <div>Loading...</div>;
  }

  const { fid, username, displayName, pfpUrl } = context.user;
  const isAdded = context.client?.added;

  return (
    <div className="profile">
      {pfpUrl && <img src={pfpUrl} alt={displayName} />}
      <h2>{displayName}</h2>
      <p>@{username}</p>
      <p>FID: {fid}</p>
      {isAdded && <span className="badge">App Saved</span>}
    </div>
  );
}
```

**Tip**: Create a custom hook to centralize context access:

```typescript
// hooks/useFarcasterContext.ts
import { useEffect, useState } from 'react';
import { sdk, type MiniAppContext } from '@farcaster/miniapp-sdk';

export function useFarcasterContext() {
  const [context, setContext] = useState<MiniAppContext | null>(null);

  useEffect(() => {
    setContext(sdk.context);
  }, []);

  return context;
}
```

---

## Share Flow

### Before (MiniKit)
```typescript
// components/ShareButton.tsx
'use client';

import { useState } from 'react';
import { useComposeCast, useMiniKit } from '@coinbase/onchainkit/minikit';

interface Props {
  score: number;
  gameId: string;
}

export function ShareButton({ score, gameId }: Props) {
  const [shared, setShared] = useState(false);
  const { composeCast } = useComposeCast();
  const { context } = useMiniKit();

  const handleShare = async () => {
    const shareUrl = `https://myapp.com/game/${gameId}`;
    
    composeCast({
      text: `I scored ${score} points! Can you beat me? 🎮`,
      embeds: [shareUrl]
    });
    
    setShared(true);
  };

  return (
    <button 
      onClick={handleShare}
      disabled={shared}
    >
      {shared ? 'Shared!' : 'Share Score'}
    </button>
  );
}
```

### After (Farcaster SDK)
```typescript
// components/ShareButton.tsx
'use client';

import { useState } from 'react';
import { sdk } from '@farcaster/miniapp-sdk';

interface Props {
  score: number;
  gameId: string;
}

export function ShareButton({ score, gameId }: Props) {
  const [shared, setShared] = useState(false);

  const handleShare = async () => {
    const shareUrl = `https://myapp.com/game/${gameId}`;
    
    const result = await sdk.actions.composeCast({
      text: `I scored ${score} points! Can you beat me? 🎮`,
      embeds: [shareUrl]
    });
    
    // Check if user actually posted
    if (result?.cast) {
      setShared(true);
      console.log('Cast posted with hash:', result.cast.hash);
    }
  };

  return (
    <button 
      onClick={handleShare}
      disabled={shared}
    >
      {shared ? 'Shared!' : 'Share Score'}
    </button>
  );
}
```

---

## Full App Structure

### Before (MiniKit) - Provider Setup

```typescript
// app/providers.tsx
'use client';

import { ReactNode } from 'react';
import { MiniKitProvider } from '@coinbase/onchainkit/minikit';
import { base } from 'wagmi/chains';

export function Providers({ children }: { children: ReactNode }) {
  return (
    <MiniKitProvider
      apiKey={process.env.NEXT_PUBLIC_ONCHAINKIT_API_KEY}
      chain={base}
      config={{
        appearance: {
          mode: 'auto',
          theme: 'default',
        },
      }}
    >
      {children}
    </MiniKitProvider>
  );
}
```

```typescript
// app/layout.tsx
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

### After (Farcaster SDK) - No Provider Needed

```typescript
// app/providers.tsx
// DELETE THIS FILE - No provider needed!

// Or if you need other providers (wagmi, etc):
'use client';

import { ReactNode } from 'react';
import { WagmiProvider } from 'wagmi';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { config } from './wagmi-config';

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

```typescript
// app/layout.tsx
// If no other providers needed:
export default function RootLayout({ children }) {
  return (
    <html>
      <body>{children}</body>
    </html>
  );
}

// Or with other providers:
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

```typescript
// app/page.tsx - Initialize SDK here
'use client';

import { useEffect, useState } from 'react';
import { sdk } from '@farcaster/miniapp-sdk';

export default function HomePage() {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const init = async () => {
      await sdk.actions.ready();
      setIsReady(true);
    };
    init();
  }, []);

  if (!isReady) return null;

  return <main>Your app content</main>;
}
```

---

## Common Patterns Summary

| Pattern | MiniKit | Farcaster SDK |
|---------|---------|---------------|
| Get context | `useMiniKit().context` | `sdk.context` (direct) |
| Signal ready | `setFrameReady()` in useEffect | `await sdk.actions.ready()` |
| Action handlers | Direct function call | Async function with await |
| Provider | Required `<MiniKitProvider>` | Not needed |
| Hook imports | Multiple hook imports | Single `sdk` import |
