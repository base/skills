---
title: "AgentRisk Plugin"
description: "Pre-trade honeypot/tax risk scoring for Base tokens via x402-paid HTTP API, checked before a swap."
tags: [dex, swap, trading, discovery, ai-agents]
name: agentrisk
version: 0.1.0
integration: http-api
chains: [base]
requires:
  shell: none
  allowlist: [agentrisk.dev]
  externalMcp: null
  cliPackage: null
auth: none
risk: []
---

# AgentRisk Plugin

> [!IMPORTANT]
> Run Base MCP onboarding first (see SKILL.md). No additional session setup required — each call is paid independently via x402.

## Overview
AgentRisk is a self-hosted pre-trade risk API for Base Mainnet. It combines direct on-chain checks (ownership, pausability, LP-burn), GoPlus Security data, and DexScreener liquidity data into a single risk score. It returns an advisory JSON decision (`shouldExecute`, `riskScore`, `riskLevel`, `verdict`, `reasons`) — it does not build or submit any calldata itself.

Beyond the base risk score, AgentRisk also flags:
- **Deployer wallet freshness** — newly-created wallets used for one-off token launches
- **Brand impersonation** — tokens named after known companies (Apple, Google, Meta, etc.)
- **Data source disagreement** — cases where third-party APIs and our own on-chain checks conflict
- **Human-readable verdict** — one plain-English sentence summarizing the decision
- Repeat scans within 5 minutes are served from cache in under 1ms

## Surface Routing
| Capability | Harness with HTTP/shell (Claude Code, Codex, Cursor) | Chat-only (Claude.ai, ChatGPT) |
| --- | --- | --- |
| Check token risk (read) | Call the endpoint directly via the harness HTTP tool; harness's x402-aware client handles the 402 payment automatically. | Call via Base MCP `web_request` (`agentrisk.dev` is on the allowlist); Base MCP's native x402 payment capability handles the 402 automatically. |

## Endpoints
- `GET https://agentrisk.dev/scan?token=<CONTRACT_ADDRESS>` — x402-gated (0.15 USDC, Base mainnet, `eip155:8453`). Returns the full risk report JSON (`risk_score`, `risk_level`, `findings`, `is_honeypot`, `liquidity_usd`, etc.).
- `POST https://agentrisk.dev/mcp/tools/check_token_risk` — body `{"token_address": "<CONTRACT_ADDRESS>"}`. Same underlying analysis, x402-gated identically. Returns `{"status": "success", "decision": {"shouldExecute": bool, "riskScore": int, "riskLevel": string, "reasons": [string]}}`.

## Orchestration
1. User asks to buy/swap an unknown or untrusted token on Base.
2. Agent calls one of the endpoints above with the token contract address.
3. Endpoint responds `402 Payment Required` with x402 payment requirements (0.15 USDC, `eip155:8453`, exact scheme).
4. The agent's x402-aware client (harness or Base MCP) signs and submits the USDC payment authorization, then retries the request with the payment header.
5. AgentRisk verifies and settles the payment through its own self-hosted x402 facilitator, then runs the analysis and returns the decision.
6. Agent reads `shouldExecute`. If `false`, do not proceed — explain `reasons` to the user. If `true`, the agent may separately call Base MCP's own `swap` tool to execute the trade.

## Submission
`none`. AgentRisk's endpoints return an advisory JSON decision only — they do not produce calldata for `send_calls`. The only value that reaches Base MCP directly is the x402 USDC payment itself, handled by Base MCP's native x402 payment capability, not by this plugin.

## Example Prompts
1. "Buy $50 of token 0xABC... on Base, I'm not sure if it's safe." → Agent calls `GET /scan?token=0xABC...`, pays the x402 fee, reads `shouldExecute`. If `false`, explains the reasons and stops. If `true`, calls Base MCP `swap`.
2. "Is this new token a honeypot before I ape in?" → Same flow; agent surfaces `reasons` regardless of the verdict so the user sees the evidence.
3. Same request on a chat-only surface (Claude.ai) → identical flow, routed through Base MCP `web_request` instead of a direct HTTP call.

## Notes
- Price: 0.15 USDC per call, charged identically on both endpoints.
- Facilitator: self-hosted (not Coinbase CDP) — verification and settlement happen on Base mainnet directly.
- Only Base Mainnet (`eip155:8453`) is supported; no testnet.
- Source: https://github.com/Neurobyteio/agentrisk
