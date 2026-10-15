---
title: "Kokosh Plugin"
description: "Paid wallet-hygiene audit (allowance exposure + scam-airdrop scan) for kajko24.base.eth via x402 → sign on Base."
tags: [wallet-hygiene, security, ai-agents, discovery]
name: kokosh
version: 0.1.0
integration: http-api
chains: [base]
requires:
  shell: none
  allowlist: [kokosh-agent.vercel.app]
  externalMcp: null
  cliPackage: null
auth: none
risk: [irreversible]
---

# Kokosh Plugin

> [!IMPORTANT]
> Run Base MCP onboarding first (see SKILL.md). No session prerequisite beyond onboarding — each `/audit` call pays independently.

## Overview

Kokosh is a wallet-hygiene sentinel agent for `kajko24.base.eth` on Base mainnet. Its paid `/audit`
endpoint (`https://kokosh-agent.vercel.app/audit`, $0.01 USDC via x402) returns live token/Permit2
allowance exposure plus a scam-airdrop scan (URL-in-name, urgency language, homoglyph, ticker-impersonation
heuristics) for that one wallet. This plugin does not build onchain calldata — it reads a 402 payment
requirement from an HTTP response and routes the resulting x402 payment authorization through Base MCP's
`sign` tool before resubmitting the request.

## Surface Routing

| Capability | Surface | Path |
|---|---|---|
| Request `/audit` | Claude Code / Codex / Cursor (harness HTTP tool) | Direct HTTP GET; on `402`, decode the `payment-required` header, sign via Base MCP `sign`, resubmit with `X-PAYMENT`. |
| Request `/audit` | Claude.ai / ChatGPT (chat-only) | Base MCP `web_request` to `kokosh-agent.vercel.app` (already on the allowlist above); same 402 → sign → resubmit flow. |
| Free reads (`/exposure`, `/drops`, `/healthz`) | Any surface | Direct HTTP GET, no payment, no signing. |

## Endpoints

- `GET https://kokosh-agent.vercel.app/audit` — paid, $0.01 USDC on Base (`eip155:8453`), payTo is Kokosh's agent wallet. No parameters. On first call (no payment) returns `402` with a `payment-required` header: a base64 JSON blob (`x402Version`, `resource`, `accepts[]` — scheme `exact`, `network eip155:8453`, `amount` in USDC base units, `asset` = native USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`, `payTo`). On success (`200`) returns `{ wallet, auditedAt, exposure: { liveErc20Approvals, livePermit2Grants, approvals[], permit2Grants[] }, scamAirdrops: { scannedTokens, flaggedCount, flagged[] }, hygieneScore }`.
- `GET https://kokosh-agent.vercel.app/exposure` — free. Same `exposure` shape as above, cached from the last approval scan; `202` if no scan has run yet.
- `GET https://kokosh-agent.vercel.app/drops` — free. Same `scamAirdrops` shape as above, computed live against current token holdings.
- `GET https://kokosh-agent.vercel.app/healthz` — free liveness check.
- `GET https://kokosh-agent.vercel.app/.well-known/agent-card.json` — free ERC-8004 agent card (also lists the mainnet Identity Registry `agentId`).

## Orchestration

1. `GET /audit`.
2. If `200`, return the body — done, no payment needed for this call in this flow instance.
3. If `402`, base64-decode the `payment-required` response header to get the `PaymentRequired` object and its single `accepts[0]` entry (scheme `exact`, network `eip155:8453`, `amount`, `asset`, `payTo`).
4. Build the EIP-3009 `TransferWithAuthorization` EIP-712 typed data for the `asset` (USDC) contract: domain `{ name: "USD Coin", version: "2", chainId: 8453, verifyingContract: asset }`, message `{ from: <wallet>, to: payTo, value: amount, validAfter, validBefore, nonce }` (see [Submission](#submission) for the smart-wallet caveat before signing).
5. Sign via Base MCP `sign`.
6. Encode the signed authorization as the `X-PAYMENT` header per x402 v2 (`x402Version`, `scheme: "exact"`, `network`, `payload: { authorization, signature }`) and resubmit the original `GET /audit` request with that header.
7. Return the `200` body to the user; note the USDC amount actually spent.

## Submission

Names the Base MCP tool: **`sign`** (EIP-712 typed-data signature over the EIP-3009 authorization) — **not** `send_calls`. The signed authorization travels in an HTTP header (`X-PAYMENT`), not as an onchain transaction submitted by the agent; the x402 facilitator broadcasts the actual USDC transfer.

**Smart-wallet caveat, updated after live testing:** Base MCP's default wallet is a smart contract account, and `sign`/typed-data signatures against it come back ERC-1271/6492-shaped rather than a plain 65-byte ECDSA signature. Standard EIP-3009 `transferWithAuthorization(address,address,uint256,uint256,uint256,bytes32,uint8,bytes32,bytes32)` (the classic `(v,r,s)` overload, selector `0xe3ee160e`) verifies with a plain `ecrecover` and rejects that shape — so a facilitator that only calls that overload **will** fail settlement for a smart-contract wallet. However, USDC (Circle's FiatTokenV2) also exposes `transferWithAuthorization(address,address,uint256,uint256,uint256,bytes32,bytes)` — a single raw `bytes signature` overload (selector `0xcf092995`) — that validates through a `SignatureChecker`-style path accepting both plain ECDSA and ERC-1271/6492 contract-wallet signatures. **Verified live on mainnet (2026-07-23):** paying this exact `/audit` endpoint from a Coinbase Smart Wallet (Base Account) via Base MCP's native `initiate_x402_request`/`complete_x402_request` tools settled successfully — the on-chain tx called the `bytes`-signature overload, not the classic one. Root cause: Kokosh's `/audit` seller uses `@coinbase/x402`'s CDP-hosted facilitator, which picks the `bytes`-overload call when the signature isn't classic-ECDSA-shaped.
>
> Net effect: **prefer Base MCP's native `initiate_x402_request` / `complete_x402_request` tools over this plugin's manual `sign` → build-your-own-`X-PAYMENT` orchestration whenever both are available** — the native path already handled the smart-wallet case correctly here, with no special-casing needed. The manual path in this plugin's Orchestration section (building `X-PAYMENT` by hand from a raw `sign` call) remains useful for harnesses that lack Base MCP's native x402 tools, but its risk is real only insofar as the *target facilitator* might not implement the `bytes`-overload dispatch — that's a per-facilitator property, not a fixed limitation of x402's `exact` scheme or of smart-contract wallets in general. Kokosh's own facilitator (CDP-hosted) does implement it, confirmed against real settlement.

## Example Prompts

1. **"What's kajko24.base.eth's onchain hygiene right now?"**
   → Steps 1–2 (free path if a scan is cached) or 1–7 (paid path) of Orchestration against `/audit`; summarize `hygieneScore`, live approval count, and flagged tokens.
2. **"Any scam airdrops sitting in kajko24.base.eth?"**
   → `GET /drops` (free); list `flagged[]` with `reasons`.
3. **"Pay for a full Kokosh audit and tell me if I should revoke anything."**
   → Full Orchestration 1–7; highlight any `approvals[]`/`permit2Grants[]` entries, cross-reference with `scamAirdrops.flagged` addresses.
4. **Chat-only surface (Claude.ai) request** → same flow via `web_request` (Surface Routing); if the surface can't sign EIP-712 through Base MCP `sign` at all, stop and tell the user this capability needs a Base MCP-enabled harness.

## Risks & Warnings

- **`irreversible`** — each successful `/audit` call spends real USDC ($0.01) with no refund path; don't call it speculatively or in a retry loop. Confirm with the user before paying if the surface doesn't already gate writes behind approval, and never auto-retry a failed payment without telling the user money may have moved.

## Notes

- Kokosh's ERC-8004 identity: agentId `59633` on the Base mainnet Identity Registry (`0x8004A169FB4a3325136EB29fA0ceB6D2e539a432`); agent wallet is a dedicated relay address, separate from the audited wallet (`kajko24.base.eth`).
- `/exposure` and `/drops` are free and cover most "is my wallet OK" questions — only route to paid `/audit` when the user wants the combined report + `hygieneScore`, or explicitly asks to pay.
- Repo: github.com/Kajko25/kokosh — `docs/JOURNAL.md` has the full build history including the x402 seller/buyer implementation this plugin describes.
