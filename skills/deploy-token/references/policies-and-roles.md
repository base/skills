# B20 Roles and Policies

## Roles

B20 uses OZ-style AccessControl with a fixed enforced taxonomy (constants in `base-std/lib/B20Constants.sol`):

| Role | Gates |
|---|---|
| `DEFAULT_ADMIN_ROLE` (`bytes32(0)`) | role grants/revokes, `updatePolicy`, `updateSupplyCap` |
| `MINT_ROLE` | `mint`, `mintWithMemo` (+ `batchMint` on Asset) |
| `BURN_ROLE` | self-burns: `burn`, `burnWithMemo` |
| `BURN_BLOCKED_ROLE` | `burnBlocked` — third-party burn, **only** against accounts denied by `TRANSFER_SENDER_POLICY` (freeze-and-seize) |
| `PAUSE_ROLE` / `UNPAUSE_ROLE` | `pause` / `unpause` — separate by design so incident responders can halt without being able to re-enable |
| `METADATA_ROLE` | `updateName`, `updateSymbol`, `updateContractURI` (+ `updateExtraMetadata` on Asset) |
| `OPERATOR_ROLE` (Asset only) | `updateMultiplier`, `announce` |

Custom roles via `setRoleAdmin`/`grantRole` are allowed but gate nothing built-in.

**Admin lifecycle gotchas:**
- The last `DEFAULT_ADMIN_ROLE` holder cannot `renounceRole`/`revokeRole` themselves out (`LastAdminCannotRenounce`); the only path to admin-less is the explicit `renounceLastAdmin()`.
- Once admin-less (or created with `initialAdmin = address(0)`), admin operations are *permanently* dead — no resurrection through custom role-admin chains. Already-granted operational roles keep working.

## Policy scopes

B20 has four policy slots; each stores a `uint64` PolicyRegistry ID checked on every gated operation (revert: `PolicyForbids`):

| Scope | Checks |
|---|---|
| `TRANSFER_SENDER_POLICY` | `from` of `transfer`/`transferFrom` |
| `TRANSFER_RECEIVER_POLICY` | `to` of `transfer`/`transferFrom` |
| `TRANSFER_EXECUTOR_POLICY` | `msg.sender` of `transferFrom` only |
| `MINT_RECEIVER_POLICY` | `to` of `mint` — **enforced even during factory bootstrap** |

- **Every scope defaults to `ALWAYS_ALLOW` (ID `0`)** — an unconfigured B20 is fully open. Constrain intentionally.
- `approve` is never policy-gated; gates fire when balance moves.
- Read with `policyId(scope)`, write with `updatePolicy(scope, id)` (admin-gated, validates the scope and that the policy exists).

## The PolicyRegistry

Singleton precompile (`StdPrecompiles.POLICY_REGISTRY`) holding list-based policies. Two types:

- **`BLOCKLIST`** — allow by default, deny listed accounts (sanctions screening)
- **`ALLOWLIST`** — deny by default, allow listed accounts (KYC sets, custodian sets)

Built-in IDs usable without creating anything: `ALWAYS_ALLOW = 0` and `ALWAYS_BLOCK = (uint64(ALLOWLIST) << 56) | 1`. `ALWAYS_BLOCK` on `MINT_RECEIVER_POLICY` is a clean way to permanently disable minting.

**Creating a policy** (do this *before* `createB20` — the token's `updatePolicy` requires the ID to exist):

```solidity
import {IPolicyRegistry} from "base-std/interfaces/IPolicyRegistry.sol";
import {StdPrecompiles} from "base-std/StdPrecompiles.sol";

// empty policy, or seed members in the same call:
uint64 policyId = StdPrecompiles.POLICY_REGISTRY.createPolicyWithAccounts(
    policyAdmin, IPolicyRegistry.PolicyType.BLOCKLIST, initialMembers
);
```

**Membership updates** (policy admin only): `updateBlocklist(id, blocked, accounts)` / `updateAllowlist(id, allowed, accounts)` — use the call matching the policy's type, the other reverts `IncompatiblePolicyType`.

**Policy admin lifecycle**: two-step transfer (`stageUpdateAdmin` → `finalizeUpdateAdmin`; staging `address(0)` cancels); `renounceAdmin` freezes membership forever while the policy stays queryable.

**Why write-time validation matters**: `isAuthorized` never reverts on a bad ID — it collapses to empty-set semantics, so a typo'd BLOCKLIST ID silently behaves as `ALWAYS_ALLOW`. The token validates at `updatePolicy` time, which is why nonexistent IDs in initCalls make `createB20` revert.

**Activation note**: PolicyRegistry *writes* (createPolicy, membership updates) are gated by the ActivationRegistry; reads always work. In tests the mocks activate everything; on a live chain a `FeatureNotActivated` revert means the feature isn't switched on yet.
