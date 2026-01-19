---
name: converting-minikit-to-farcaster
description: Convert Mini Apps from MiniKit (OnchainKit) to native Farcaster SDK. Use when migrating apps from @coinbase/onchainkit/minikit to @farcaster/miniapp-sdk, converting MiniKit hooks to SDK calls, or removing MiniKitProvider. Triggers on mentions of MiniKit, OnchainKit minikit, Farcaster SDK conversion, or hook-to-SDK migration.
---

# Converting MiniKit to Farcaster SDK

MiniKit wraps the Farcaster SDK into React hooks. This skill converts those abstractions back to direct SDK calls.

## Quick Reference

| MiniKit | Farcaster SDK |
|---------|---------------|
| `useMiniKit().setFrameReady()` | `await sdk.actions.ready()` |
| `useMiniKit().context` | `await sdk.context` |
| `useClose()` | `await sdk.actions.close()` |
| `useOpenUrl()` | `await sdk.actions.openUrl(url)` |
| `useViewProfile()` | `await sdk.actions.viewProfile({ fid })` |
| `useViewCast()` | `await sdk.actions.viewCast({ hash })` |
| `useComposeCast()` | `await sdk.actions.composeCast({ text, embeds })` |
| `useAddFrame()` | `await sdk.actions.addMiniApp()` |
| `useAuthenticate()` | `await sdk.actions.signIn()` |
| `useNotification()` | Manual webhook (see [NOTIFICATIONS.md](NOTIFICATIONS.md)) |

## Conversion Workflow

1. **Analyze project**: Run `python3 analyze_project.py <project_dir>` to find all MiniKit usage
2. **Convert imports**: Replace `@coinbase/onchainkit/minikit` with `@farcaster/miniapp-sdk`
3. **Transform hooks**: Convert each hook following patterns in [MAPPING.md](MAPPING.md)
4. **Remove provider**: Delete `MiniKitProvider`, see [PROVIDER_MIGRATION.md](PROVIDER_MIGRATION.md)
5. **Update manifest**: Change `frame` → `miniapp` in `.well-known/farcaster.json`, see [MANIFEST.md](MANIFEST.md)
6. **Update package.json**: See [DEPENDENCIES.md](DEPENDENCIES.md)
7. **Validate**: Run `python3 validate_conversion.py <project_dir>`

## Key Differences

- **No provider needed**: Farcaster SDK uses direct imports, not React context
- **All actions are async**: Always use `await sdk.actions.*()` 
- **Async context access**: Use `await sdk.context` (it's a Promise), not through a hook
- **SDK initialization**: Call `sdk.actions.ready()` once when app loads
- **Manifest key**: Use `miniapp` instead of `frame` in `farcaster.json`

For complete before/after examples, see [EXAMPLES.md](EXAMPLES.md).
