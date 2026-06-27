# Policy Model (Compliance Allowlist/Blocklist)

## Table of Contents

- [PolicyRegistry](#policyregistry)
- [Policy Types](#policy-types)
- [Policy IDs](#policy-ids)
- [Creating and Managing a Policy](#creating-and-managing-a-policy)
- [The Four Policy Scopes B20 Enforces](#the-four-policy-scopes-b20-enforces)
- [The Default Everyone Misses](#the-default-everyone-misses)
- [Reading and Writing a Token's Scope Assignment](#reading-and-writing-a-tokens-scope-assignment)
- [Enforcement](#enforcement)
- [Setting a Policy at Deploy Time](#setting-a-policy-at-deploy-time)

## PolicyRegistry

A singleton precompile (`0x8453000000000000000000000000000000000002`) that manages
allowlists/blocklists independently of any specific token. **Any caller can create a policy and
nominate its admin** — policies aren't owned by B20 tokens, tokens just reference policy IDs.

State-changing functions (`createPolicy`, `updateBlocklist`, etc.) are gated by the
`ActivationRegistry`. Read functions — `isAuthorized`, `policyExists`, `policyAdmin`,
`pendingPolicyAdmin` — are always callable, even if the policy feature itself isn't activated.

## Policy Types

| Type | Default-state semantics |
|------|---|
| `BLOCKLIST` | All accounts **authorized** by default; explicitly listed accounts are **denied** |
| `ALLOWLIST` | All accounts **denied** by default; explicitly listed accounts are **authorized** |

## Policy IDs

A `uint64` encodes the type in the top byte and a global counter (starting at 2) in the low 56
bits — you don't construct these by hand except for the two built-in constants:

| Constant | ID | Behavior |
|----------|----|---|
| `ALWAYS_ALLOW` | `0` | Authorizes every account unconditionally. **This is the default scope value on every new B20 token.** |
| `ALWAYS_BLOCK` | `(uint64(ALLOWLIST) << 56) \| 1` | Denies every account unconditionally |

`isAuthorized` **never reverts** on a non-existent ID — a non-existent `BLOCKLIST` ID authorizes
everyone (consistent with the type's default-allow semantics); a non-existent `ALLOWLIST` ID
denies everyone.

## Creating and Managing a Policy

```solidity
uint64 policyId = policyRegistry.createPolicy(adminAddress, PolicyType.BLOCKLIST);
// or, seeded with initial members:
uint64 policyId = policyRegistry.createPolicyWithAccounts(adminAddress, PolicyType.BLOCKLIST, accounts);

policyRegistry.updateBlocklist(policyId, /* blocked: */ true, accounts);
policyRegistry.updateBlocklist(policyId, /* blocked: */ false, accounts); // unblock
// ALLOWLIST equivalent:
policyRegistry.updateAllowlist(policyId, /* allowed: */ true, accounts);
```

### Two-Step Admin Transfer

```solidity
policyRegistry.stageUpdateAdmin(policyId, newAdmin);   // called by current admin
policyRegistry.finalizeUpdateAdmin(policyId);          // called by the new (pending) admin
```

### Freezing a Policy Forever

```solidity
policyRegistry.renounceAdmin(policyId); // membership can never be changed again, irreversible
```

### PolicyRegistry-Level Errors

Distinct from the B20-token-level `PolicyNotFound(uint64)`/`UnsupportedPolicyType(bytes32)` in
[errors.md](errors.md) — these come from the registry itself when managing policies directly:

| Error | Cause |
|-------|-------|
| `PolicyNotFound()` | Referenced `policyId` doesn't exist (no args — unlike the B20-level error of the same name) |
| `IncompatiblePolicyType()` | Called `updateAllowlist` on a BLOCKLIST policy, or `updateBlocklist` on an ALLOWLIST policy |
| `Unauthorized()` | Caller isn't the policy's current admin |
| `ZeroAddress()` | Passed `address(0)` as `admin` to `createPolicy`/`createPolicyWithAccounts` |
| `BatchSizeTooLarge(uint256 maxBatchSize)` | `accounts` array exceeds the registry's per-call limit |
| `NoPendingAdmin()` | Called `finalizeUpdateAdmin` with no transfer staged |

## The Four Policy Scopes B20 Enforces

| Scope | Gates |
|-------|---|
| `TRANSFER_SENDER_POLICY` | The `from` of `transfer` / `transferFrom` |
| `TRANSFER_RECEIVER_POLICY` | The `to` of `transfer` / `transferFrom` |
| `TRANSFER_EXECUTOR_POLICY` | The `msg.sender` of `transferFrom`, when distinct from `from` |
| `MINT_RECEIVER_POLICY` | The `to` of `mint` |

**`approve` is not policy-gated** — only actual balance movement (`transfer`/`transferFrom`/`mint`)
is checked. Approving a denied address is allowed; that address's subsequent attempt to move funds
is what gets blocked.

## The Default Everyone Misses

> **Every scope defaults to `ALWAYS_ALLOW` at token creation unless overridden in the bootstrap
> `initCalls`. An unattended B20 deployment is fully open** — no compliance gating happens unless
> you explicitly wire it up.

If a user asks for a "compliant" or "regulated" token and you deploy without setting any policy
scopes, you've shipped an open token that happens to support compliance features — not a
compliant token. Confirm with the user whether they actually need policy gating before assuming
the defaults are fine.

## Reading and Writing a Token's Scope Assignment

```solidity
function policyId(bytes32 scope) external view returns (uint64);
function updatePolicy(bytes32 scope, uint64 newPolicyId) external; // admin-gated
```

`updatePolicy` reverts if `scope` isn't one of the four recognized constants above.

## Enforcement

On every gated operation, B20 calls `isAuthorized` against the relevant scope's currently-assigned
policy and **reverts `PolicyForbids(scope, policyId)`** if the account isn't authorized. This is
not a bug when it happens — it's the issuer's own configured compliance rule firing as designed.
See [post-deploy.md](post-deploy.md) for the related `burnBlocked` freeze-and-seize mechanic, which
specifically requires the target to already be denied under `TRANSFER_SENDER_POLICY`.

## Setting a Policy at Deploy Time

Bootstrap it via `initCalls` so the token is never open even momentarily:

```solidity
bytes[] memory initCalls = new bytes[](3);
initCalls[0] = B20FactoryLib.encodeGrantRole(B20Constants.MINT_ROLE, account);
initCalls[1] = B20FactoryLib.encodeUpdateSupplyCap(type(uint128).max);
initCalls[2] = B20FactoryLib.encodeUpdatePolicy(B20Constants.TRANSFER_SENDER_POLICY, myBlocklistPolicyId);
```

Note the policy itself must already exist (created via `PolicyRegistry.createPolicy` beforehand) —
`initCalls` only *assigns* an existing policy ID to a scope, it doesn't create policies.
