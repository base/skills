---
name: account-policies
description: Design account policies for Base Account integrations. Covers paymaster sponsorship allowlists, spend permission guardrails, subscription policy templates, and app-level validation. Use when asked about gas sponsorship rules, recurring payment guardrails, policy validation logic, allowlists, spend limits, or structuring rules for subscriptions, payouts, or automation on Base. Trigger phrases include "account policy", "paymaster policy", "sponsorship rules", "spend permissions guardrails", "subscription policy template", "recurring payment guardrails", "policies for Base", "Base account policy design", "gas sponsorship allowlist", "app policy", or "payment guardrails".
---

# Account Policies

Account policies are the rules that govern what a Base Account can do on behalf of a user. This skill helps you design those rules — it does not run policies; it guides the reasoning that produces good policy design.

Three core domains: **gas sponsorship**, **spend permissions**, and **recurring charge limits**. Each has different stakes and different defaults.

## When to Use This Skill

Use this skill when a developer asks to:
- "Help me define account policies for my Base app"
- "What should my paymaster sponsorship policy allow?"
- "How do I write spend permission guardrails?"
- "What are safe default policies for recurring payments?"
- "How should I structure policy rules for subscriptions, payouts, or gas sponsorship?"
- "Give me sample policy scenarios for Base Account"

Also use proactively when a developer describes a product flow that involves gas sponsorship, recurring USDC charges, or automated spend — ask about policy design before implementing.

## Policy Design Checklist

Copy and use this checklist:

```
Account Policy Design:
- [ ] Step 1: Identify the product scenario (SaaS, checkout, automation, marketplace, team app)
- [ ] Step 2: Determine which policy types apply (gas, spend, subscriptions — may be multiple)
- [ ] Step 3: Choose a starting template from Section 5
- [ ] Step 4: Customize limits, allowlists, and validation rules for the use case
- [ ] Step 5: Review security guardrails (Section 7)
- [ ] Step 6: Check for common mistakes (Section 8)
- [ ] Step 7: Confirm with user before implementing
```

## Policy Type Reference

| Policy Type | Reference | When to Read |
|-------------|-----------|--------------|
| Paymaster / Gas Sponsorship | [references/paymaster-policies.md](references/paymaster-policies.md) | Allowlists, ERC-7677 configuration, gas budgets, conditional sponsorship |
| Spend Permissions | [references/spend-permissions.md](references/spend-permissions.md) | One-time and recurring spend limits, approval scopes, revocation patterns |
| Subscription Guardrails | [references/subscription-guardrails.md](references/subscription-guardrails.md) | Recurring charge limits, period resets, idempotency, cancellation flows |
| Advanced Policy Validation | [references/policy-validation.md](references/policy-validation.md) | Size limits, offchain vs. onchain checks, policy change audits, retrofits |
| Real-World Scenarios | [references/scenarios.md](references/scenarios.md) | Full writeups for 5 product types |

## Questions to Ask Before Proposing a Policy

Ask these before writing a single rule:

1. Is this a one-time spend, recurring charge, or open-ended automation?
2. What is the maximum USDC amount needed in one transaction? In one period?
3. Which smart contracts should the paymaster sponsor? Is the list closed or open-ended?
4. Who can update the policy — the user, the app operator, or both?
5. What happens if the user revokes permission mid-transaction?
6. Should gas sponsorship be conditional on transaction success or unconditional?
7. Does the app need cross-chain policy enforcement or is Base-only sufficient?
8. Is there an existing offchain subscription system being migrated, or is this greenfield?
9. What is the expected transaction volume per day / per week?
10. Are there compliance requirements that affect policy scope (geo-restrictions, KYC)?

## Safe Default Templates

### Gas Sponsorship Defaults

Default: **deny, explicit allowlist only**. Sponsor only calls to known, necessary contracts via the paymasterService capability (ERC-7677).

```
Policy pseudocode (illustrative — verify against current SDK):
  # At the paymaster configuration level:
  # Only sponsor calls to known contracts
  sponsored_call_targets = [
    USDC_contract,
    app_primary_contract,
    known_dex_addresses,
    known_bridge_addresses,
  ]
  # Set a gas budget cap at the paymaster service level:
  max_gas_per_tx = 200000      # configure per paymaster provider
  max_sponsored_tx_per_user_per_day = 10
```

Never sponsor arbitrary ERC-20 transfers or unknown contract calls. If the call target list grows beyond ~10 entries, the policy is too loose — revisit.

Start with the minimum set, expand as the app matures. Use conditional sponsorship (first N transactions free, then evaluate) for new users. Configure these limits via your CDP paymaster dashboard, not hardcoded in the app.

### Spend Permission Defaults

Default: **least privilege, shortest duration**. Only the amount and contract that is actually needed.

```
Policy pseudocode (illustrative — verify against current SDK):
  max_amount = "100"  # USDC string, capped at order total
  allowed_contract = specific_known_address
  revocable = true
  # Use shortest viable duration — one-time charges should
  # revoke immediately after confirmation
```

For subscriptions, set a `max_per_period` to prevent `remainingChargeInPeriod` accumulation from exceeding the expected periodic charge. Verify the exact field name for per-period limits in docs.base.org/llms.txt.

Never set spend permission to unlimited USDC or to an unscoped contract address.

### Subscription Defaults

Default: **bounded, cancellable, idempotent**. Charge only during an active period, track transaction IDs, allow immediate cancellation.

```
Policy pseudocode (illustrative — verify against current SDK):
  # Use SDK's native recurring charge fields:
  recurringCharge = "9.99"   # confirmed: SDK field name
  periodInDays = 30            # confirmed: SDK field name
  subscriptionOwner = cdp_wallet  # confirmed: server-side only
  # Add app-layer bounds the SDK does not enforce natively:
  max_per_period = "9.99"      # app-layer cap to prevent overcharge
  idempotency_key = tx_id     # track to prevent double-charge on retry
  require_balance = true       # but check auxiliaryFunds capability first
  cancellation = immediate     # revoke() is immediate per SDK behavior
```

Use `auxiliaryFunds` to skip balance checks — the wallet may have Coinbase balances onchain that are not reflected in visible balance.

The SDK's `remainingChargeInPeriod` field accumulates charges within a period. Set an explicit `max_per_period` at the app layer to bound this.

### Admin / Internal Tool Defaults

Internal tooling has higher trust but still needs limits. Default: **per-member caps, no cross-member transfers, visible audit trail**.

```
Policy pseudocode (illustrative — verify against current SDK):
  # App-layer spend tracking per member:
  max_spend_per_member_per_month = "500"  # USDC string
  # Gas budget via CDP paymaster dashboard, not SDK fields:
  max_gas_per_member_per_month = configured_in_cdp_dashboard
  allowed_contract = app_admin_contract_only  # app-layer constraint
  cross_member_transfer = false  # verify wallet contract behavior
  policy_change_audited = true  # implement at key-management layer
```

These are app-layer constraints. The SDK's native spend permissions do not expose per-member monthly caps — implement that tracking in your application layer.

## Scenario Examples

### 1. Subscription SaaS — $9.99/mo USDC subscription

**Product**: User pays $9.99/mo to access a service. App charges via Spend Permissions.

**Policy**:
- `recurringCharge`: "9.99" — SDK confirmed field name
- `periodInDays`: 30 — SDK confirmed field name
- `subscriptionOwner`: CDP wallet address (server-side only, never exposed client-side)
- `allowedContract`: USDC contract only (app-layer constraint — SDK does not enforce contract-level scoping natively)
- App-layer `max_per_period`: "9.99" — to bound `remainingChargeInPeriod` accumulation
- `cancellation`: immediate via `revoke()` (SDK confirmed behavior)
- `idempotency`: track subscription ID + charge attempt to prevent double-charge on network retry

**Why this works**: Amount is fixed, period is bounded, revocation is immediate. The app cannot overcharge because the permission is per-period capped.

### 2. Consumer Checkout — one-time USDC payment

**Product**: User buys a $25 product. Single charge, no subscription.

**Policy**:
- Spend permission with amount capped at order total
- `allowedContract`: app payment contract only
- `revocable`: true
- Use `base.subscription.subscribe()` with a high `periodInDays` and immediately revoke after charge — this approximates a one-time approval without a native one-time-use concept in the SDK

**Why this works**: The app controls the amount via the subscription charge call, scoped to the payment contract. Immediate revocation after successful charge ensures the permission does not persist.

Do not use field names like `oneTimeUse` or `expiry` — the SDK does not expose these directly. If the SDK adds a one-time spend permission type, verify against docs before using.

### 3. Trading Bot — automated DEX + bridge spending

**Product**: A bot executes trades on behalf of a user. Open-ended, potentially frequent transactions.

**Policy**:
- Spend permission scoped to DEX + bridge contract addresses
- `maxPerDay`: "500" (rolling daily limit)
- `maxPerWeek`: "2000" (rolling weekly cap)
- Gas sponsorship: conditional via paymasterService capability — first N transactions sponsored per month, then user pays — configure via CDP paymaster dashboard
- Policy survives key rotation (smart wallet, not EOA)
- `revocable`: true (user can cancel at any time)

**Why this works**: Separate daily and weekly caps prevent runaway spend while allowing normal usage. Conditional gas sponsorship via paymaster avoids abuse without blocking legitimate activity.

### 4. Internal Team App — per-member spend caps

**Product**: A team of 10 uses sub-accounts to interact with a shared internal tool. Company sponsors gas.

**Policy**:
- Per-member spend cap: "200" USDC/month — configure via app-layer tracking
- Per-member gas cap: set via CDP paymaster dashboard (not a field in the SDK)
- `allowedContract`: app contract only (app-layer constraint)
- Cross-member transfers: disabled at the smart contract level — verify current wallet behavior
- Policy changes: require multi-sig (not single admin) — implement at the admin/key-management layer
- Gas sponsorship: use CDP paymaster with per-member budget limits configured in the CDP dashboard

**Why this works**: Caps are per-member not aggregate — one member's spend does not affect another's. Multi-sig on policy changes prevents a single compromised key from raising all caps at once.

### 5. Marketplace — seller payout on delivery milestone

**Product**: Buyer locks USDC, released to seller when delivery is confirmed (oracle or offchain sign-off).

**Policy**:
- Buyer's spend permission: amount + seller address + conditional release
- Use a time-bounded escrow pattern: set a reasonable lock duration (e.g., 30 days), after which the app should release or refund
- Cancellation: buyer can cancel before the release condition is met
- Gas sponsorship: buyer pays (or app sponsors if acquiring new users)

**Why this works**: Conditional release means the app cannot rug the buyer — the oracle or authorized offchain signal gates the release. Time-bounded lock prevents funds from being stuck indefinitely.

The specific field names for conditional release and lock duration depend on the current Spend Permissions API — verify against docs.base.org/llms.txt before implementing escrow logic.

## Red Flags

Patterns that should trigger a warning from the agent:

- **Unlimited USDC spend permission** to an unscoped contract — never propose this
- **Open-ended allowlist** for paymaster sponsorship (more than ~10 entries) — default deny, explicit allow only
- **No transaction ID tracking** on subscription charges — retry on network failure = double charge without idempotency
- **Offchain policy validation** when onchain validation is available — the SDK has native enforcement
- **Missing `auxiliaryFunds` check** before showing "insufficient funds" — wallet may have Coinbase balances
- **Sponsoring arbitrary ERC-20 transfers** — only sponsor known, necessary contracts
- **Single-admin policy changes** for high-value permissions — use multi-sig for admin-level policy changes
- **No gas budget cap** on sponsorship — a malicious or buggy app can drain the paymaster budget
- **Retrofitting policies** without accounting for existing user permission state — audit first
- **Denylist for paymaster** instead of allowlist — ERC-7677 compliance requires allowlists

## What Not to Promise

Do not claim or imply the following without verifying against current SDK docs:

- Any specific SDK method name that has not been confirmed in `docs.base.org/llms.txt` or `docs.base.org/base-account`
- Gas sponsorship rules that apply universally across all paymaster providers
- Policy enforcement that works identically across EOA and smart wallet contexts
- Cross-chain policy enforcement that is not documented in the Base Account reference
- Spend permission limits that reset in a specific way without confirming the current SDK behavior
- Specific error codes or status values for policy-related failures

**When in doubt**: say "the current SDK docs indicate X — verify before implementing" rather than asserting a behavior that may have changed.

## Verifying Against Official Docs

Base Account capabilities evolve. Before proposing specific SDK calls or configuration values, always check:

- **AI-optimized docs**: [docs.base.org/llms.txt](https://docs.base.org/llms.txt)
- **Base Account reference**: [docs.base.org/base-account](https://docs.base.org/base-account)
- **Spend Permissions contracts**: [github.com/coinbase/spend-permissions](https://github.com/coinbase/spend-permissions)
- **Base Gasless Campaign**: [docs.base.org/base-account/more/base-gasless-campaign](https://docs.base.org/base-account/more/base-gasless-campaign)
- **Coinbase Developer Platform**: [portal.cdp.coinbase.com](https://portal.cdp.coinbase.com)
- **Smart Wallet source**: [github.com/coinbase/smart-wallet](https://github.com/coinbase/smart-wallet)

Code examples in this skill and its references are policy-logic illustrations unless explicitly labeled as confirmed SDK calls.