# B20 Stablecoin Variant

The fixed-decimals, fiat-backed carveout. Everything in the core standard (roles, policies, pause, permit, memos, supply cap) applies; this file covers the deltas.

## Create params

```solidity
B20FactoryLib.encodeStablecoinCreateParams(name, symbol, initialAdmin, currency)
```

- `currency`: required, **immutable**, uppercase ASCII `A`–`Z` only (no digits, lowercase, or separators). Empty reverts `MissingRequiredField("currency")`; invalid bytes revert `InvalidCurrency`. Use the ISO 4217 code of the tracked fiat (`"USD"`, `"EUR"`, `"GBP"`). It is **self-declared** — the chain does not verify fiat backing; wallets and indexers use it for grouping only.
- `decimals()` is hard-wired to `6` (matching major stablecoins). If the user needs other decimals, they need the Asset variant — flag the trade-off (they lose the `currency()` field).

## Role holders bundle

Use `B20FactoryLib.B20RoleHolders` with `buildRoleGrants(...)` — minter, burner, burnBlocker, pauser, unpauser, metadataAdmin. No `operator` slot (announcements/multiplier are Asset-only). `address(0)` slots are skipped.

## Initial mint in initCalls

There is no `batchMint` on stablecoins and no `encodeMint` helper in `B20FactoryLib` — encode the core `mint` directly:

```solidity
import {IB20} from "base-std/interfaces/IB20.sol";

bytes[] memory mints = new bytes[](1);
mints[0] = abi.encodeCall(IB20.mint, (treasury, 1_000_000e6)); // 6 decimals!
```

Remember: amounts are in 6-decimal units (`1_000_000e6` = 1M tokens), and `MINT_RECEIVER_POLICY` is enforced even during bootstrap — mint before setting a restrictive mint policy, or mint to an allowlisted recipient.

## Typical stablecoin configuration

Regulated issuers usually want, in initCalls (in this order):

1. Role grants — minter (issuance backend), burnBlocker (compliance), pauser/unpauser (incident response)
2. Initial mint (if any)
3. `TRANSFER_SENDER_POLICY` and `TRANSFER_RECEIVER_POLICY` → a BLOCKLIST policy they administer (sanctions screening)
4. `MINT_RECEIVER_POLICY` → an ALLOWLIST of custodial addresses

The blocklist + `BURN_BLOCKED_ROLE` combination is the freeze-and-seize path: `burnBlocked` only works against accounts denied by `TRANSFER_SENDER_POLICY`. See [policies-and-roles.md](policies-and-roles.md).
