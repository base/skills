# MiniKit to Farcaster SDK

Converts Mini Apps from MiniKit (OnchainKit) to native Farcaster SDK.

## Breaking Changes (SDK v0.2.0+)

1. `sdk.context` is a **Promise** — must await
2. `sdk.isInMiniApp()` accepts **no parameters**
3. `sdk.actions.setPrimaryButton()` has no onClick callback

Check version: `npm list @farcaster/miniapp-sdk`

## Quick Reference

| MiniKit | Farcaster SDK | Notes |
|---------|---------------|-------|
| `useMiniKit().setFrameReady()` | `await sdk.actions.ready()` | |
| `useMiniKit().context` | `await sdk.context` | **Async** |
| `useMiniKit().isSDKLoaded` | `await sdk.isInMiniApp()` | No params |
| `useClose()` | `await sdk.actions.close()` | |
| `useOpenUrl(url)` | `await sdk.actions.openUrl(url)` | |
| `useViewProfile(fid)` | `await sdk.actions.viewProfile({ fid })` | |
| `useViewCast(hash)` | `await sdk.actions.viewCast({ hash })` | |
| `useComposeCast()` | `await sdk.actions.composeCast({ text, embeds })` | |
| `useAddFrame()` | `await sdk.actions.addMiniApp()` | |
| `usePrimaryButton(opts, cb)` | `await sdk.actions.setPrimaryButton(opts)` | No callback |
| `useAuthenticate()` | `sdk.quickAuth.getToken()` | See [auth.md](auth.md) |

## Context Access Pattern

```typescript
// WRONG
const fid = sdk.context?.user?.fid;

// CORRECT
const context = await sdk.context;
const fid = context?.user?.fid;
```

In React components, use state:

```typescript
const [context, setContext] = useState(null);

useEffect(() => {
  const load = async () => {
    const ctx = await sdk.context;
    setContext(ctx);
  };
  load();
}, []);
```

## Conversion Workflow

1. Verify Node.js >= 22.11.0
2. Update dependencies — see [dependencies.md](dependencies.md)
3. Replace imports: `@coinbase/onchainkit/minikit` → `@farcaster/miniapp-sdk`
4. Convert hooks using reference above
5. Add FrameProvider — see [provider.md](provider.md)
6. Update manifest: `frame` → `miniapp` — see [manifest.md](manifest.md)

## Common Errors

**"Property 'user' does not exist on type 'Promise<MiniAppContext>'"**
→ Await `sdk.context` before accessing properties

**"Expected 0 arguments, but got 1"**
→ Remove parameters from `sdk.isInMiniApp()`

**Context is null in components**
→ Ensure FrameProvider is in your provider chain

## References

- [mapping.md](mapping.md) — Complete hook-by-hook conversion reference
- [examples.md](examples.md) — Before/after code examples
- [provider.md](provider.md) — Provider setup with FrameProvider
- [pitfalls.md](pitfalls.md) — Common errors and solutions
- [dependencies.md](dependencies.md) — Package updates
- [auth.md](auth.md) — Quick Auth migration
- [manifest.md](manifest.md) — farcaster.json changes
