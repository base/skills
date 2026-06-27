# Roles and Admin Model

B20 extends OpenZeppelin `AccessControl` with a fixed set of built-in roles, plus support for
arbitrary custom roles.

## Built-In Roles

| Role | Gates |
|------|-------|
| `DEFAULT_ADMIN_ROLE` | All admin operations: role grants, policy updates, supply-cap changes |
| `MINT_ROLE` | `mint`, `mintWithMemo` |
| `BURN_ROLE` | Caller-side burns: `burn`, `burnWithMemo` (burning your own balance) |
| `BURN_BLOCKED_ROLE` | Third-party burns via `burnBlocked` — the freeze-and-seize path |
| `PAUSE_ROLE` | `pause(features)` |
| `UNPAUSE_ROLE` | `unpause(features)` — **deliberately a separate role from `PAUSE_ROLE`** |
| `METADATA_ROLE` | `updateName`, `updateSymbol`, `updateContractURI`, (ASSET) `updateExtraMetadata` |
| `OPERATOR_ROLE` | **ASSET variant only** — `updateMultiplier`, `announce` |

`PAUSE_ROLE` and `UNPAUSE_ROLE` being separate is intentional design, not an oversight — e.g. a
token can let an automated monitor pause on anomaly detection without also letting it unpause.

## Custom Roles

Beyond the built-ins, arbitrary roles are supported via `setRoleAdmin` + `grantRole`:

```solidity
bytes32 CUSTOM_ROLE = keccak256("MY_CUSTOM_ROLE");
token.setRoleAdmin(CUSTOM_ROLE, DEFAULT_ADMIN_ROLE); // or any other role as the admin
token.grantRole(CUSTOM_ROLE, someAccount);
```

Custom roles **carry no built-in effect** — B20 doesn't gate anything on them itself. They only do
something if your own integration code checks `hasRole(CUSTOM_ROLE, ...)` externally (e.g. an
off-chain indexer or a separate contract that reads this token's role state).

## The Admin Model

`DEFAULT_ADMIN_ROLE` is the default admin for every other role (i.e. a `DEFAULT_ADMIN_ROLE` holder
can `grantRole`/`revokeRole` for `MINT_ROLE`, `PAUSE_ROLE`, etc., unless `setRoleAdmin` rewires a
role to a different admin role).

### Why You Can't Just `renounceRole` Your Way to Trustless

Calling `renounceRole(DEFAULT_ADMIN_ROLE, yourself)` or `revokeRole(DEFAULT_ADMIN_ROLE, lastAdmin)`
as/against the **sole remaining admin** reverts with `LastAdminCannotRenounce`. This is a guardrail
against accidentally bricking a token's admin-gated functions through an ordinary role call.

### The Real Path: `renounceLastAdmin()`

```solidity
function renounceLastAdmin() external; // reverts NotSoleAdmin if other admins still hold the role
```

This is the **only** way to permanently remove the last admin, and it's irreversible. The same
end-state can also be reached at creation time by passing `initialAdmin == address(0)` in the
create params.

### What "Admin-less" Actually Means

After the last admin is gone (via `renounceLastAdmin()` or admin-less creation):

- Every operation gated by `DEFAULT_ADMIN_ROLE` becomes **permanently uncallable** — no more policy
  updates, no more supply-cap changes via the admin path, no more role admin changes.
- **Other already-granted roles keep working independently.** If `PAUSE_ROLE`/`MINT_ROLE`/etc. were
  granted to specific accounts before admin was renounced, those accounts retain those powers
  forever — going admin-less does not revoke them.
- **Admin resurrection is explicitly blocked**: `grantRole`, `revokeRole`, and `setRoleAdmin` all
  revert with `AccessControlUnauthorizedAccount` once admin-less — there is no backdoor to bring
  admin back.

> **Agent behavior:** If a user wants a "fully trustless" token, walk through this explicitly
> before they call `renounceLastAdmin()`:
> 1. Decide final role assignments first (mint, pause, burn-blocked) — these are frozen forever
>    once admin is gone.
> 2. Decide final policy scopes (see [policy.md](policy.md)) — these also can't be changed without
>    `DEFAULT_ADMIN_ROLE`.
> 3. Only then call `renounceLastAdmin()`, and confirm the user understands it cannot be undone.

## Pause Model

`PausableFeature` is an append-only enum partitioning the token surface into independently
pausable operations:

```solidity
enum PausableFeature { TRANSFER, MINT, BURN }
```

```solidity
function pause(PausableFeature[] calldata features) external;   // gated by PAUSE_ROLE
function unpause(PausableFeature[] calldata features) external; // gated by UNPAUSE_ROLE
function pausedFeatures() external view returns (PausableFeature[] memory);
function isPaused(PausableFeature feature) external view returns (bool);
```

Pausing is granular — you can pause `TRANSFER` while leaving `MINT`/`BURN` operable, etc. Calling a
paused operation reverts `ContractPaused(feature)`.
