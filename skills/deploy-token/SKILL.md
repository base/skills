---
name: b20-token-creator
description: Create and deploy B20 tokens — Base's native ERC-20 superset — via the IB20Factory precompile using base-std. Use this skill whenever the user wants to create, deploy, scaffold, or launch a token, stablecoin, or tokenized asset on Base (or mentions B20, base-std, IB20Factory, createB20, or initCalls), even if they call it an "ERC-20" or don't name B20 explicitly. Covers variant selection (Asset vs Stablecoin), factory create params, bootstrap initCalls (roles, policies, supply caps, initial mints), PolicyRegistry setup, Foundry deploy scripts, and tests against the base-std mocks.
---

# Creating B20 Tokens

B20 is Base's ERC-20 superset: role-based access control, pluggable transfer/mint policies, granular pausing, supply caps, memos, and ERC-2612 permit — all built in.

**The most important thing to internalize: you do not write a token contract.** Every B20 is created by calling the singleton factory precompile (`IB20Factory` at `0xB20f000000000000000000000000000000000000`) with encoded parameters. There is no contract to inherit, no OpenZeppelin ERC20 to extend, no token bytecode to deploy. If you find yourself scaffolding a `contract MyToken is ERC20`, stop — that is the wrong path for a B20. The deliverable is a Foundry script that calls `createB20`, plus a test that verifies the resulting configuration.

## Workflow

1. **Gather requirements** — resolve the checklist below from the user's request; ask only about choices that change on-chain behavior irreversibly (variant, decimals, currency, admin model).
2. **Set up the project** — install `base-std`, add remappings.
3. **Write the creation script** — encode params with `B20FactoryLib`, assemble `initCalls` in a valid order, call `createB20`.
4. **Write a test** — against the bundled precompile mocks, verifying every piece of requested configuration.
5. **Verify** — `forge build` and `forge test` must pass before you present the result.

## Step 1: Requirements checklist

| Decision | Options | Notes |
|---|---|---|
| Variant | `ASSET` or `STABLECOIN` | See below. **Immutable.** |
| Name / symbol | any strings | Updatable later by `METADATA_ROLE` |
| Initial admin | address or `address(0)` | `address(0)` = permanently admin-less — see warning |
| Decimals (Asset only) | 6–18 | **Immutable.** Stablecoin is fixed at 6 |
| Currency (Stablecoin only) | uppercase A–Z, e.g. `"USD"` | **Immutable**, required, self-declared |
| Role holders | minter, burner, pauser, … | See [references/policies-and-roles.md](references/policies-and-roles.md) |
| Policies | per-scope allowlist/blocklist | Default: everything open (`ALWAYS_ALLOW`) |
| Supply cap | uint256 | Default: uncapped (`type(uint256).max`) |
| Initial mint | recipients + amounts | Ordering matters — see Step 3 |
| Salt | any bytes32 | Determines the token address |

**Choosing the variant**: `STABLECOIN` is the fiat-backed carveout — fixed 6 decimals, immutable currency code. `ASSET` is everything else — configurable decimals, plus multiplier/rebasing, announcements, batch mint, and extra metadata. Details: [references/asset.md](references/asset.md), [references/stablecoin.md](references/stablecoin.md).

**Admin-less warning**: `initialAdmin = address(0)` never grants `DEFAULT_ADMIN_ROLE`; all admin-gated configuration must then happen inside `initCalls` and is frozen forever after creation (roles granted in `initCalls` keep working, but nothing new can be granted or changed). Confirm the user really wants this before proceeding.

## Step 2: Project setup

```bash
forge install base/base-std
```

Add remappings (in `foundry.toml` or `remappings.txt`). The `base-std-test/` remapping is required — the bundled test mocks import themselves via that prefix:

```toml
remappings = [
    "base-std/=lib/base-std/src/",
    "base-std-test/=lib/base-std/test/",
]
```

Everything you need is then importable:

- `base-std/StdPrecompiles.sol` — `StdPrecompiles.B20_FACTORY`, `.POLICY_REGISTRY`, `.ACTIVATION_REGISTRY` handles
- `base-std/lib/B20FactoryLib.sol` — encoders for params and initCalls (use these; don't hand-encode)
- `base-std/lib/B20Constants.sol` — role and policy-scope constants
- `base-std/interfaces/IB20.sol`, `IB20Asset.sol`, `IB20Stablecoin.sol`, `IB20Factory.sol`, `IPolicyRegistry.sol`
- `base-std-test/lib/BaseTest.sol` — test base that etches all precompile mocks

## Step 3: The creation script

A complete example — capped Asset token, roles split across addresses, initial mint to a treasury:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script} from "forge-std/Script.sol";
import {StdPrecompiles} from "base-std/StdPrecompiles.sol";
import {B20Constants} from "base-std/lib/B20Constants.sol";
import {B20FactoryLib} from "base-std/lib/B20FactoryLib.sol";
import {IB20Factory} from "base-std/interfaces/IB20Factory.sol";

contract CreateMyToken is Script {
    function run() external returns (address token) {
        address admin = vm.envAddress("TOKEN_ADMIN");
        address minter = vm.envAddress("TOKEN_MINTER");
        address treasury = vm.envAddress("TOKEN_TREASURY");

        // Role grants: address(0) slots are skipped automatically.
        bytes[] memory roleGrants = B20FactoryLib.buildRoleGrants(
            B20FactoryLib.B20AssetRoleHolders({
                minter: minter,
                burner: address(0),
                burnBlocker: address(0),
                pauser: admin,
                unpauser: admin,
                metadataAdmin: address(0),
                operator: address(0)
            })
        );

        // Initial mint, then the cap. Both execute inside the bootstrap window.
        address[] memory recipients = new address[](1);
        recipients[0] = treasury;
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = 100_000e18;

        bytes[] memory rest = new bytes[](2);
        rest[0] = B20FactoryLib.encodeBatchMint(recipients, amounts);
        rest[1] = B20FactoryLib.encodeUpdateSupplyCap(1_000_000e18);

        bytes[] memory initCalls = B20FactoryLib.concat(roleGrants, rest);

        vm.startBroadcast();
        token = StdPrecompiles.B20_FACTORY.createB20(
            IB20Factory.B20Variant.ASSET,
            keccak256("my-token-v1"), // salt: pick per token; reuse reverts TokenAlreadyExists
            B20FactoryLib.encodeAssetCreateParams("My Token", "MYT", admin, 18),
            initCalls
        );
        vm.stopBroadcast();
    }
}
```

For a Stablecoin, the differences are: `B20Variant.STABLECOIN`, `encodeStablecoinCreateParams(name, symbol, admin, "USD")`, the smaller `B20RoleHolders` struct (no `operator`), and initial mints encoded manually as `abi.encodeCall(IB20.mint, (to, amount))` — `batchMint` is Asset-only. See [references/stablecoin.md](references/stablecoin.md).

### How initCalls work, and how to order them

Each entry in `initCalls` is an ABI-encoded call dispatched on the new token inside the creation transaction's *bootstrap window*. During the window, factory-originated calls bypass the token's role gates and the transfer-side policy gates — so the script can grant roles, set policies, and mint without the deployer holding any role. The bypass is deliberately **not** total, which makes ordering matter:

- **`MINT_RECEIVER_POLICY` is always enforced, even during bootstrap.** If you set a restrictive mint-receiver policy and then mint to a recipient that policy denies, the whole `createB20` reverts. Sequence mints *before* the restrictive policy, or mint only to recipients on the policy's list.
- **Pause is never bypassed.** A start-paused token must place its `pause(...)` call *last* — pausing earlier would block subsequent bootstrap mints/transfers.
- **Supply-cap math is never bypassed.** A mint that exceeds an already-set cap reverts; mint first or keep amounts consistent.
- **Any policy ID you reference must already exist.** `updatePolicy` validates `policyExists(policyId)`, so policies must be created in the PolicyRegistry *before* `createB20` runs (it's fine to do it earlier in the same script and pass the returned `uint64` ID). See [references/policies-and-roles.md](references/policies-and-roles.md) for creating policies.

A safe default ordering: role grants → mints → supply cap → policies → metadata → pause (if any).

### Addresses are deterministic

The token address derives from `(variant, msg.sender, salt)` — `msg.sender` being whoever calls `createB20` (in a broadcast script, the broadcasting EOA). Predict it with `factory.getB20Address(variant, deployer, salt)`; check provenance with `isB20(addr)` and creation completion with `isB20Initialized(addr)`. `TokenAlreadyExists` means that `(variant, sender, salt)` tuple was already used — pick a new salt.

## Step 4: The test

Write a Foundry test that inherits `BaseTest` from `base-std-test/lib/BaseTest.sol`. It etches fully-functional mocks of all three precompiles at their canonical addresses and activates the B20 features, so `createB20` works in plain `forge test` with no fork. Assert every piece of configuration the user asked for — name/symbol/decimals/currency, `hasRole` for each role holder, `policyId(scope)` for each policy, `supplyCap()`, balances from initial mints — and exercise at least one behavior (e.g. minter can mint, blocked account can't receive). Full patterns, including how to reuse the script from the test and fork-mode notes: [references/testing.md](references/testing.md).

## Step 5: Verify

Run `forge build` and `forge test` and fix what fails before presenting results. Common reverts and what they mean:

| Revert | Cause |
|---|---|
| `FeatureNotActivated` | Variant not activated on this chain (Base team controls activation; mocks activate everything) |
| `TokenAlreadyExists` | Salt reuse — pick a different salt |
| `InvalidDecimals` | Asset decimals outside 6–18 |
| `InvalidCurrency` / `MissingRequiredField` | Stablecoin currency empty or not uppercase A–Z |
| `InitCallFailed(i)` / bubbled inner revert | initCall `i` reverted — check ordering rules above |
| `PolicyForbids(MINT_RECEIVER_POLICY, …)` | Bootstrap mint to a policy-denied recipient — reorder |

## Reference files

- [references/asset.md](references/asset.md) — Asset variant: decimals, multiplier/rebasing, announcements, batch mint, extra metadata, `OPERATOR_ROLE`
- [references/stablecoin.md](references/stablecoin.md) — Stablecoin variant: currency codes, fixed decimals, initial mint pattern
- [references/policies-and-roles.md](references/policies-and-roles.md) — the seven roles, four policy scopes, creating PolicyRegistry policies, admin lifecycle
- [references/testing.md](references/testing.md) — test patterns with the bundled mocks, full example test, fork testing
