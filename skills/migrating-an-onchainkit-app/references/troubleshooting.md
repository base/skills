# Troubleshooting OnchainKit Migration

## Build Errors

### `Module not found: Can't resolve '@react-native-async-storage/async-storage'`
**Cause**: MetaMask SDK includes a react-native dependency that doesn't resolve in web environments.
**Impact**: Warning only. Does not affect functionality.
**Solution**: Ignore. This is a known issue with MetaMask SDK's web bundle.

### `Type error: Cannot find module 'wagmi/connectors'`
**Cause**: Outdated wagmi version.
**Solution**: Update wagmi to >= 2.16:
```bash
npm install wagmi@latest
```

### `Error: useAccount must be used within WagmiConfig`
**Cause**: A component using wagmi hooks is rendering outside the WagmiProvider tree.
**Solution**: Ensure `WagmiProvider` wraps the entire app. In Next.js, this goes in the root provider component. Both the provider and any component using wagmi hooks must have `"use client"` directive.

### `Error: No QueryClient set, use QueryClientProvider`
**Cause**: `QueryClientProvider` is missing from the provider tree.
**Solution**: Add `QueryClientProvider` inside `WagmiProvider`:
```typescript
<WagmiProvider config={wagmiConfig}>
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
</WagmiProvider>
```

### `Error: Invalid chain configuration`
**Cause**: The `transports` object doesn't have an entry for every chain in the `chains` array.
**Solution**: Every chain in `chains` needs a matching transport:
```typescript
createConfig({
  chains: [base, baseSepolia],
  transports: {
    [base.id]: http(),
    [baseSepolia.id]: http(), // Must match
  },
});
```

## Runtime Errors

### Wallet modal opens but nothing happens on click
**Cause**: The connector might not be available or the wallet extension isn't installed.
**Solution**: For extension-based wallets (MetaMask), the user needs the extension installed. For Coinbase Wallet and Base Account, they work via popup/redirect without an extension.

### Connection succeeds but address doesn't display
**Cause**: Component not re-rendering after connection state change.
**Solution**: Ensure the component using `useAccount()` is a client component with `"use client"`. wagmi hooks trigger re-renders automatically when state changes.

### Dark mode styles not working
**Cause**: Tailwind dark mode not configured.
**Solution**: Tailwind v4 uses `prefers-color-scheme` by default. If the project uses class-based dark mode, ensure the `<html>` element has the `dark` class. For Tailwind v3, check `tailwind.config.js` has `darkMode: 'class'`.

## Migration-Specific Issues

### OnchainKit styles break after removing the import
**Cause**: Some layouts depended on OnchainKit's global CSS.
**Solution**: The OnchainKit CSS mainly provides:
- Custom `ock-*` CSS variables for theming
- Rounded corner and color utilities
- Font styling

These are replaced by Tailwind utilities. If specific layouts break, inspect the element and add equivalent Tailwind classes.

### Multiple wallet connection prompts
**Cause**: The wagmi config has connectors that auto-connect on page load.
**Solution**: Use `cookieStorage` for persistence (prevents reconnection prompts):
```typescript
storage: createStorage({ storage: cookieStorage }),
```

### SSR hydration mismatch
**Cause**: Wallet state differs between server and client render.
**Solution**: Ensure the wagmi config has `ssr: true` and the provider component has `"use client"` directive. Use `cookieStorage` for state persistence across SSR.
