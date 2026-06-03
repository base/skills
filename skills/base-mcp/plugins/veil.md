---
title: "Veil Cash Plugin"
description: "Privacy pool on Base via Veil MCP — prepare register/deposit calldata for send_calls; private withdraw, transfer, and x402 via Veil relay."
tags: [privacy, shielded-payments, agent-commerce]
name: veil
version: 0.2.1
integration: external-mcp
chains: [base]
requires:
  shell: none
  allowlist: []
  externalMcp:
    name: veil
    url: null
  cliPackage: null
auth: none
risk: [irreversible]
---

# Veil Cash Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before calling any Veil tool. Use `baseAccount.address` from Base MCP `get_wallets` as `owner` on Veil MCP calls that require it.

## Overview

Veil Cash is a privacy pool for ETH and USDC on Base mainnet (`8453`, Base MCP chain string `base`). This is an **external-mcp** plugin: all Veil operations go through a local Veil MCP server (`@veil-cash/mcp` on npm). Public register/deposit flows return **unsigned calldata** for Base MCP `send_calls`; private withdraw, transfer, x402 payment, and UTXO consolidation submit through the Veil relay inside Veil MCP (`none` on Base MCP — see [Submission](#submission)).

Veil MCP v1 is **stdio-only**. There is no hosted HTTP MCP URL: `VEIL_KEY`, proof building, and balance decryption must stay on the user's machine. A hosted MCP would require custodial keys and would centralize activity metadata, which defeats the purpose of a privacy pool.

The exact list of Veil tools, their parameters, and descriptions are advertised by Veil MCP itself — read the tool catalog at runtime rather than relying on a fixed list in this file.

If another Veil skill from `@veil-cash/sdk` is available, treat it as CLI-specific reference only. This plugin is the authority for Base MCP use: do not switch to CLI signing modes, Bankr flows, or direct SDK transaction submission.

Veil keys are local. Base Account smart wallets do not reliably provide the plain `personal_sign` signature needed for Veil's deterministic key derivation, so v1 uses a random local Veil key (`veil_init_keypair`). Configure `VEIL_KEY` in the MCP server env or `.env.veil` to enable private balances and relay-backed writes.

## Detection

If no Veil tools (e.g. `veil_status`, `veil_prepare_deposit`, `veil_get_balances`) are exposed to the harness, Veil MCP is not installed. Do not improvise Veil flows with the SDK CLI or direct contract calls — install Veil MCP alongside Base MCP (see [Installation](#installation)), reconnect or restart the session so tools register, then retry.

## Installation

Veil MCP is a **local stdio** server, not a hosted HTTP connector. Install it beside Base MCP in the harness MCP config (`command` + `args`, or global `veil-mcp` binary). `requires.externalMcp.url` is `null` by design — do not substitute a remote URL or SDK CLI in place of the local MCP.

Pin a version for reproducibility, e.g. `@veil-cash/mcp@0.2.1`.

**Recommended (avoids per-launch npm resolution):**

```bash
npm install -g @veil-cash/mcp
```

Detect the harness and apply the matching step:

- **Claude Code:** add Veil MCP to the harness MCP config (see JSON below) and restart.
- **Codex:** add `[mcp_servers.veil]` with `command = "veil-mcp"` to `codex.toml`, or use the JSON snippet below.
- **Cursor / JSON-config harnesses:** add the snippet below to `~/.cursor/mcp.json` or the project's `.cursor/mcp.json` and restart.
- **Claude.ai web / ChatGPT connectors:** unsupported on v1. These surfaces require a hosted HTTP MCP URL; Veil deliberately does not offer one because private keys and metadata must stay local. Tell the user Veil requires a harness that can launch a local MCP process (Cursor, Codex, Claude Code). Do not improvise a workaround or suggest a hosted alternative.
- **Other / unknown harness:** show the JSON snippet below and ask the user where their MCP config lives.

```json
{
  "mcpServers": {
    "base-mcp": { "url": "https://mcp.base.org" },
    "veil": {
      "command": "npx",
      "args": ["-y", "@veil-cash/mcp@0.2.1"]
    }
  }
}
```

Or, when `veil-mcp` is installed globally:

```json
{
  "mcpServers": {
    "base-mcp": { "url": "https://mcp.base.org" },
    "veil": { "command": "veil-mcp" }
  }
}
```

**Enabling private writes** — set `VEIL_KEY` (and optionally `RPC_URL`) in the Veil MCP server env:

```json
{
  "mcpServers": {
    "veil": {
      "command": "npx",
      "args": ["-y", "@veil-cash/mcp@0.2.1"],
      "env": {
        "VEIL_KEY": "0x...",
        "RPC_URL": "https://your-base-rpc"
      }
    }
  }
}
```

Use `npx -y github:veildotcash/veil-mcp` only for development; GitHub resolution slows MCP startup.

After install, ask the user to reconnect or restart the session so Veil tools register.

## Surface Routing

| Capability | Harness surface | Execution path | Base MCP submission |
|---|---|---|---|
| All Veil operations | Harness with local Veil MCP (stdio) | Veil MCP tools | varies by operation — see [Submission](#submission) |
| Read (status, balances, deposit status, x402 quote/receipts) | Cursor, Codex, Claude Code, etc. | Veil MCP read tools | `none` |
| Register / deposit (public on-chain) | Same | Veil MCP prepare tools → Base MCP | `send_calls` |
| Private withdraw / transfer / x402 / consolidate | Same | Veil MCP relay tools (`confirm: true`) | `none` |
| Chat-only connectors (Claude.ai web, ChatGPT) | No local stdio MCP | **Stop** — no hosted URL on v1 (privacy) | — |

Veil MCP performs its own RPC and relay HTTP calls internally. Base MCP `web_request` is not used for Veil protocol access. A dedicated `RPC_URL` on the Veil MCP server is recommended because Merkle tree, event, queue, and balance reads can hit public RPC rate limits; it does not replace Base MCP for public transaction submission.

## Orchestration

### Registration

```text
1. Base MCP get_wallets → owner (baseAccount.address)
2. Veil MCP veil_status({ owner })
3. If no local Veil key, veil_init_keypair({}) — returns deposit key only, never VEIL_KEY
4. Veil MCP veil_status({ owner }) to confirm key and registration state
5. Veil MCP veil_prepare_register({ owner })
6. If action is alreadyRegistered and calls is empty, skip send_calls
7. Base MCP send_calls({ chain: "base", calls }) → approvalUrl + requestId
8. User approves → Base MCP get_request_status(requestId)
```

If the owner is registered with a different deposit key, ask the user before retrying `veil_prepare_register` with `force: true` (key rotation).

### Deposit

```text
1. Base MCP get_wallets → owner
2. Veil MCP veil_status({ owner }) — ensure key exists and owner is registered
3. Veil MCP veil_prepare_deposit({ owner, asset, amount })
4. Base MCP send_calls({ chain: "base", calls })
5. User approves → get_request_status(requestId)
6. Veil MCP veil_get_balances({ owner, pool }) to find pending nonce
7. Veil MCP veil_deposit_status({ owner, pool, nonce }) until status is not pending
```

After Base MCP confirms the transaction, funds enter the Veil queue before becoming private balance. Typical processing is **8–12 minutes**. Report the lifecycle clearly: submitted on Base → pending in queue → accepted into private balance. `veil_deposit_status` reports `queuePosition`, `queueLength`, and `typicalProcessingMinutes`.

Deposit `amount` is the **net** amount that lands in Veil; the 0.3% protocol fee is included in prepared calldata. Minimums: `0.01 ETH`, `10 USDC`.

### Private withdraw, transfer, x402, or consolidation

```text
1. Ask the user to explicitly confirm the relay-backed private action.
2. For private transfers, verify the recipient is registered with Veil.
3. For x402: optionally veil_x402_quote first; confirm URL, maxPayment cap, and that private USDC moves to a payer EOA.
4. Veil MCP veil_withdraw / veil_transfer / veil_pay_x402 / veil_consolidate_utxos with confirm: true
5. Report public metadata only: tx hashes, amounts, payer address, response status/body, success
```

Do **not** route private relay actions through Base MCP `send_calls`.

### x402 payment (private USDC)

Supports Coinbase-compatible x402 v2 `exact` Base USDC resources (GET and POST). Always set a tight `maxPayment` cap (decimal USDC string, e.g. `"0.10"`); default and hard cap is `10 USDC`. `veil_pay_x402` pre-flights the endpoint — if the probe is not HTTP 402, it returns `action: "endpoint_error"` and withdraws nothing.

If a funded payer already holds enough USDC, `veil_pay_x402` may return `action: "reuse_available"`. Ask the user to reuse via `payerIndex` or withdraw anew with `forceFresh: true`. Each payment writes a local receipt (`.veil-x402-receipts.json`).

### UTXO consolidation

A single transaction consumes at most **16 input UTXOs**. When `veil_get_balances` reports `fragmentation.needsConsolidation: true`, call `veil_consolidate_utxos({ asset, confirm: true })`. Repeat while `needsAnotherRound: true`.

### Subaccounts

Valid slots are 0–2. v1 of this plugin exposes status only via `veil_subaccount_status`. If the user asks to deploy, sweep, merge, or recover subaccounts, explain that those flows are not exposed in v1.

## Submission

This plugin uses **two** Base MCP submission targets depending on the operation.

### Public flows → `send_calls`

Veil MCP prepare tools return:

```json
{
  "chain": "base",
  "calls": [
    { "to": "0x...", "value": "0x0", "data": "0x..." }
  ]
}
```

Map directly into Base MCP:

```json
{
  "chain": "base",
  "calls": [
    { "to": "<call.to>", "value": "<call.value>", "data": "<call.data>" }
  ]
}
```

- Pass `chain` and `calls` unchanged from the Veil MCP response.
- USDC deposits return an ordered **approve + deposit** batch — submit the full array in one `send_calls` request.
- ETH deposits may include nonzero `value` on the deposit call; keep hex-encoded wei strings as returned.
- If `veil_prepare_register` returns `action: "alreadyRegistered"` with `calls: []`, do **not** call `send_calls`.
- After submission, present the approval URL and poll `get_request_status(requestId)` until completed, failed, or rejected.

### Private flows → `none`

Withdraw, transfer, x402 payment, and UTXO consolidation submit through the **Veil relay** inside Veil MCP. Base MCP is not involved after onboarding (`get_wallets` for `owner`). State explicitly: submission tool is `none`.

Private relay tools require `confirm: true` after explicit user approval — they are not Base MCP approval-link flows.

## Example Prompts

```
Deposit 0.1 ETH into Veil privately
```

1. Base MCP `get_wallets` → `owner`.
2. Veil MCP `veil_status({ owner })`; call `veil_init_keypair` if no local key.
3. Veil MCP `veil_prepare_register({ owner })`; if calls non-empty, Base MCP `send_calls`.
4. Veil MCP `veil_prepare_deposit({ owner, asset: "ETH", amount: "0.1" })`.
5. Base MCP `send_calls({ chain: "base", calls })` → user approves → `get_request_status`.
6. Veil MCP `veil_deposit_status({ owner, pool: "eth", nonce })` until accepted; explain 8–12 minute queue if pending.

```
What's my Veil balance?
```

1. Base MCP `get_wallets` → `owner`.
2. Veil MCP `veil_get_balances({ owner, pool: "all" })`.
3. Summarize wallet, queue, and private balances per pool. No Base MCP write.

```
Withdraw 50 USDC from Veil to my wallet
```

1. Confirm recipient address and amount with the user.
2. Veil MCP `veil_withdraw({ asset: "USDC", amount: "50", recipient: "<address>", confirm: true })`.
3. Report transaction hash and success. Submission: `none`.

```
Pay this x402 API from my private USDC
```

1. Veil MCP `veil_x402_quote({ url, maxPayment: "0.10" })` — validate price and support.
2. Confirm URL and cap with the user.
3. Veil MCP `veil_pay_x402({ url, maxPayment: "0.10", confirm: true })`.
4. If `reuse_available`, ask user to pick `payerIndex` or `forceFresh: true` before retrying.
5. Report payment status and response summary. Submission: `none`.

```
Use Veil on Claude.ai
```

1. Detect chat-only connector surface with no local MCP config.
2. Explain: Veil v1 requires a local stdio MCP because `VEIL_KEY` and private metadata must stay on the user's machine; there is no hosted HTTP URL by design.
3. Direct the user to Cursor, Codex, or Claude Code with Base MCP + Veil MCP installed. Do not substitute SDK CLI or direct contract calls.

## Risks & Warnings

### irreversible

Onchain register/deposit transactions and relay-backed private actions cannot be undone once submitted. Confirm asset, amount, recipient, and whether the action uses Base MCP approval or the Veil relay before any write. Deposits enter a screening queue; rejected deposits may be refunded to the fallback receiver per queue rules. Do not resubmit private relay actions without explicit user confirmation after a failure.

Guardrails:

- Never ask Veil MCP to reveal `VEIL_KEY` or request raw private key material from the user.
- Never echo proof internals, nullifiers, encrypted outputs, payer private keys, or x402 signatures.
- Do not show raw calldata as the final user-facing answer — summarize asset, amount, fee, status, request id, transaction hash, and nonce.
- Set a tight `maxPayment` on every x402 call; never raise the cap silently.
- For private transfers, verify the recipient is registered with Veil before submitting.

## Notes

### Environment (Veil MCP server)

Veil MCP loads `.env.veil` first, then `.env`.

| Variable | Purpose |
| --- | --- |
| `VEIL_KEY` | Local Veil private key for private balances and relay writes |
| `DEPOSIT_KEY` | Public deposit key for register/deposit calldata |
| `RPC_URL` | Base RPC URL; defaults to `https://mainnet.base.org` |
| `RELAY_URL` | Veil relay URL override |
| `X402_RELAY_URL` | x402 relay base; defaults to `RELAY_URL + /x402` or hosted relay `/x402` |
| `X402_PAYER_INDEX` | Deterministic payer index counter; managed by `veil_pay_x402` |

### Error guidance

- Missing local Veil key: `veil_init_keypair` or provide `VEIL_KEY` in server env.
- Different registered deposit key: ask before `veil_prepare_register({ force: true })`.
- Invalid amount: minimum `0.01 ETH`, `10 USDC`.
- x402 unsupported: only Base USDC `exact` v2 is supported.
- RPC/network failure: suggest dedicated `RPC_URL`; check `veil_status` relay health.
- Relay failure: do not resubmit private actions without user confirmation.

### Fragmentation

`veil_get_balances` returns per-pool `fragmentation` (`unspentCount`, `largestUtxo`, `smallestUtxo`, `needsConsolidation`). When `needsConsolidation` is true, the full balance cannot be spent in one transaction until consolidated.

### x402 payer recovery

`veil_x402_payer_balances({ discover: true })` finds USDC left on payer EOAs after failed payments. Funds remain recoverable from `VEIL_KEY + payerIndex`. `veil_x402_receipts({ limit })` reconstructs local spend history.

### Package

- npm: [@veil-cash/mcp@0.2.1](https://www.npmjs.com/package/@veil-cash/mcp)
- source: [veildotcash/veil-mcp](https://github.com/veildotcash/veil-mcp)
