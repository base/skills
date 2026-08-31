---
title: "AgentFlow — wallet trust & sybil screening on Base"
description: "Before an agent transacts with, trades against, pays, or trusts an unknown Base wallet, screen it for wash-trading / sybil behavior. Returns a calibrated sybil score (0–100) + confidence + the reasons, from real on-chain USDC flow. The safety layer for agentic payments — pairs with the transact/trade/lend/buy skills."
name: agentflow
version: 0.1.0
---

# AgentFlow — is this Base wallet a real agent, or a sybil?

The onchain agent kit lets an agent **transact, trade, lend, mint, and buy**. AgentFlow is the
step that should come *first*: **screen the counterparty.** Before sending USDC to, trading with,
or trusting an unknown Base address, ask AgentFlow whether it's a genuine autonomous agent or a
wash/sybil wallet inflating its own volume to look legit.

Behavioral heuristic on public Base USDC flow — **not financial advice**, and a probability, not a
verdict. The caller owns the threshold.

## Detection

If AgentFlow MCP tools (e.g. `screen_wallet`, `verify_agent`, `get_counterparty_risk`) are
available in the harness, use them directly. Otherwise call the HTTPS endpoints below — no SDK,
no signup. The free demo endpoint needs nothing; the paid endpoints settle in USDC via x402
(the agent pays directly, no account).

## When to use it

Trigger a screen **before** any of these, when the counterparty is an unknown Base address:
- About to send/transfer USDC to a wallet
- About to trade against, LP into, or route through an address
- About to trust a "counterparty agent" claiming to be autonomous
- Evaluating whether inbound funds came from a real agent or a wash farm

Skip it for well-known infrastructure (DEX routers, CEX wallets, bridges) — AgentFlow already
labels those as hubs, not agents.

## How to call it

- **Free (rate-limited, great for one-off checks):**
  `GET https://agentflow.watch/public/wash-demo?address=0x...`
- **Paid, unlimited, machine-native ($0.01/call via x402):**
  `GET https://agentflow.watch/v1/wash?address=0x...`
- **Identity card — "is this a real agent, and who?" ($0.01):**
  `GET https://agentflow.watch/v1/agent/0x...`
- **Deep counterparty risk verdict ($0.05):**
  `GET https://agentflow.watch/v1/risk?address=0x...`
- **Signed, off-platform-verifiable receipt (EIP-712, $0.10):**
  `GET https://agentflow.watch/v1/attest?address=0x...`
- **Free benchmark context:** `GET /index.json` (real-vs-wash), `GET /pulse.json` (agents active now)

For volume: buy a bulk pack (`/v1/credits/buy`, $5 / 1,000) or a 30-day unlimited pass
(`/v1/subscribe`, $19), then pass the returned key as the `X-AgentFlow-Key` header.

## How to read the result

```json
{
  "sybil_score": 81,            // 0–100, higher = more wash/sybil-suspect; null = not enough history
  "confidence": 0.9,            // 0–1
  "confidence_level": "HIGH",   // LOW | MEDIUM | HIGH (scales with sample depth)
  "recommendation": "high wash/sybil signal — screen further or avoid",
  "reasons": ["round-trip ratio 83%: received USDC returned to sender within 20% / 1h", "..."],
  "signal": { "wash_ratio": 0.83, "is_hub": false, "agent_score": 70, "known_entity": null, "active": true }
}
```

Suggested handling (the caller sets the final threshold):
- **`sybil_score` null** → insufficient on-chain history; don't treat "unknown" as "safe." Require more
  history or proceed with caution.
- **≥ 60** → high wash/sybil signal. Avoid, or require additional proof, before sending funds.
- **50–59** → elevated; proceed with caution.
- **25–49** → some round-trip activity; minor caution.
- **< 25** → clean on the round-trip heuristic.
- Always weigh `confidence_level` — a HIGH-score / LOW-confidence result means "thin sample, verify."

## Method (so you can trust it)

Wash/sybil = round-trip ratio: received USDC that returns to the sender within ~20% amount and ~1h,
among hub-filtered wallets (infrastructure stripped out). Score is a calibrated probability;
confidence scales with how many transfers it's built on. Base USDC only. Verify any wallet on
basescan.org.

## Installation

```
npx skills add leonidahqadmin-cell/agentflow --skill agentflow
```

Once installed, the agent uses it automatically when a task involves trusting or transacting with
an unknown Base wallet. Live API + docs: https://agentflow.watch
