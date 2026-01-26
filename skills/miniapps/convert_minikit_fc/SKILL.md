---
name: converting-minikit-to-farcaster
description: Converts Mini Apps from MiniKit (OnchainKit) to native Farcaster SDK. Use when migrating from @coinbase/onchainkit/minikit, converting MiniKit hooks, removing MiniKitProvider, or when user mentions MiniKit, OnchainKit, or Farcaster SDK migration.
---

# MiniKit to Farcaster SDK

## Breaking Changes (SDK v0.2.0+)

1. `sdk.context` is a **Promise** — must await
2. `sdk.isInMiniApp()` accepts **no parameters**
3. `sdk.actions.setPrimaryButton()` has no onClick callback
4. **No React exports** — SDK has no `/react` subpath
5. **MiniAppProvider must be CREATED** — It is NOT exported from the SDK. You must create this component yourself (see [references/PROVIDER.md](references/PROVIDER.md))

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
| `useAuthenticate()` | `sdk.quickAuth.getToken()` | See [references/AUTH.md](references/AUTH.md) |

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
2. Update dependencies — see [references/DEPENDENCIES.md](references/DEPENDENCIES.md)
3. Replace imports: `@coinbase/onchainkit/minikit` → `@farcaster/miniapp-sdk`
4. Convert hooks using reference above
5. **Create** MiniAppProvider + WagmiProvider components, remove OnchainKitProvider — see [references/PROVIDER.md](references/PROVIDER.md)
6. Handle SafeArea (see conditional workflow below)
7. Update manifest: `frame` → `miniapp` — see [references/MANIFEST.md](references/MANIFEST.md)
8. Rename config: `minikit.config.ts` → `farcaster.config.ts`, `minikitConfig` → `farcasterConfig`, update import in `.well-known` route

## SafeArea Workflow

Check if the project imports `SafeArea` from OnchainKit:

**Project uses `<SafeArea>`?** → Create replacement component — see [references/SAFEAREA.md](references/SAFEAREA.md)
**Project does NOT use `<SafeArea>`?** → Skip, no action needed

## Common Errors

**"Property 'user' does not exist on type 'Promise<MiniAppContext>'"**
→ Await `sdk.context` before accessing properties

**"Expected 0 arguments, but got 1"**
→ Remove parameters from `sdk.isInMiniApp()`

**Context is null in components**
→ Ensure MiniAppProvider is in your provider chain

**"Failed to fetch" in development**
→ Always check `await sdk.isInMiniApp()` before calling SDK methods

## References

- [references/MAPPING.md](references/MAPPING.md) — Complete hook-by-hook conversion reference
- [references/EXAMPLES.md](references/EXAMPLES.md) — Before/after code examples
- [references/PROVIDER.md](references/PROVIDER.md) — Provider setup with MiniAppProvider
- [references/SAFEAREA.md](references/SAFEAREA.md) — SafeArea component migration
- [references/PITFALLS.md](references/PITFALLS.md) — Common errors and solutions
- [references/DEPENDENCIES.md](references/DEPENDENCIES.md) — Package updates
- [references/AUTH.md](references/AUTH.md) — Quick Auth migration
- [references/MANIFEST.md](references/MANIFEST.md) — farcaster.json changes

## Scripts

- [scripts/analyze_project.py](scripts/analyze_project.py) — Analyze MiniKit usage before conversion
- [scripts/validate_conversion.py](scripts/validate_conversion.py) — Validate conversion is complete
