# User Analytics

Help a builder track users, retention and conversion for their app on Base, keyed by wallet address. Builder Codes attribute onchain transactions to the app; Base does not provide per-app user, retention or funnel analytics, so builders track these in the analytics stack of their choice. This reference describes what to measure and where each signal comes from. How it is wired up is up to the builder.

## When to Use

Use when a developer asks to:

- "Add analytics to my app"
- "Track my users / DAU / retention / funnels"
- "How many users does my app on Base have?"
- "Base Dashboard no longer shows my users or transactions"
- Recreate user metrics that used to be shown in Base Dashboard

## Prerequisites

- A web app with a wallet connection
- An analytics stack chosen by the builder

## Workflow

Copy this checklist and track progress:

```
User Analytics:
- [ ] Step 1: Confirm the analytics stack and Builder Code attribution
- [ ] Step 2: Identify users by wallet address
- [ ] Step 3: Record key moments in the user journey
- [ ] Step 4: Use onchain data for transactions
- [ ] Step 5: Suggest dashboards and hand off
```

## Step 1: Confirm the Analytics Stack and Builder Code Attribution

Ask which analytics stack the builder uses, or wants to use, and follow that stack's own documentation for setup. Do not recommend or default to a specific tool; the builder decides.

Check that the app appends its Builder Code to transactions. If it does not, offer to add it using [overview.md](overview.md). The onchain signals in Step 4 depend on it.

## Step 2: Identify Users by Wallet Address

- Use the connected wallet address, **lowercased**, as the user identifier
- Set it when a wallet connects and clear it when the wallet disconnects
- Only clear identity after a wallet was identified, so anonymous visits are not split into many users
- Do not count a wallet that reconnects automatically on page load as a new connection

The same lowercased address is the join key between in-app activity and onchain activity.

## Step 3: Record Key Moments in the User Journey

| Moment | Useful context |
|---|---|
| App opened | Referrer and campaign source |
| Wallet connected | Chain ID |
| Transaction submitted | What it does in the app (for example mint, swap, deposit) and the transaction hash |

The transaction hash links an in-app submission to its onchain outcome in Step 4.

## Step 4: Use Onchain Data for Transactions

Onchain data is the source of truth for transaction outcomes. For each transaction, look at:

| Signal | What to check |
|---|---|
| Builder Code | The calldata ends with the app's ERC-8021 suffix (see Verify attribution in [overview.md](overview.md)) |
| Sender | The wallet address that sent it, which matches the user identifier from Step 2 |
| Status | Whether the transaction receipt shows success or a revert |

Count a transaction as successful only when its receipt status is success. Rejected or reverted transactions are drop-offs in the funnel.

## Step 5: Suggest Dashboards and Hand Off

Suggest three starter dashboards, described as journey stages so they work in any stack:

- **Growth:** daily, weekly and monthly active users, new vs. returning wallets
- **Retention:** D1, D7 and D30 cohorts by the week a wallet was first seen
- **Funnel:** open → connect → first successful transaction, split by referrer or campaign source

Then summarize every file changed and any configuration the builder must set. Suggest checking that a test wallet connection and transaction appear under the lowercased wallet address, and that the recorded outcome matches the transaction receipt.

## Guardrails

- **Wallet address is the only user identifier** — never capture emails, names, government IDs or payment details
- **Never commit analytics keys** — keep them in environment variables
- **Do not modify Builder Code attribution** — analytics must not change `dataSuffix` config or transaction calldata
