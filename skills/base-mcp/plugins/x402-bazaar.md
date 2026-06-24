---
title: "x402 Bazaar Plugin"
description: "Read-only onchain data & AI reports for Base (token risk, wallet intelligence, OFAC sanctions, prices, NFTs) via the x402-bazaar-mcp server; paid per call in USDC over x402. Returns data only — makes no Base MCP transaction."
tags: [data, token-risk, wallet-intel, compliance, x402]
name: x402-bazaar
version: 0.1.0
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

x402 Bazaar is a pay-per-call API marketplace on Base exposing 40+ read-only
services — token safety (risk, honeypot, rug score), wallet intelligence (net
worth, age/activity, approvals, transfers, NFTs), OFAC sanctions screening,
prices/momentum/pools, and Claude-written AI token & wallet reports. It is
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
      "env": { "AGENT_PRIVATE_KEY": "0xYOUR_BASE_WALLET_KEY" }
    }
  }
}
```

The wallet needs only USDC on Base. Package: `x402-bazaar-mcp` (npm) ·
registry `io.github.sukrutkrdg/x402-bazaar-mcp`.

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
