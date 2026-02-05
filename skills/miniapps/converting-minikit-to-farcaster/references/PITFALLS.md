# Common Pitfalls & Errors

## Contents
- Type errors (sdk.context, isInMiniApp, setPrimaryButton)
- Runtime issues (context null, detection fails)
- React patterns (useEffect with async)
- Sign-in migration

---

## Type Errors

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
setFrameContext({ context, isInMiniApp: true });

// CORRECT
const context = await sdk.context;
setFrameContext({ context, isInMiniApp: true });
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

### isInMiniApp returns false unexpectedly

Possible causes:
- Not running in iframe or React Native WebView
- Server-side rendering (detection is client-side only)
- Missing `'use client'` directive

### Context is null in components

FrameProvider not in provider chain.

```typescript
// WRONG
export function Providers({ children }) {
  return <WagmiProvider>{children}</WagmiProvider>;
}

// CORRECT
export function Providers({ children }) {
  return (
    <FrameProvider>
      <WagmiProvider>{children}</WagmiProvider>
    </FrameProvider>
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
