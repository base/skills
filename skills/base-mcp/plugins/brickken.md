---
title: "Brickken Plugin"
description: "ERC-8004 agent identity, reputation, and agent-owned ERC-20s on Base — Brickken builds unsigned calldata for send_calls, or self-executes through its x402 CLI/MCP."
tags: [ai-agents, agent-commerce, token-launches]
name: brickken
version: 0.2.0
integration: hybrid
chains: [base]
requires:
  shell: optional
  allowlist: [api.brickken.com, api.sandbox.brickken.com]
  externalMcp: { name: brickken, url: https://mcp.brickken.com/mcp }
  cliPackage: npx brickken-cli
auth: none
risk: [irreversible, pii]
---

# Brickken Plugin

> [!IMPORTANT]
> Run Base MCP onboarding first (see `SKILL.md`). Brickken's agent API is **x402-paid**: every call costs USDC, so the payer (the Base Account on Path A when settlement is supported, or a funded EOA key on Path B) must hold USDC on the target chain before you start. The Base Account address is fetched lazily via `get_wallets` when a call needs it.

## Overview

Brickken puts the **ERC-8004** agent stack onchain: a registry for **agent identity**, a registry for **reputation/feedback**, and an **agent-owned ERC-20** factory for launching and managing agent tokens. This plugin covers those agent methods on Base. Brickken does not execute through one fixed route — it **builds the unsigned calldata** for each action, and you choose how it lands onchain:

- **Path A — Base Account via `send_calls` (x402-gated).** Brickken builds the calldata; when Base MCP can settle Brickken's x402 prepare invoice from the Base Account, the user's Base Account signs and broadcasts it through `send_calls`. Submission tool: **`send_calls`**.
- **Path B — Brickken self-executes (key-based).** The `brickken` CLI (or the Brickken MCP with a `privateKey`) signs with a local EOA key, pays x402, and broadcasts — no Base Account. Submission tool: **`none`**.

Both are first-class; pick per surface in [Surface Routing](#surface-routing). The agent API is x402-native: `prepare-transactions` and `send-transactions` are **each** priced in USDC (EIP-3009 `TransferWithAuthorization`). Path A pays only the prepare fee (then Base gas via `send_calls`); Path B pays the full USDC total plus native gas from the EOA unless Brickken confirms sponsorship for the target chain. See [Risks & Warnings](#risks--warnings) for per-method costs.

## Detection

The Brickken MCP path is available only if the harness exposes Brickken tools (`agent_register`, `agent_create_token`, `prepare_transactions`, …). If no `agent_*` tool is callable, the MCP is not installed — use the CLI (Path B, shell required) or call the HTTP API directly (see [Installation](#installation)). Do not assume the MCP is present. For Path A, prefer `prepare_transactions`; `agent_*` tools may auto-execute when the Brickken MCP session has a `privateKey`.

## Installation

Three routes reach Brickken; install only what your surface uses.

**HTTP API (no install).** Build calldata by POSTing to the Brickken API — host `api.brickken.com` (production) or `api.sandbox.brickken.com` (sandbox) must be on the Base MCP `web_request` allowlist for chat-only surfaces. On harnesses with a direct HTTP tool, no allowlist is needed.

**Brickken CLI (Path B, needs a shell).** No install step — run via `npx`:

```bash
npx brickken-cli --help          # or: npm i -g brickken-cli  →  brickken --help
```

The CLI is **x402-only** — it ignores API keys. Provide an EOA key for local transaction signing, x402 payment, and native gas on the target chain unless Brickken confirms sponsorship:

```bash
export BRICKKEN_PRIVATE_KEY=0x... # alias: BKN_PRIVATE_KEY
```

**Brickken MCP (optional, for the MCP path).** Remote MCP at `https://mcp.brickken.com/mcp`. Add it alongside Base MCP, e.g. in Claude Code:

```bash
claude mcp add --transport http brickken https://mcp.brickken.com/mcp
```

For other harnesses use the same URL in the connector/`mcpServers` config. A session that should self-execute (Path B via MCP) must be given a `privateKey` through the MCP's `configure` tool.

## Surface Routing

| Step | Harness with shell (Claude Code, Codex, Cursor) | Harness with HTTP tool, no shell | Chat-only (Claude.ai, ChatGPT) |
|---|---|---|---|
| **Build calldata** (prepare) | Harness HTTP `POST /prepare-transactions`, Brickken MCP `prepare_transactions`, or `brickken` CLI prepare-only (`--json`, no `--execute`) | harness HTTP `POST /prepare-transactions` | Brickken MCP `prepare_transactions`, or `web_request` POST to the allowlisted Brickken host |
| **Pay the prepare x402** | Base MCP x402 if settlement succeeds (Path A), or the CLI/EOA key (Path B) | Base MCP x402 if settlement succeeds (Path A) | Base MCP x402 if settlement succeeds (Path A) |
| **Execute the action** | Path A `send_calls`, or Path B `brickken … --execute` | Path A `send_calls` | Path A `send_calls` |

**Shell-less / chat-only:** Path B's CLI is unavailable without a shell — do not improvise it. Use Path A (`send_calls`) or the Brickken MCP. For Path A through Brickken MCP, call `get_config` first; use `prepare_transactions` or confirm `hasPrivateKey === false` before calling `agent_*`, because `agent_*` tools auto-execute when a `privateKey` is configured. Paying the prepare fee on Path A depends on Base MCP settling Brickken's x402 invoice from the Base Account (see [Notes](#notes) — verify on your surface). If neither a Base MCP x402 capability nor a funded EOA key is available to pay the prepare fee, stop and tell the user the call requires a USDC payment they can't currently make.

## Endpoints

HTTP path (Path A build-calldata, and Path B under the hood). API root: `https://api.brickken.com` (production) or `https://api.sandbox.brickken.com` (sandbox).

**`POST /prepare-transactions`** — body `{ "method": <name>, "chainId": "8453", "signerAddress": <Base Account>, …method args }`. Returns **402** the first time → pay the x402 invoice → retry → **200**:

```json
{
  "transactions": [
    { "to": "0x…", "data": "0x…", "value": "0x0", "gasLimit": "0x…", "chainId": 8453, "nonce": 49 }
  ],
  "txId": "0x…",
  "info": {
    "agentUuid": "54399c6e-…",
    "standard": "ERC-8004",
    "registryAddress": "0x8004A818…",
    "reputationRegistryAddress": "0x8004B663…",
    "agentURI": "ipfs://Qm…",
    "chainId": "eip155:8453"
  }
}
```

`method` values (this plugin's scope): `agentRegister`, `agentSetURI`, `agentSetMetadata`, `agentSetWallet`, `agentGiveFeedback`, `agentRevokeFeedback`, `agentAppendFeedbackResponse`, `agentCreateToken`, `agentMintToken`, `agentBurnToken`, `agentTransferToken`, `agentTransferFromToken`, `agentApproveToken`.

Common args: `signerAddress` (must equal the broadcasting wallet); identity calls take `name/description/image/serviceName/serviceEndpoint/aiModelName/aiModelProvider/x402Support/active` (register/set-uri) or `agentId`/`agentUuid` + `metadataKey/metadataValue/metadataEncoding` (set-metadata); token calls take `tokenAddress`, `to`/`from`/`spenderAddress`, `amount`, `decimals`. `agentRegister` requires `image` (backend validation).

**`POST /send-transactions`** — `{ txId, signedTransactions }`. Used **only by Path B** (Brickken broadcasts). Path A skips it — `send_calls` broadcasts instead.

> API-key alternative (not this plugin's default): the same host accepts an `x-api-key` header instead of paying x402. Use it only if you have a Brickken API key; with no key, the host falls back to the x402 invoice this plugin assumes.

## Commands

Path B. CLI ↔ backend method. Every command is **prepare-only by default**; add `--execute` to prepare → sign locally → send → pay x402 in one step. Add `--json` for machine-readable output.

| Command | Method | Purpose |
|---|---|---|
| `brickken agent register` | `agentRegister` | Register an ERC-8004 agent identity |
| `brickken agent set-uri` | `agentSetURI` | Update the agent profile/metadata URI (IPFS) |
| `brickken agent set-metadata` | `agentSetMetadata` | Set one onchain key/value |
| `brickken agent set-wallet` | `agentSetWallet` | Rotate the agent's operational wallet |
| `brickken agent feedback give` | `agentGiveFeedback` | Submit reputation feedback |
| `brickken agent feedback respond` | `agentAppendFeedbackResponse` | Respond to received feedback |
| `brickken agent feedback revoke` | `agentRevokeFeedback` | Revoke a feedback entry |
| `brickken create-token` | `agentCreateToken` | Deploy an agent-owned ERC-20 |
| `brickken mint` / `burn` | `agentMintToken` / `agentBurnToken` | Mint / burn agent tokens |
| `brickken transfer` / `transfer-from` | `agentTransferToken` / `agentTransferFromToken` | Transfer agent tokens |
| `brickken approve` | `agentApproveToken` | Approve an ERC-20 allowance |
| `brickken tx prepare --method <name>` | any | Raw method call — any backend method |

Key flags: `--chain 8453`, `--signer-address <wallet>`, `--json`, `--execute`, `--file <json>` (nested payloads), `--env production` (or `--base-url <api root>`). For `create-token --execute`, set `--rpc-url`, `BRICKKEN_RPC_URL`, or `BKN_RPC_URL` when the CLI must recover `tokenAddress` on Base. Output JSON exposes `prepared.transactions[]`, `prepared.txId`, `prepared.info.agentUuid`, `prepared.info.agentURI`, `sent.txHash`, and `tokenAddress` (after `create-token --execute` when receipt lookup succeeds).

## Orchestration

Pick a path from [Surface Routing](#surface-routing). `signerAddress` must equal the wallet that will broadcast — on Path A that's the Base Account, on Path B the EOA behind the key.

### Path A — Base Account via `send_calls`

1. `get_wallets` → the Base Account address (use as `signerAddress`, `chainId: "8453"`).
2. Build calldata: `POST /prepare-transactions` (harness HTTP / `web_request`) or Brickken MCP `prepare_transactions`, **without** executing. Use `agent_*` only after `get_config` confirms `hasPrivateKey === false`.
3. Pay the **prepare** x402 invoice with Base MCP's x402 capability if it can settle Brickken's EIP-3009 invoice from the Base Account. If settlement fails, stop and report that Path A is unavailable on the current surface.
4. Map `transactions[]` → `send_calls` (see [Submission](#submission)). For multi-step results (e.g. approve + action), pass them as one batch in order.
5. User approves the `send_calls` request; poll status (see `../references/approval-mode.md`). Report success only after the status tool confirms it.

### Path B — Brickken self-executes (CLI / MCP)

1. Set `BRICKKEN_PRIVATE_KEY` (alias: `BKN_PRIVATE_KEY`). The EOA must hold USDC for x402 and native gas on the target chain unless Brickken confirms sponsorship.
2. Run the command with `--execute --json`, e.g. `brickken --env production agent register --chain 8453 --signer-address $WALLET --name … --image … --x402-support true --execute --json`. This pays **prepare + send** x402, signs locally, and broadcasts through Brickken's backend.
3. Parse `sent.txHash`; for `create-token`, capture `tokenAddress`; for `register`, capture `prepared.info.agentUuid` and reuse it in `set-uri` / `set-metadata`. Don't continue `create-token` → `mint` unless `tokenAddress` is present.

> `agentGiveFeedback` returned a backend **500** during June 2026 sandbox testing — re-test before featuring feedback in a happy path, and surface the error rather than retrying blindly.

## Submission

**Path A → `send_calls`** (EIP-5792 batched calls; see `../references/batch-calls.md`). Map each prepared transaction into a call:

```
transactions[i].to    → calls[i].to
transactions[i].data  → calls[i].data
transactions[i].value → calls[i].value   (default "0x0")
```

Call `send_calls` with `chain: "base"` (map `chainId 8453` → the Base MCP chain string `base`) and the `calls` array in the returned order — any approval precedes the action it unlocks. Drop `gasLimit`/`nonce`/`chainId` from the items; the Base Account fills them. Normalize `value` and `data` to `0x`-prefixed hex (default `value` to `"0x0"`); if Brickken returns `value` as a decimal string or a `{type:"BigNumber",hex}` object, convert to hex wei first. The prepare-fee x402 payment is a **separate step before** `send_calls`, not part of it. Follow the approval/polling flow in `../references/approval-mode.md`.

**Path B → `none`.** The CLI / Brickken MCP submits to Brickken's own backend (which broadcasts after the x402 send payment); nothing routes through a Base MCP write tool.

## Example Prompts

**"Register my agent on Base."** (Path A)
1. `get_wallets` → Base Account address.
2. `POST /prepare-transactions` `{ method: "agentRegister", chainId: "8453", signerAddress: <address>, name, description, image, x402Support: true, active: true }`; pay the prepare x402.
3. Map `transactions[]` → `send_calls(chain: "base", calls)`.
4. User approves → poll status → report the agent identity (`info.agentUuid`, `info.agentURI`).

**"Launch an agent token called RAGT and mint 1000 to me."** (Path B / CLI — agent-token deploy is the priciest call; confirm cost first)
1. Confirm with the user: `agentCreateToken` ≈ **$9.99 USDC** + deploy gas on mainnet (see [Risks & Warnings](#risks--warnings)).
2. `brickken --env production create-token --chain 8453 --signer-address $WALLET --name "Research Agent Token" --symbol RAGT --agent-wallet $WALLET --premint 1000 --decimals 18 --rpc-url $BASE_RPC_URL --execute --json` → capture `tokenAddress` + `sent.txHash`.
3. `brickken --env production mint --chain 8453 --signer-address $WALLET --token-address $TOKEN --to $WALLET --amount 1000 --decimals 18 --execute --json`.

**"Transfer 10 RAGT to 0xabc…."** (Path A)
1. Prepare `{ method: "agentTransferToken", chainId: "8453", signerAddress: <Base Account>, tokenAddress, to: "0xabc…", amount: "10", decimals: "18" }`; pay prepare x402.
2. `send_calls(chain: "base", calls)` → approve → poll.

**Chat-only fallback.** On Claude.ai / ChatGPT with no harness HTTP tool: use the Brickken MCP if installed; otherwise the Brickken host must be allowlisted for `web_request` to POST `prepare-transactions`. If it isn't, tell the user this surface can't reach Brickken and point them to a harness with HTTP tools (e.g. Claude Code). Do not fall back to user-paste — the prepare call is a POST.

## Risks & Warnings

- **`irreversible`** — every action here is an onchain write (identity registration, wallet rotation, token deploy/mint/burn/transfer). They cannot be undone once broadcast. Confirm the target chain is `base` (8453) and the `signerAddress` matches the broadcasting wallet before submitting; never auto-rotate the agent wallet (`agentSetWallet`) without explicit user intent.
- **`pii`** — identity and feedback calls accept emails (`ownerEmail`, feedback `email`) and free-text profile fields that get written onchain / pinned to IPFS. Don't send personal data the user didn't authorize; warn that anything submitted is public and permanent.
- **Cost (x402, mainnet).** Each action is paid in USDC and is **non-refundable**. Path A pays the prepare column, then Base gas through `send_calls`; Path B pays prepare + send USDC plus native gas from the EOA unless Brickken confirms sponsorship. Always state the USDC cost and get confirmation before executing — especially `agentCreateToken` (**≈ $9.99** + deploy gas). Never auto-spend. Per-method totals are in [Notes](#notes).
- **Base availability.** These contracts/prices are validated against Brickken's sandbox (Ethereum Sepolia). Confirm the ERC-8004 registries, token factory, and x402 facilitator are live on Base mainnet (8453) before promising execution there.

## Notes

**Mainnet x402 pricing (USDC/call, 2 calls per action).** Path A = Prepare only + Base gas; Path B = Total + native gas where required.

| Method | Prepare | Send | Total | Extra |
|---|---|---|---|---|
| `agentRegister` | 0.50 | 0.49 | 0.99 | |
| `agentSetURI` | 0.25 | 0.24 | 0.49 | + IPFS |
| `agentSetMetadata` | 0.25 | 0.24 | 0.49 | |
| `agentSetWallet` | 0.50 | 0.49 | 0.99 | |
| `agentGiveFeedback` | 0.13 | 0.12 | 0.25 | |
| `agentRevokeFeedback` | 0.13 | 0.12 | 0.25 | |
| `agentAppendFeedbackResponse` | 0.25 | 0.24 | 0.49 | + IPFS |
| `agentCreateToken` | 5.00 | 4.99 | 9.99 | + deploy gas (high) |
| `agentMintToken` | 0.05 | 0.05 | 0.10 | + ERC-20 gas |
| `agentBurnToken` | 0.03 | 0.02 | 0.05 | + ERC-20 gas |
| `agentTransferToken` | 0.03 | 0.02 | 0.05 | + ERC-20 gas |
| `agentTransferFromToken` | 0.03 | 0.02 | 0.05 | + ERC-20 gas |
| `agentApproveToken` | 0.02 | 0.01 | 0.03 | + ERC-20 gas |

Sandbox / Sepolia is a flat ~$0.01 ref price per call — do not quote it for mainnet.

- **x402 mechanics.** The 402 carries a `PAYMENT-REQUIRED` header; payment is a base64 `X-Payment` header wrapping an EIP-3009 `TransferWithAuthorization` USDC signature over `{from, to, value, validAfter, validBefore, nonce}`. Path B signs this with the EOA key. Path A relies on Base MCP's x402 capability to sign it from the Base Account — **a smart-contract wallet signs via ERC-1271, not EOA ECDSA**, so confirm Base MCP + Brickken's facilitator settle this on your surface before treating Path A as keyless.
- **Path A vs B economics.** Path A = prepare USDC + Base gas (Base Account broadcasts). Path B = full USDC total + native gas from the EOA unless Brickken confirms sponsorship (Brickken's backend broadcasts the locally signed transaction after the send-side x402 payment). Path A skips Brickken's `send-transactions` fee; the IPFS upload for `register`/`set-uri`/`append-response` happens at **prepare**, so a Path-A broadcast is functionally complete.
- **Chains.** Brickken maps decimal `8453` → internal hex `2105`; pass `8453` (or `0x2105`). Brickken's testnet is **Ethereum Sepolia (11155111)**, which is *not* Base's `base-sepolia` (84532) — there is no shared testnet, so this plugin targets `chains: [base]` (mainnet) only.
- **Reference addresses (Sepolia, for orientation only):** identity registry `0x8004A818BFB912233c491871b3d84c89A494BD9e`, reputation registry `0x8004B663056A597Dffe9eCcC1965A193B7388713`, agent-token factory `0xB082876148de3a8372d5fa333a9364f9eD16354B`. Get Base addresses from the `prepare` response `info`, not these.
- **CLI is x402-only** — it ignores `BRICKKEN_API_KEY`/`BKN_API_KEY`. Both `prepare` and `send` are x402-priced, so an executed command costs the Total above.
