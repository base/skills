# SafeArea Migration

**Only create this component if the project imports `SafeArea` from `@coinbase/onchainkit/minikit`.**

If the project does NOT use SafeArea, skip this file entirely.

## Contents

- [SafeArea Component](#safearea-component)
- [Usage](#usage)
- [useSafeAreaInsets Hook](#usesafeareainsets-hook)
- [When to Use](#when-to-use)
- [SafeAreaInsets Type](#safeareainsets-type)

---

## SafeArea Component

Create `src/components/SafeArea.tsx`:

```typescript
'use client'

import { useMiniAppContext } from '@/components/providers/MiniAppProvider';
import { ReactNode } from 'react';

interface SafeAreaProps {
  children: ReactNode;
  className?: string;
}

export function SafeArea({ children, className }: SafeAreaProps) {
  const miniAppContext = useMiniAppContext();

  // Only apply insets when running inside a mini app
  if (!miniAppContext?.isInMiniApp) {
    return <div className={className}>{children}</div>;
  }

  const insets = miniAppContext.context?.client?.safeAreaInsets;

  return (
    <div
      className={className}
      style={{
        paddingTop: insets?.top ?? 0,
        paddingBottom: insets?.bottom ?? 0,
        paddingLeft: insets?.left ?? 0,
        paddingRight: insets?.right ?? 0,
      }}
    >
      {children}
    </div>
  );
}
```

## Usage

**Before (OnchainKit):**
```typescript
import { SafeArea } from '@coinbase/onchainkit/minikit';

<SafeArea>
  {children}
</SafeArea>
```

**After:**
```typescript
import { SafeArea } from '@/components/SafeArea';

<SafeArea>
  {children}
</SafeArea>
```

---

## useSafeAreaInsets Hook

For more control, create `src/hooks/useSafeAreaInsets.ts`:

```typescript
'use client'

import { useMiniAppContext } from '@/components/providers/MiniAppProvider';

const DEFAULT_INSETS = { top: 0, bottom: 0, left: 0, right: 0 };

export function useSafeAreaInsets() {
  const miniAppContext = useMiniAppContext();

  // Return zeros when not in mini app
  if (!miniAppContext?.isInMiniApp) {
    return DEFAULT_INSETS;
  }

  return miniAppContext.context?.client?.safeAreaInsets ?? DEFAULT_INSETS;
}
```

**Usage:**
```typescript
import { useSafeAreaInsets } from '@/hooks/useSafeAreaInsets';

function MyComponent() {
  const insets = useSafeAreaInsets();

  return (
    <div style={{ paddingBottom: insets.bottom }}>
      Fixed footer content
    </div>
  );
}
```

---

## When to Use

| Scenario | Solution |
|----------|----------|
| Project imports `SafeArea` from OnchainKit | Create replacement component |
| Project does NOT use SafeArea | Skip this file |
| Full page wrapper (after creating component) | `<SafeArea>` component |
| Specific edge padding | `useSafeAreaInsets()` hook |

---

## SafeAreaInsets Type

From `@farcaster/miniapp-sdk`:

```typescript
type SafeAreaInsets = {
  top: number;
  bottom: number;
  left: number;
  right: number;
};
```

Available via `context.client.safeAreaInsets` when `isInMiniApp` is true.
