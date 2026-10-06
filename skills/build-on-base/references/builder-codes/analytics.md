# User Analytics

Add product analytics to an app on Base so the builder can track users, retention and funnels keyed by wallet address. Builder Codes attribute onchain transactions to the app; Base does not provide per-app user, retention or funnel analytics, so builders track these in their own analytics tool.

## Contents

- [When to Use](#when-to-use)
- [Prerequisites](#prerequisites)
- [Workflow](#workflow)
- [Step 1: Detect the Wallet Framework](#step-1-detect-the-wallet-framework)
- [Step 2: Choose the Analytics Provider](#step-2-choose-the-analytics-provider)
- [Step 3: Install and Initialize](#step-3-install-and-initialize)
- [Step 4: Identify Users by Wallet Address](#step-4-identify-users-by-wallet-address)
- [Step 5: Capture Events](#step-5-capture-events)
- [Step 6: Verify and Hand Off](#step-6-verify-and-hand-off)
- [Guardrails](#guardrails)

## When to Use

Use when a developer asks to:

- "Add analytics to my app"
- "Track my users / DAU / retention / funnels"
- "How many users does my app on Base have?"
- "Base Dashboard no longer shows my users or transactions"
- Recreate user metrics that used to be shown in Base Dashboard

## Prerequisites

- A web app with a wallet connection
- An account and project key with the chosen analytics provider (PostHog free tier by default)

## Workflow

Copy this checklist and track progress:

```
User Analytics:
- [ ] Step 1: Detect the wallet framework
- [ ] Step 2: Choose the analytics provider (confirm with user)
- [ ] Step 3: Install and initialize client-side
- [ ] Step 4: Identify users by wallet address
- [ ] Step 5: Capture app and transaction events
- [ ] Step 6: Verify events and hand off
```

## Step 1: Detect the Wallet Framework

Use the detection steps in [overview.md](overview.md#framework-detection-required-first-step) to classify the app as `privy`, `wagmi`, `viem` or `rpc`. The framework decides how wallet connects are detected in Step 4.

While you are in the code, check that the app appends its Builder Code to transactions. If it does not, offer to add it using [overview.md](overview.md); onchain activity without the suffix is not attributed to the app.

## Step 2: Choose the Analytics Provider

Default to PostHog (free tier, supports autocapture, identity and funnels). Confirm with the user:

> "I'll add analytics with PostHog. Want a different provider, such as Mixpanel, Amplitude or Plausible?"

| Provider | Package | Identify | Capture | Reset |
|---|---|---|---|---|
| PostHog | `posthog-js` | `posthog.identify(id)` | `posthog.capture(name, props)` | `posthog.reset()` |
| Mixpanel | `mixpanel-browser` | `mixpanel.identify(id)` | `mixpanel.track(name, props)` | `mixpanel.reset()` |
| Amplitude | `@amplitude/analytics-browser` | `amplitude.setUserId(id)` | `amplitude.track(name, props)` | `amplitude.reset()` |
| Plausible | script tag or `@plausible-analytics/tracker` | Not supported | `plausible(name, { props })` | Not needed |

Plausible has no per-user identity, so wallet-based retention and cohorts are not available. Skip Step 4 if the user picks it.

## Step 3: Install and Initialize

Install the provider SDK and initialize it **once, client-side only**, at app startup. Read keys from public env vars using the framework's convention and skip init when the key is missing.

```bash
npm install posthog-js
```

```typescript
// src/lib/analytics.ts
import posthog from "posthog-js";

const key = process.env.NEXT_PUBLIC_POSTHOG_KEY; // VITE_POSTHOG_KEY via import.meta.env in Vite

export function initAnalytics() {
  if (typeof window === "undefined" || !key) return;
  posthog.init(key, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://us.i.posthog.com",
    autocapture: true,
    capture_pageview: "history_change", // count client-side route changes as page views
  });
}

export { posthog };
```

Add the env var names to `.env.example`. Never commit real values.

## Step 4: Identify Users by Wallet Address

Identify with the **lowercased** wallet address on connect and reset on disconnect. Only reset after a wallet was identified, otherwise every anonymous page load starts a new user.

### Wagmi

```tsx
import { useAccountEffect } from "wagmi";
import { posthog } from "@/lib/analytics";

export function AnalyticsIdentity() {
  useAccountEffect({
    onConnect({ address, connector, chainId, isReconnected }) {
      posthog.identify(address.toLowerCase());
      // Also fires when a wallet reconnects on page load; count new connects only
      if (!isReconnected) {
        posthog.capture("wallet_connected", { connector: connector.name, chain_id: chainId });
      }
    },
    onDisconnect() {
      posthog.reset();
    },
  });
  return null;
}
```

### Privy

```tsx
import { useEffect, useRef } from "react";
import { usePrivy } from "@privy-io/react-auth";
import { posthog } from "@/lib/analytics";

export function AnalyticsIdentity() {
  const { ready, authenticated, user } = usePrivy();
  const identified = useRef<string | null>(null);
  const address = user?.wallet?.address?.toLowerCase();

  useEffect(() => {
    if (!ready) return;
    if (authenticated && address && identified.current !== address) {
      posthog.identify(address);
      posthog.capture("wallet_connected", { connector: user?.wallet?.walletClientType });
      identified.current = address;
    } else if (!authenticated && identified.current) {
      posthog.reset();
      identified.current = null;
    }
  }, [ready, authenticated, address]);

  return null;
}
```

### Viem or Standard RPC

Listen to the EIP-1193 provider:

```typescript
let identified: string | null = null;

window.ethereum?.on("accountsChanged", (accounts: string[]) => {
  const address = accounts[0]?.toLowerCase();
  if (address && address !== identified) {
    posthog.identify(address);
    posthog.capture("wallet_connected", { connector: "injected" });
    identified = address;
  } else if (!address && identified) {
    posthog.reset();
    identified = null;
  }
});
```

Also identify right after the app's own `eth_requestAccounts` call succeeds.

## Step 5: Capture Events

| Event | Properties | When |
|---|---|---|
| `app_opened` | `referrer`, `utm_source`, `utm_medium`, `utm_campaign` | Once per session at startup |
| `wallet_connected` | `connector`, `chain_id` | On connect (Step 4) |
| `tx_submitted` | `action`, `tx_hash` | When the wallet returns a hash |
| `tx_confirmed` | `action`, `tx_hash` | After the receipt confirms with status success |
| `tx_failed` | `action`, `error_message` | When the user rejects, the call errors or the receipt reverts |

Name `action` after what the app does (for example `mint`, `swap`, `deposit`). Use the call-site searches in [overview.md](overview.md#finding-transaction-call-sites) to find where transactions are sent, and wait for the receipt with the framework's helper (`useWaitForTransactionReceipt` in Wagmi, `waitForTransactionReceipt` in Viem, `tx.wait()` in ethers). Treat a receipt as successful only when `status` is `"success"` (Viem/Wagmi) or `1` (ethers).

## Step 6: Verify and Hand Off

1. Run the app, connect a wallet and send a test transaction
2. Confirm `app_opened`, `wallet_connected`, `tx_submitted` and `tx_confirmed` appear in the provider's live events view, attributed to the lowercased wallet address
3. Summarize every file changed, the env vars to set, and how to view live events
4. Suggest three starter dashboards:
   - **Growth:** daily, weekly and monthly active users, new vs. returning wallets
   - **Retention:** D1, D7 and D30 cohorts by the week a wallet was first seen
   - **Funnel:** `app_opened` → `wallet_connected` → `tx_confirmed`, split by `utm_source`

## Guardrails

- **Wallet address is the only user identifier** — never capture emails, names, government IDs or payment details
- **Never commit analytics keys** — use public env vars and list names in `.env.example`
- **Initialize client-side only** — guard against server-side rendering
- **Do not modify Builder Code attribution** — analytics must not change `dataSuffix` config or transaction calldata
