# B20 Asset Variant

The general-purpose variant for assets of all kinds — RWAs, wrapped assets, yield-bearing instruments, points, anything that isn't a fiat stablecoin. Everything in the core standard (roles, policies, pause, permit, memos, supply cap) applies; this file covers the deltas.

## Create params

```solidity
B20FactoryLib.encodeAssetCreateParams(name, symbol, initialAdmin, decimals)
```

- `decimals`: 6–18 inclusive (`B20Constants.MIN_ASSET_DECIMALS` / `MAX_ASSET_DECIMALS`), **immutable after creation**. Out-of-range reverts `InvalidDecimals`. Default to 18 for DeFi-style assets, 6 for stablecoin-adjacent instruments, unless the user specifies.

## Role holders bundle

Use `B20FactoryLib.B20AssetRoleHolders` with `buildRoleGrants(...)` — it's the stablecoin bundle plus an `operator` slot for `OPERATOR_ROLE`. `address(0)` slots are skipped.

## Multiplier (rebasing)

Stored balances are **raw**; a uniform on-chain **multiplier** (WAD precision, `1e18` = 1.0) scales them into the **scaled** view consumers display — like wstETH vs stETH. One `updateMultiplier` call rebases every balance at once.

- Read: `multiplier()`, `scaledBalanceOf(account)`, `toScaledBalance(raw)`, `toRawBalance(scaled)` (floor-rounded, round-trip can lose 1 ULP)
- Write: `updateMultiplier(newMultiplier)` — gated by `OPERATOR_ROLE`, and should be wrapped in an announcement (below)

If the user wants a rebasing/yield-bearing token, grant `OPERATOR_ROLE` in initCalls and note the multiplier starts at `1e18`.

## Announcements

Public, indexable disclosure brackets for operator actions. `announce(internalCalls, id, description, uri)` (gated by `OPERATOR_ROLE`) emits `Announcement`, dispatches each internal call via self-delegatecall (inner role checks see the operator), then emits `EndAnnouncement`.

- Each `id` is unique forever (`AnnouncementIdAlreadyUsed`); no nesting (`AnnouncementInProgress`)
- Inner reverts are wrapped in `InternalCallFailed` — replay the inner call directly to debug
- Convention: wrap `updateMultiplier` and `batchMint` in announcements so indexers can correlate the state change with its disclosure. Effects emitted *without* a bracket read as emergency overrides.

```solidity
bytes[] memory internalCalls = new bytes[](1);
internalCalls[0] = abi.encodeCall(IB20Asset.updateMultiplier, (newMultiplier));
IB20Asset(token).announce(internalCalls, "2026-Q3-rebase", "Ratified rebase #42", "https://disclosures.example.com/42");
```

## Batch mint

`batchMint(recipients, amounts)` — many recipients in one call, gated by `MINT_ROLE`. In initCalls, encode with `B20FactoryLib.encodeBatchMint(recipients, amounts)`. Post-creation, operators typically call it inside `announce()` (which additionally needs `OPERATOR_ROLE`). Every recipient is checked against `MINT_RECEIVER_POLICY`, even during bootstrap.

## Extra metadata

Arbitrary string key/value store per token (e.g. `"category" → "treasury-bill"`). Read with `extraMetadata(key)`; write with `updateExtraMetadata(key, value)` — gated by `METADATA_ROLE`, no announce wrapper needed, empty value removes the entry, empty key reverts `InvalidMetadataKey`. In initCalls: `B20FactoryLib.encodeUpdateExtraMetadata(key, value)` or `buildExtraMetadataUpdates(keys, values)` for several.

## `OPERATOR_ROLE`

Asset-only role gating `updateMultiplier` and `announce`. Deliberately separate from `METADATA_ROLE` (higher blast radius than metadata edits) and from `DEFAULT_ADMIN_ROLE` (operators shouldn't need full admin power).
