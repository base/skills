---
title: "x402 Bazaar Plugin"
description: "Read-only onchain data & AI reports for Base (token risk, B20 token safety, wallet intelligence, OFAC sanctions, prices, NFTs) plus off-chain counterparty checks (page-to-text, email and domain verification) via the x402-bazaar-mcp server; paid per call in USDC over x402. Returns data only — makes no Base MCP transaction."
tags: [data, token-risk, b20, wallet-intel, compliance, x402]
name: x402-bazaar
version: 0.1.1
integration: external-mcp
chains: [base]
requires:
  shell: none
  allowlist: []
  externalMcp: x402-bazaar-mcp
  cliPackage: null
auth: none
risk: [irreversible]
---

# x402 Bazaar Plugin

> [!IMPORTANT]
> Run Base MCP onboarding first (see SKILL.md). This plugin is read-only — it
> returns intelligence the user/agent can act on; it never builds a transaction.

## Overview

x402 Bazaar is a pay-per-call API marketplace on Base exposing read-only
services — token safety (risk, honeypot, rug score), wallet intelligence
(net worth, age/activity, approvals, transfers, NFTs), OFAC sanctions screening,
prices/momentum/pools, and Claude-written AI token & wallet reports. The agent
reads the tool list live from the catalog at startup, so the count tracks the
marketplace rather than this document. Alongside the onchain reads it now also
covers checks an agent needs before it acts off-chain: `url_extract` /
`url_to_json` (any page as agent-ready text or structured JSON), `email_verify`
and `domain_check` (deliverability, registration age and registry status — the
counterparty checks before an invoice or a signup is trusted) and
`sanctions_name` (OFAC screening for people and companies, not just wallets).
It also ships the only **B20** safety suite (~29 tools): B20 is Base's native token standard
(live 2026-07-08), and unlike ERC-20 a B20 issuer can freeze or seize a holder's
balance at the protocol level (Policy Registry / `burnBlocked`) — `b20_safety`
reads those powers into one hold/caution/avoid verdict, and the wider suite covers
seizure history, full blocklist membership, transfer preflight, supply/rebase and
an AI due-diligence dossier. Newer drain-surface reads include `wallet_delegation`
(EIP-7702 rogue-delegate check) and `agent_wallet_audit` (approvals + spend
permissions + delegation in one verdict). It is
reached through the **`x402-bazaar-mcp`** server. Each call settles a tiny USDC
micro-payment over **x402** on Base (gasless for the payer; the wallet key never
leaves the caller's machine). It complements Base MCP: Base MCP lets an agent
*act*, x402 Bazaar lets it *know what to act on*. No onchain transaction is
produced, so no `send_calls` handoff occurs.

## Detection

Consider this plugin available when the host has the `x402-bazaar` MCP server
connected (tools prefixed `x402-bazaar` / e.g. `token_risk`, `ai_token_report`,
`wallet_networth`). The agent reads the MCP's own tool catalog at runtime; the
live service list is also at `https://402.com.tr/.well-known/x402`.

## Installation

Add the MCP server to the host config (Claude Desktop / Cursor / any MCP client):

```json
{
  "mcpServers": {
    "x402-bazaar": {
      "command": "npx",
      "args": ["-y", "x402-bazaar-mcp"],
      "env": { "X402_CREDIT_TOKEN": "ck_YOUR_PREPAID_TOKEN" }
    }
  }
}
```

Three modes, in order of how much they expose:

| Mode | Env | What the host holds |
|---|---|---|
| Free trial | none | nothing — one free call per service per day, opted into with `?free=1` |
| Prepaid credits (recommended) | `X402_CREDIT_TOKEN` | a bearer token with a capped balance, bought once at `https://402.com.tr/credits` |
| Wallet | `AGENT_PRIVATE_KEY` | a Base private key; only USDC is needed, and it never leaves the machine |

Prefer credits where the host config is shared or synced: a spent-out credit
token is worth nothing, while a leaked key is worth everything in the wallet.
Package: `x402-bazaar-mcp` (npm) · registry `io.github.sukrutkrdg/x402-bazaar-mcp`.

## Auth

No account, no API key, no login. Access is decided per call by what the host
supplies, and the agent never performs an auth handshake:

- **Nothing supplied** — add `?free=1` to the URL and the trial serves one call
  per service per day, keyed by IP. Enough to try any tool before paying for it.
  Without that flag an unpaid call always answers `402` with the price, so that a
  crawler reading the catalog sees what a service costs rather than its output.
- **`X402_CREDIT_TOKEN`** — a bearer token bought once, debited per call. Send it
  and nothing else; there is no signature per call and no wallet involved.
- **`AGENT_PRIVATE_KEY`** — the server signs an x402 payment locally per call.
  The key stays on the machine; only a signed payment authorization is sent.

Nothing here requires SIWE or grants write access to the wallet: an x402 payment
authorizes one transfer of the quoted amount to the seller, nothing else.

## Surface Routing

| Capability | Surface | Execution path |
|---|---|---|
| Any read (token/wallet/compliance/AI report) | MCP client (Claude Desktop, Cursor, Code) | `x402-bazaar` MCP tool → pays x402 → returns JSON |
| Same | chat-only host without the MCP server | Not available — instruct the user to add `x402-bazaar-mcp` (see Installation) |

Shell-less fallback: none required — all access is via the MCP server's tools.

## Endpoints

The server registers every catalogued service as a tool at startup, so the
authoritative list is the MCP tool catalog itself (and
`https://402.com.tr/.well-known/x402`). The ones an agent reaches for most:

| Tool | Price | Returns |
|---|---|---|
| `token_risk` | $0.03 | ERC-20 conformance, ownership renounce, proxy upgradeability → risk level |
| `rug_score` | $0.03 | Liquidity, holder concentration and deployer history → rug score |
| `sellability` | $0.08 | Simulated exit: can this token actually be sold, and at what tax |
| `pre_trade_gate` | $0.10 | The four checks above as one GO / HOLD / STOP before a buy |
| `b20_safety` | $0.04 | B20 issuer powers (freeze, seize, pause, rebase) → hold/caution/avoid |
| `wallet_networth` | $0.02 | Token balances and total value for a wallet |
| `approval_advisor` | $0.05 | Live ERC-20 approvals, ranked by what they can drain, with a revoke queue |
| `wallet_delegation` | $0.03 | EIP-7702 delegate, and whether it is a recognized implementation |
| `agent_wallet_audit` | $0.06 | Approvals + spend permissions + delegation as one drain-surface verdict |
| `sanctions` | $0.02 | OFAC screening for a wallet address |
| `sanctions_name` | $0.05 | OFAC screening for a person or company name |
| `email_verify` | $0.02 | Syntax, MX/A deliverability, disposable/role detection → GO/HOLD/STOP |
| `domain_check` | $0.02 | Registration age, expiry and registry status from RDAP → GO/HOLD/STOP |
| `url_extract` | $0.002 | Any web page as clean, agent-ready text |
| `url_to_json` | $0.04 | The same page as structured JSON against a caller-supplied shape |
| `ai_token_report` | $0.12 | Claude-written token due diligence |
| `deep_dd` | $0.75 | The full multi-signal due-diligence report |

Prices are quoted live in each 402 challenge; the numbers above are indicative.
Verdict tools additionally return a decision receipt — input hash, policy
version, confidence band, and a structured refusal instead of a guess when a
feed is unavailable.

## Orchestration

1. Confirm the `x402-bazaar` MCP server is connected (Detection); if not, point the user to Installation.
2. Pick the tool matching the user's intent (e.g. `ai_token_report` for "is this token safe?", `wallet_networth` for "what's in this wallet?", `sanctions` for OFAC screening).
3. Call the tool with the address/params; the server settles the x402 USDC micro-payment and returns JSON.
4. Use the returned data in the answer. If the user then wants to act (swap, send), hand that off to Base MCP separately — this plugin does not transact.

## Submission

Tool: `none`. This plugin is read-only; it returns data and never calls a Base
MCP submission tool (`send_calls`/`swap`/`sign`).

## Example Prompts

1. "Is `0x…` a safe token to buy on Base?" → call `ai_token_report` (or `token_risk` + `token_price`), summarize the verdict and risks.
2. "Screen `0x…` for OFAC sanctions before I send funds." → call `sanctions` (or `compliance_check`); report blocked/clear.
3. "Profile wallet `0x…` — net worth, age, what can drain it." → call `wallet_networth`, `wallet_summary`, `approval_advisor`; summarize.
4. "What's the 24h price & momentum of `0x…`?" → call `token_momentum`; report price and 1h/6h/24h change.
5. "Is `0x…` a B20 token that can freeze or seize my funds?" → call `b20_safety`; report the hold/caution/avoid verdict and which issuer powers (freeze / seize / pause / rebase) are live.
6. "Is wallet `0x…` 7702-delegated to code I should worry about?" → call `wallet_delegation`; report the delegate and whether it is a known Coinbase implementation or unrecognized (takeover risk).
7. "This invoice asks me to pay a new supplier at `billing@acme-payments.com` — check it." → call `email_verify` and `domain_check`; report deliverability plus how old the domain is, since a domain registered weeks ago is the standard vendor-impersonation pattern.

## Risks & Warnings

- **Paid calls are irreversible.** Each call settles a USDC micro-payment on
  Base. It cannot be undone, so do not loop a paid tool over a list without the
  user agreeing to the total first. Quote the price before a batch.
- **This is data, not advice.** Verdicts (`GO`/`HOLD`/`STOP`, risk levels,
  scores) are computed from onchain and registry data. They are inputs to the
  user's decision, not a recommendation to buy, sell or trust anything. Present
  them with their reasons, not as conclusions.
- **A refusal is not a pass.** When a feed is unavailable the response carries a
  refusal with `confidence.band: "low"` rather than a verdict. Never read that as
  "clean" — say the check could not be completed.
- **Freshness.** Everything is read at call time; a token or wallet can change
  the block after the answer. For anything time-sensitive, re-check rather than
  reusing an earlier result.
- **Wallet mode holds a key.** With `AGENT_PRIVATE_KEY` the host config contains
  a Base private key. Prefer the credit token where the config is shared, synced
  or committed. Fund the wallet with USDC only.
- **Read-only by construction.** No tool here produces a transaction, so nothing
  in this plugin can move the user's assets other than the per-call payment.

## Notes

- **Free trial:** one call per service per day, no key needed — but it is opt-in.
  Pass `?free=1` (or the header `x-402-free: 1`); a plain unpaid call returns `402`
  by design. AI services and a few others are never free and ignore the flag.
- **Free calls return a preview.** Once the daily free call is used the endpoint
  serves a trimmed teaser marked `preview: true`; treat that as a sample, not the
  answer, and pay for the full report when the user needs the detail.
- **Decision receipts** are documented at
  <https://github.com/sukrutkrdg/402/blob/main/docs/decision-receipt.md>.
- **Coverage is honest about its edges:** RDAP does not exist for every TLD and
  OFAC screening is name/address matching, so those tools refuse rather than
  guess. Surface the refusal reason to the user.
- Live catalogue and prices: <https://402.com.tr/.well-known/x402> · docs:
  <https://402.com.tr/agents>
