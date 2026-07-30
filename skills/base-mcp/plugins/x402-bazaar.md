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
risk: []
---

# x402 Bazaar Plugin

> [!IMPORTANT]
> Run Base MCP onboarding first (see SKILL.md). This plugin is read-only — it
> returns intelligence the user/agent can act on; it never builds a transaction.

## Overview

x402 Bazaar is a pay-per-call API marketplace on Base exposing 118 read-only
services today — token safety (risk, honeypot, rug score), wallet intelligence
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
| Free tier | none | nothing — one free call per service per day |
| Prepaid credits (recommended) | `X402_CREDIT_TOKEN` | a bearer token with a capped balance, bought once at `https://402.com.tr/credits` |
| Wallet | `AGENT_PRIVATE_KEY` | a Base private key; only USDC is needed, and it never leaves the machine |

Prefer credits where the host config is shared or synced: a spent-out credit
token is worth nothing, while a leaked key is worth everything in the wallet.
Package: `x402-bazaar-mcp` (npm) · registry `io.github.sukrutkrdg/x402-bazaar-mcp`.

## Surface Routing

| Capability | Surface | Execution path |
|---|---|---|
| Any read (token/wallet/compliance/AI report) | MCP client (Claude Desktop, Cursor, Code) | `x402-bazaar` MCP tool → pays x402 → returns JSON |
| Same | chat-only host without the MCP server | Not available — instruct the user to add `x402-bazaar-mcp` (see Installation) |

Shell-less fallback: none required — all access is via the MCP server's tools.

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
3. "Profile wallet `0x…` — net worth, age, what can drain it." → call `wallet_networth`, `wallet_summary`, `token_approvals`; summarize.
4. "What's the 24h price & momentum of `0x…`?" → call `token_momentum`; report price and 1h/6h/24h change.
5. "Is `0x…` a B20 token that can freeze or seize my funds?" → call `b20_safety`; report the hold/caution/avoid verdict and which issuer powers (freeze / seize / pause / rebase) are live.
6. "Is wallet `0x…` 7702-delegated to code I should worry about?" → call `wallet_delegation`; report the delegate and whether it is a known Coinbase implementation or unrecognized (takeover risk).
7. "This invoice asks me to pay a new supplier at `billing@acme-payments.com` — check it." → call `email_verify` and `domain_check`; report deliverability plus how old the domain is, since a domain registered weeks ago is the standard vendor-impersonation pattern.
