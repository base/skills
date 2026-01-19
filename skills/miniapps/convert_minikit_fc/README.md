# MiniKit to Farcaster SDK Converter

A Claude Skill for converting Mini Apps from [MiniKit](https://docs.base.org/onchainkit/latest/components/minikit/overview) (OnchainKit) to the native [Farcaster SDK](https://miniapps.farcaster.xyz/docs/getting-started).

## What This Does

MiniKit wraps the Farcaster SDK into React hooks. This skill helps Claude convert those abstractions back to direct SDK calls when you want to:

- Remove the OnchainKit dependency
- Use the native Farcaster SDK directly
- Have more control over the Mini App lifecycle
- Reduce bundle size

## Quick Reference

| MiniKit | Farcaster SDK |
|---------|---------------|
| `useMiniKit().setFrameReady()` | `await sdk.actions.ready()` |
| `useMiniKit().context` | `await sdk.context` |
| `useClose()` | `await sdk.actions.close()` |
| `useOpenUrl()` | `await sdk.actions.openUrl(url)` |
| `useViewProfile()` | `await sdk.actions.viewProfile({ fid })` |
| `useComposeCast()` | `await sdk.actions.composeCast({ text, embeds })` |
| `useAddFrame()` | `await sdk.actions.addMiniApp()` |
| `useAuthenticate()` | `await sdk.actions.signIn()` |

## Installation

### For Claude Code

Copy this skill to your Claude Code skills directory:

```bash
# Personal skill (available in all projects)
cp -r . ~/.claude/skills/minikit-to-farcaster/

# Or project skill (shared with team via git)
cp -r . .claude/skills/minikit-to-farcaster/
```

### For Claude.ai Projects

Upload the skill files to your Claude project's knowledge base.

## Usage

Once installed, Claude will automatically use this skill when you ask it to:

- Convert a MiniKit app to Farcaster SDK
- Migrate from OnchainKit minikit to native SDK
- Remove MiniKitProvider from your app
- Convert MiniKit hooks to SDK calls

### Example Prompts

```
Convert this MiniKit component to use the Farcaster SDK directly
```

```
Help me migrate my app from @coinbase/onchainkit/minikit to @farcaster/miniapp-sdk
```

```
Remove MiniKitProvider and use the native Farcaster SDK instead
```

## Utility Scripts

### Analyze a Project

Find all MiniKit usage in your project:

```bash
python3 analyze_project.py ./my-minikit-app
```

Output includes:
- All MiniKit imports
- Hook usages and their locations
- Provider locations
- Summary of what needs to change

### Validate Conversion

After converting, verify everything is correct:

```bash
python3 validate_conversion.py ./my-converted-app
```

Checks for:
- No remaining MiniKit imports
- No remaining MiniKit hooks
- MiniKitProvider removed
- Farcaster SDK properly imported
- `sdk.actions.ready()` is called
- package.json has correct dependencies

## Documentation

- [SKILL.md](SKILL.md) - Main skill entry point
- [MAPPING.md](MAPPING.md) - Complete hook-to-SDK mapping reference
- [EXAMPLES.md](EXAMPLES.md) - Before/after code examples
- [PROVIDER_MIGRATION.md](PROVIDER_MIGRATION.md) - Removing MiniKitProvider
- [MANIFEST.md](MANIFEST.md) - `.well-known/farcaster.json` configuration
- [DEPENDENCIES.md](DEPENDENCIES.md) - Package.json changes
- [NOTIFICATIONS.md](NOTIFICATIONS.md) - Notification system migration

## Key Differences

| Aspect | MiniKit | Farcaster SDK |
|--------|---------|---------------|
| Setup | Requires `<MiniKitProvider>` | Direct import |
| Hooks | React hooks | Direct async methods |
| Context | `useMiniKit().context` | `await sdk.context` |
| Ready signal | `setFrameReady()` | `await sdk.actions.ready()` |
| Manifest key | `frame` | `miniapp` |
| Bundle | Includes OnchainKit | Minimal SDK only |

## Contributing

Issues and PRs welcome! This skill is designed to be:

- **Concise** - Only essential information
- **Progressive** - Detailed docs in separate files
- **Testable** - Utility scripts for validation

## License

MIT

## Links

- [MiniKit Documentation](https://docs.base.org/onchainkit/latest/components/minikit/overview)
- [Farcaster SDK Documentation](https://miniapps.farcaster.xyz/docs/getting-started)
- [Claude Skills Documentation](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
