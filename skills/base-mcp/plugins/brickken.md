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
  externalMcp: { name: brickken, url: https://mcp.brickken.com/mcp }
  cliPackage: npx brickken-cli
auth: none
risk: [irreversible, pii]
---

# Brickken Plugin

> [!IMPORTANT]
> Run Base MCP onboarding first (see `SKILL.md`). **Building calldata with Brickken is free** — the x402 USDC fee applies only when **Brickken broadcasts** the transaction (the send step, Path B). A payer holding USDC on the target chain is therefore needed only for Path B (CLI/MCP self-execute); Path A (Base Account via `send_calls`) pays only Base gas. The Base Account address is fetched lazily via `get_wallets` when a call needs it.

## Overview

Brickken puts the **ERC-8004** agent stack onchain: a registry for **agent identity**, a registry for **reputation/feedback**, and an **agent-owned ERC-20** factory for launching and managing agent tokens. This plugin covers those agent methods on Base. Brickken does not execute through one fixed route — it **builds the unsigned calldata** for each action, and you choose how it lands onchain:

- **Path A — Base Account via `send_calls`.** Brickken builds the calldata for free; the user's Base Account signs and broadcasts it through `send_calls`. No Brickken fee — only Base gas. Submission tool: **`send_calls`**.
- **Path B — Brickken self-executes (key-based).** The `brickken` CLI (or the Brickken MCP with a `privateKey`) signs with a local EOA key and broadcasts through Brickken's backend, paying the x402 **send** fee. Submission tool: **`none`**.

Both are first-class; pick per surface in [Surface Routing](#surface-routing). **Preparing transactions (building calldata) is free**; the x402 USDC fee (EIP-3009 `TransferWithAuthorization`) is charged once, at the **send** step, and only when Brickken broadcasts (Path B). Path A pays no Brickken fee (just Base gas via `send_calls`); Path B pays the send fee plus native gas from the EOA unless Brickken confirms sponsorship. See [Risks & Warnings](#risks--warnings) for per-method costs.

## Detection

The Brickken MCP path is available only if the harness exposes Brickken tools (`agent_register`, `agent_create_token`, `prepare_transactions`, …). If no `agent_*` tool is callable, the MCP is not installed — use the CLI (Path B, shell required). Do not assume the MCP is present. For Path A, prefer `prepare_transactions`; `agent_*` tools may auto-execute when the Brickken MCP session has a `privateKey`.

## Installation

Two routes reach Brickken; install only what your surface uses.

**Brickken CLI (Path B, needs a shell).** No install step — run via `npx`:

```bash
npx brickken-cli --help          # or: npm i -g brickken-cli  →  brickken --help
```

The CLI is **x402-only**. Provide an EOA key for local transaction signing, the x402 **send** payment, and native gas on the target chain unless Brickken confirms sponsorship:

```bash
export BRICKKEN_PRIVATE_KEY=0x... # alias: BKN_PRIVATE_KEY
```

**Brickken MCP (optional, for the MCP path).** Remote MCP at `https://mcp.brickken.com/mcp`. Add it alongside Base MCP, e.g. in Claude Code:

```bash
claude mcp add --transport http brickken https://mcp.brickken.com/mcp
```

For other harnesses use the same URL in the connector/`mcpServers` config. A session that should self-execute (Path B via MCP) must be given a `privateKey` through the MCP's `configure` tool.

## Surface Routing

| Step | Harness with shell (Claude Code, Codex, Cursor) | Shell-less (Claude.ai, ChatGPT) |
|---|---|---|
| **Build calldata** (prepare, free) | Brickken MCP `prepare_transactions`, or `brickken` CLI prepare-only (`--json`, no `--execute`) | Brickken MCP `prepare_transactions` |
| **Execute the action** | Path A `send_calls`, or Path B `brickken … --execute` (pays the send x402) | Path A `send_calls` |

**Shell-less / chat-only:** Path B's CLI is unavailable without a shell — do not improvise it. Use Path A (`send_calls`) or the Brickken MCP. For Path A through Brickken MCP, call `get_config` first; use `prepare_transactions` or confirm `hasPrivateKey === false` before calling `agent_*`, because `agent_*` tools auto-execute when a `privateKey` is configured. Building calldata is free, so the only x402 payment is the send fee on Path B. If the Brickken MCP isn't installed and there's no shell for the CLI, this surface can't reach Brickken — point the user to a harness with the Brickken MCP or a shell.

## Methods

The build-calldata call — Brickken MCP `prepare_transactions` (or `brickken tx prepare`) — takes a `method` plus its args and returns the unsigned transactions (free, no payment):

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

The **send** step (Brickken MCP `send_transactions`, or CLI `--execute`) is used **only by Path B** — it is where Brickken broadcasts and the x402 send fee applies. Path A skips it: `send_calls` broadcasts the prepared calldata instead.

## Commands

Path B. CLI ↔ backend method. Every command is **prepare-only by default** (free); add `--execute` to prepare → sign locally → send → pay the send x402 in one step. Add `--json` for machine-readable output.

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

Key flags: `--chain 8453`, `--signer-address <wallet>`, `--json`, `--execute`, `--file <json>` (nested payloads), `--env production`. For `create-token --execute`, set `--rpc-url`, `BRICKKEN_RPC_URL`, or `BKN_RPC_URL` when the CLI must recover `tokenAddress` on Base. Output JSON exposes `prepared.transactions[]`, `prepared.txId`, `prepared.info.agentUuid`, `prepared.info.agentURI`, `sent.txHash`, and `tokenAddress` (after `create-token --execute` when receipt lookup succeeds).

## Orchestration

Pick a path from [Surface Routing](#surface-routing). `signerAddress` must equal the wallet that will broadcast — on Path A that's the Base Account, on Path B the EOA behind the key.

### Path A — Base Account via `send_calls`

1. `get_wallets` → the Base Account address (use as `signerAddress`, `chainId: "8453"`).
2. Build calldata (free): Brickken MCP `prepare_transactions`, **without** executing. Use `agent_*` only after `get_config` confirms `hasPrivateKey === false`.
3. Map `transactions[]` → `send_calls` (see [Submission](#submission)). For multi-step results (e.g. approve + action), pass them as one batch in order.
4. User approves the `send_calls` request; poll status (see `../references/approval-mode.md`). Report success only after the status tool confirms it.

### Path B — Brickken self-executes (CLI / MCP)

1. Set `BRICKKEN_PRIVATE_KEY` (alias: `BKN_PRIVATE_KEY`). The EOA must hold USDC for the x402 **send** fee and native gas on the target chain unless Brickken confirms sponsorship.
2. Run the command with `--execute --json`, e.g. `brickken --env production agent register --chain 8453 --signer-address $WALLET --name … --image … --x402-support true --execute --json`. This builds the calldata (free), signs locally, broadcasts through Brickken's backend, and pays the **send** x402.
3. Parse `sent.txHash`; for `create-token`, capture `tokenAddress`; for `register`, capture `prepared.info.agentUuid` and reuse it in `set-uri` / `set-metadata`. Don't continue `create-token` → `mint` unless `tokenAddress` is present.

> `agentGiveFeedback` returned a backend **500** during June 2026 sandbox testing — re-test before featuring feedback in a happy path, and surface the error rather than retrying blindly.

## Submission

**Path A → `send_calls`** (EIP-5792 batched calls; see `../references/batch-calls.md`). Map each prepared transaction into a call:

```
transactions[i].to    → calls[i].to
transactions[i].data  → calls[i].data
transactions[i].value → calls[i].value   (default "0x0")
```

Call `send_calls` with `chain: "base"` (map `chainId 8453` → the Base MCP chain string `base`) and the `calls` array in the returned order — any approval precedes the action it unlocks. Drop `gasLimit`/`nonce`/`chainId` from the items; the Base Account fills them. Normalize `value` and `data` to `0x`-prefixed hex (default `value` to `"0x0"`); if Brickken returns `value` as a decimal string or a `{type:"BigNumber",hex}` object, convert to hex wei first. Building the calldata is free, so `send_calls` is the only step on Path A (plus Base gas). Follow the approval/polling flow in `../references/approval-mode.md`.

**Path B → `none`.** The CLI / Brickken MCP submits to Brickken's own backend (which broadcasts after the x402 send payment); nothing routes through a Base MCP write tool.

## Example Prompts

**"Register my agent on Base."** (Path A)
1. `get_wallets` → Base Account address.
2. Brickken MCP `prepare_transactions` `{ method: "agentRegister", chainId: "8453", signerAddress: <address>, name, description, image, x402Support: true, active: true }` (free).
3. Map `transactions[]` → `send_calls(chain: "base", calls)`.
4. User approves → poll status → report the agent identity (`info.agentUuid`, `info.agentURI`).

**"Launch an agent token called RAGT and mint 1000 to me."** (Path B / CLI — agent-token deploy is the priciest call; confirm cost first)
1. Confirm with the user: `agentCreateToken` ≈ **$9.98 USDC** (send fee) + deploy gas on mainnet (see [Risks & Warnings](#risks--warnings)).
2. `brickken --env production create-token --chain 8453 --signer-address $WALLET --name "Research Agent Token" --symbol RAGT --agent-wallet $WALLET --premint 1000 --decimals 18 --rpc-url $BASE_RPC_URL --execute --json` → capture `tokenAddress` + `sent.txHash`.
3. `brickken --env production mint --chain 8453 --signer-address $WALLET --token-address $TOKEN --to $WALLET --amount 1000 --decimals 18 --execute --json`.

**"Transfer 10 RAGT to 0xabc…."** (Path A)
1. Prepare (free) `{ method: "agentTransferToken", chainId: "8453", signerAddress: <Base Account>, tokenAddress, to: "0xabc…", amount: "10", decimals: "18" }`.
2. `send_calls(chain: "base", calls)` → approve → poll.

**Chat-only fallback.** On Claude.ai / ChatGPT with no shell: use the Brickken MCP (`prepare_transactions` → `send_calls`). If the Brickken MCP isn't installed, this surface can't reach Brickken — point the user to a harness with the Brickken MCP or a shell (e.g. Claude Code). Do not fall back to user-paste.

## Risks & Warnings

- **`irreversible`** — every action here is an onchain write (identity registration, wallet rotation, token deploy/mint/burn/transfer). They cannot be undone once broadcast. Confirm the target chain is `base` (8453) and the `signerAddress` matches the broadcasting wallet before submitting; never auto-rotate the agent wallet (`agentSetWallet`) without explicit user intent.
- **`pii`** — identity and feedback calls accept emails (`ownerEmail`, feedback `email`) and free-text profile fields that get written onchain / pinned to IPFS. Don't send personal data the user didn't authorize; warn that anything submitted is public and permanent.
- **Cost (x402, mainnet).** Building calldata (prepare) is **always free**. The x402 fee applies only when Brickken broadcasts: **Path A pays no Brickken fee** (the Base Account broadcasts via `send_calls` — only Base gas), while **Path B pays the x402 send fee** plus native gas from the EOA unless Brickken confirms sponsorship. The send fee is **non-refundable**. Always state the USDC cost and get confirmation before executing on Path B — especially `agentCreateToken` (**≈ $9.98** + deploy gas). Never auto-spend. Per-method send fees are in [Notes](#notes).
- **Base availability.** These contracts/prices are validated against Brickken's sandbox (Ethereum Sepolia). Confirm the ERC-8004 registries, token factory, and x402 facilitator are live on Base mainnet (8453) before promising execution there.

## Notes

**Mainnet x402 pricing (USDC/action).** Building calldata (prepare) is **free**. The fee below is the **send** fee, charged once and only when Brickken broadcasts (Path B). On Path A the same actions cost no Brickken fee — only Base gas.

| Method | Send fee | Extra |
|---|---|---|
| `agentRegister` | 0.98 | |
| `agentSetURI` | 0.48 | + IPFS |
| `agentSetMetadata` | 0.48 | |
| `agentSetWallet` | 0.98 | |
| `agentGiveFeedback` | 0.24 | |
| `agentRevokeFeedback` | 0.24 | |
| `agentAppendFeedbackResponse` | 0.48 | + IPFS |
| `agentCreateToken` | 9.98 | + deploy gas (high) |
| `agentMintToken` | 0.10 | + ERC-20 gas |
| `agentBurnToken` | 0.04 | + ERC-20 gas |
| `agentTransferToken` | 0.04 | + ERC-20 gas |
| `agentTransferFromToken` | 0.04 | + ERC-20 gas |
| `agentApproveToken` | 0.02 | + ERC-20 gas |

Sandbox / Sepolia is a flat ~$0.01 ref price per send — do not quote it for mainnet.

- **x402 mechanics.** Only the **send** step is paid. Its 402 carries a `PAYMENT-REQUIRED` header; payment is a base64 `X-Payment` header wrapping an EIP-3009 `TransferWithAuthorization` USDC signature over `{from, to, value, validAfter, validBefore, nonce}`, signed by the EOA key on Path B. Path A never hits a paid step — building calldata is free and the Base Account broadcasts it directly via `send_calls`.
- **Path A vs B economics.** Path A = no Brickken fee + Base gas (the Base Account broadcasts). Path B = the x402 **send** fee + native gas from the EOA unless Brickken confirms sponsorship (Brickken's backend broadcasts the locally signed transaction). The IPFS upload for `register`/`set-uri`/`append-response` happens at **prepare** (free), so a Path-A broadcast is functionally complete with no Brickken charge.
- **Chains.** Brickken maps decimal `8453` → internal hex `2105`; pass `8453` (or `0x2105`). Brickken's testnet is **Ethereum Sepolia (11155111)**, which is *not* Base's `base-sepolia` (84532) — there is no shared testnet, so this plugin targets `chains: [base]` (mainnet) only.
- **Reference addresses (Sepolia, for orientation only):** identity registry `0x8004A818BFB912233c491871b3d84c89A494BD9e`, reputation registry `0x8004B663056A597Dffe9eCcC1965A193B7388713`, agent-token factory `0xB082876148de3a8372d5fa333a9364f9eD16354B`. Get Base addresses from the `prepare` response `info`, not these.
- **CLI is x402-only.** Only the **send** step is priced — preparing calldata is free — so a prepare-only command (no `--execute`) costs nothing, and an executed command costs the send fee above.
