# Common Pitfalls & Errors

## Contents

- [Type Errors](#type-errors)
  - MiniAppProvider not exported
  - Property 'user' does not exist on Promise
  - Expected 0 arguments
  - Promise not assignable
  - onClick not in SetPrimaryButtonOptions
- [Runtime Issues](#runtime-issues)
  - OnchainKitProvider still in chain
  - isInMiniApp returns false
  - Context is null
  - Failed to fetch
- [React Patterns](#react-patterns)
  - Async useEffect
  - Loading context
- [Sign-In Migration](#sign-in-migration)
- [Validation Commands](#validation-commands)

---

## Type Errors

### "Module '@farcaster/miniapp-sdk' has no exported member 'MiniAppProvider'"

MiniAppProvider is NOT exported from the SDK. You must CREATE it yourself.

```typescript
// WRONG - trying to import
import { MiniAppProvider } from '@farcaster/miniapp-sdk';

// CORRECT - create the component yourself
// See PROVIDER.md for the full MiniAppProvider component code
```

The Farcaster SDK only exports `sdk` and types. All provider components must be created by you.

### "Property 'user' does not exist on type 'Promise<MiniAppContext>'"

Accessing `sdk.context` without awaiting.

```typescript
// WRONG
const fid = sdk.context?.user?.fid;

// CORRECT
const context = await sdk.context;
const fid = context?.user?.fid;
```

### "Expected 0 arguments, but got 1"

Passing parameters to `sdk.isInMiniApp()`.

```typescript
// WRONG
await sdk.isInMiniApp({ timeoutMs: 500 });

// CORRECT
await sdk.isInMiniApp();
```

Custom timeout workaround:
```typescript
const checkWithTimeout = async (ms = 5000) => {
  try {
    return await Promise.race([
      sdk.isInMiniApp(),
      new Promise((_, r) => setTimeout(() => r(new Error('Timeout')), ms))
    ]);
  } catch {
    return false;
  }
};
```

### "Type 'Promise<MiniAppContext>' is not assignable..."

Assigning `sdk.context` to state without awaiting.

```typescript
// WRONG
const context = sdk.context;
setMiniAppContext({ context, isInMiniApp: true });

// CORRECT
const context = await sdk.context;
setMiniAppContext({ context, isInMiniApp: true });
```

### "'onClick' does not exist in type 'SetPrimaryButtonOptions'"

`setPrimaryButton` no longer supports callbacks.

```typescript
// WRONG (MiniKit pattern)
usePrimaryButton(
  { text: "Click" },
  () => handleClick()
);

// CORRECT - state only, no callback
await sdk.actions.setPrimaryButton({
  text: "Click",
  disabled: false,
  hidden: false,
  loading: false
});
```

For click handling, use regular React buttons.

---

## Runtime Issues

### OnchainKitProvider still in provider chain

Remove it entirely. Do not wrap WagmiProvider around OnchainKitProvider.

```typescript
// WRONG - keeping OnchainKitProvider
<WagmiProvider>
  <OnchainKitProvider>
    {children}
  </OnchainKitProvider>
</WagmiProvider>

// CORRECT - OnchainKitProvider removed completely
<MiniAppProvider>
  <WagmiProvider>
    {children}
  </WagmiProvider>
</MiniAppProvider>
```

### isInMiniApp returns false unexpectedly

Possible causes:
- Not running in iframe or React Native WebView
- Server-side rendering (detection is client-side only)
- Missing `'use client'` directive

### Context is null in components

MiniAppProvider not in provider chain.

```typescript
// WRONG
export function Providers({ children }) {
  return <WagmiProvider>{children}</WagmiProvider>;
}

// CORRECT
export function Providers({ children }) {
  return (
    <MiniAppProvider>
      <WagmiProvider>{children}</WagmiProvider>
    </MiniAppProvider>
  );
}
```

### Context is null even when isInMiniApp is true

Not awaiting `sdk.context`:

```typescript
// WRONG
const context = sdk.context; // Promise, not data

// CORRECT
const context = await sdk.context;
```

### "Failed to fetch" in development

SDK methods fail outside Farcaster environment (local browser, dev tools).

```typescript
// WRONG
await sdk.actions.ready();
const ctx = await sdk.context;

// CORRECT
const inMiniApp = await sdk.isInMiniApp();
if (inMiniApp) {
  const ctx = await sdk.context;
  await sdk.actions.ready();
}
```

---

## React Patterns

### Async useEffect

```typescript
// WRONG - returns Promise
useEffect(async () => {
  await sdk.actions.ready();
}, []);

// CORRECT - wrap in function
useEffect(() => {
  const init = async () => {
    await sdk.actions.ready();
  };
  init();
}, []);
```

### Loading context in components

```typescript
function MyComponent() {
  const [context, setContext] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const isInMiniApp = await sdk.isInMiniApp();
        if (isInMiniApp) {
          const ctx = await sdk.context;
          setContext(ctx);
        }
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return null;
  return <div>{context?.user?.fid}</div>;
}
```

---

## Sign-In Migration

### "This comparison appears to be unintentional..."

`signIn` returns `SignInResult`, not boolean.

```typescript
// WRONG (MiniKit pattern)
const result = await signIn({ nonce });
if (result === false) { ... }

// CORRECT
const result = await sdk.actions.signIn({ nonce });
if (!result) {
  // Sign-in cancelled or failed
}
```

For SDK v0.2.0+, prefer Quick Auth:

```typescript
const { token } = await sdk.quickAuth.getToken();
// Or use authenticated fetch
const res = await sdk.quickAuth.fetch('/api/auth');
```

---

## Validation Commands

After conversion, verify:

```bash
# No MiniKit imports remaining
grep -r "@coinbase/onchainkit/minikit" src/

# Check sdk.context usage (should be awaited)
grep -r "sdk\.context" src/

# Check isInMiniApp calls (no parameters)
grep -r "isInMiniApp(" src/

# Build and type check
npm run build && npx tsc --noEmit
```
