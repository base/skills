---
title: "Brickken Plugin"
description: "ERC-8004 agent identity, reputation, and agent-owned ERC-20s on Base — Brickken builds unsigned calldata for Base MCP send_calls."
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
> Run Base MCP onboarding first (see `SKILL.md`). This plugin uses Brickken only to build **unsigned calldata**. Submit every action through Base MCP `send_calls`; never ask for or use a private key, and never use Brickken as the broadcaster. Building calldata with Brickken is free; the user pays only Base gas when their Base Account broadcasts through `send_calls`. The Base Account address is fetched lazily via `get_wallets` when a call needs it.

## Overview

Brickken puts the **ERC-8004** agent stack onchain: a registry for **agent identity**, a registry for **reputation/feedback**, and an **agent-owned ERC-20** factory for launching and managing agent tokens. This plugin covers those agent methods on Base. Brickken builds the unsigned calldata for each action, then Base MCP lands it onchain:

- Build calldata with Brickken MCP `prepare_transactions` or a prepare-only Brickken CLI command.
- Submit the returned `{ to, data, value }` calls through Base MCP `send_calls`, where the user's Base Account signs and broadcasts after approval.

Submission tool: **`send_calls`**. Brickken self-execution and key-based broadcast are out of scope for this Base MCP plugin.

## Detection

The Brickken MCP path is available only if the harness exposes Brickken tools (`prepare_transactions`, and possibly `agent_register`, `agent_create_token`, …). Do not assume the MCP is present. Prefer `prepare_transactions` because it returns unsigned calldata. If no Brickken prepare tool is callable and the harness has a shell, use the CLI only in prepare-only mode. If neither is available, this surface cannot reach Brickken.

Do not configure or use Brickken signing credentials. If `get_config` reports that signing credentials are present, do not call `agent_*` tools that may auto-execute; use `prepare_transactions` or a fresh Brickken MCP session without signing credentials.

## Installation

Two prepare-only routes reach Brickken; install only what your surface uses.

**Brickken CLI (optional, needs a shell).** No install step — run via `npx`:

```bash
npx brickken-cli --help          # or: npm i -g brickken-cli  →  brickken --help
```

Use the CLI only to prepare unsigned calldata (`--json`, no execute/broadcast option). Do not provide signing credentials; signing and broadcasting belong to Base MCP `send_calls`.

**Brickken MCP (optional, for the MCP path).** Remote MCP at `https://mcp.brickken.com/mcp`. Add it alongside Base MCP, e.g. in Claude Code:

```bash
claude mcp add --transport http brickken https://mcp.brickken.com/mcp
```

For other harnesses use the same URL in the connector/`mcpServers` config. Do not configure signing credentials.

## Surface Routing

| Step | Harness with shell (Claude Code, Codex, Cursor) | Shell-less (Claude.ai, ChatGPT) |
|---|---|---|
| **Build calldata** (prepare, free) | Brickken MCP `prepare_transactions`, or `brickken` CLI prepare-only (`--json`, no execute/broadcast option) | Brickken MCP `prepare_transactions` |
| **Execute the action** | Base MCP `send_calls` | Base MCP `send_calls` |

**Shell-less / chat-only:** Use Brickken MCP `prepare_transactions` → Base MCP `send_calls`. If the Brickken MCP isn't installed and there's no shell for prepare-only CLI access, this surface can't reach Brickken — point the user to a harness with the Brickken MCP or a shell. Do not ask the user for a private key or try to self-broadcast through Brickken.

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

Brickken broadcast is intentionally out of scope. `send_calls` broadcasts the prepared calldata instead.

## Commands

Prepare-only CLI reference. CLI ↔ backend method. Every command must run in prepare-only mode; add `--json` for machine-readable output.

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

Key flags: `--chain 8453`, `--signer-address <Base Account>`, `--json`, `--file <json>` (nested payloads), `--env production`. Output JSON exposes `prepared.transactions[]`, `prepared.txId`, `prepared.info.agentUuid`, and `prepared.info.agentURI`. Never provide signing credentials or ask Brickken to broadcast.

## Orchestration

`signerAddress` must equal the wallet that will broadcast: the user's Base Account.

### Base Account via `send_calls`

1. `get_wallets` → the Base Account address (use as `signerAddress`, `chainId: "8453"`).
2. Build calldata (free): Brickken MCP `prepare_transactions`, or CLI prepare-only with `--json` and no execute/broadcast option.
3. Map `transactions[]` → `send_calls` (see [Submission](#submission)). For multi-step results (e.g. approve + action), pass them as one batch in order.
4. User approves the `send_calls` request; poll status (see `../references/approval-mode.md`). Report success only after the status tool confirms it.

> `agentGiveFeedback` returned a backend **500** during June 2026 sandbox testing — re-test before featuring feedback in a happy path, and surface the error rather than retrying blindly.

## Submission

Use Base MCP `send_calls` (EIP-5792 batched calls; see `../references/batch-calls.md`). Map each prepared transaction into a call:

```
transactions[i].to    → calls[i].to
transactions[i].data  → calls[i].data
transactions[i].value → calls[i].value   (default "0x0")
```

Call `send_calls` with `chain: "base"` (map `chainId 8453` → the Base MCP chain string `base`) and the `calls` array in the returned order — any approval precedes the action it unlocks. Drop `gasLimit`/`nonce`/`chainId` from the items; the Base Account fills them. Normalize `value` and `data` to `0x`-prefixed hex (default `value` to `"0x0"`); if Brickken returns `value` as a decimal string or a `{type:"BigNumber",hex}` object, convert to hex wei first. Building the calldata is free, so `send_calls` is the only submission step (plus Base gas). Follow the approval/polling flow in `../references/approval-mode.md`.

## Example Prompts

**"Register my agent on Base."**
1. `get_wallets` → Base Account address.
2. Brickken MCP `prepare_transactions` `{ method: "agentRegister", chainId: "8453", signerAddress: <address>, name, description, image, x402Support: true, active: true }` (free).
3. Map `transactions[]` → `send_calls(chain: "base", calls)`.
4. User approves → poll status → report the agent identity (`info.agentUuid`, `info.agentURI`).

**"Launch an agent token called RAGT and mint 1000 to me."**
1. Confirm with the user that token deployment spends Base gas on mainnet.
2. `get_wallets` → Base Account address.
3. Prepare `agentCreateToken` with `signerAddress: <Base Account>`, token metadata, `agentWallet: <Base Account>`, and any supported premint fields.
4. Map `transactions[]` → `send_calls(chain: "base", calls)` → approve → poll.
5. Capture `tokenAddress` from the prepare response or confirmed transaction receipt before any later mint/transfer. If a separate mint is still needed, prepare `agentMintToken` and submit it through `send_calls`.

**"Transfer 10 RAGT to 0xabc…."**
1. Prepare (free) `{ method: "agentTransferToken", chainId: "8453", signerAddress: <Base Account>, tokenAddress, to: "0xabc…", amount: "10", decimals: "18" }`.
2. `send_calls(chain: "base", calls)` → approve → poll.

**Chat-only fallback.** On Claude.ai / ChatGPT with no shell: use the Brickken MCP (`prepare_transactions` → `send_calls`). If the Brickken MCP isn't installed, this surface can't reach Brickken — point the user to a harness with the Brickken MCP or a shell that can prepare unsigned calldata. Do not fall back to user-paste.

## Risks & Warnings

- **`irreversible`** — every action here is an onchain write (identity registration, wallet rotation, token deploy/mint/burn/transfer). They cannot be undone once broadcast. Confirm the target chain is `base` (8453) and the `signerAddress` matches the broadcasting wallet before submitting; never auto-rotate the agent wallet (`agentSetWallet`) without explicit user intent.
- **`pii`** — identity and feedback calls accept emails (`ownerEmail`, feedback `email`) and free-text profile fields that get written onchain / pinned to IPFS. Don't send personal data the user didn't authorize; warn that anything submitted is public and permanent.
- **Cost (mainnet gas).** Building calldata (prepare) is **always free**. This plugin does not use Brickken's paid broadcast path, so there is no Brickken broadcast fee. The user still pays Base gas through `send_calls`; token deployment can be relatively expensive. Preview the transaction and get confirmation before submitting. Never auto-spend.
- **Base availability.** These contracts are validated against Brickken's sandbox (Ethereum Sepolia). Confirm the ERC-8004 registries and token factory are live on Base mainnet (8453) before promising execution there.

## Notes

- **Signing belongs to Base Account.** Never ask for or use a private key or other signing credential. If a Brickken surface offers broadcast, do not use it for this Base MCP plugin.
- **Prepare economics.** Preparing calldata is free. The IPFS upload for `register`/`set-uri`/`append-response` happens at prepare time, so a Base MCP `send_calls` broadcast is functionally complete with no Brickken send charge.
- **Chains.** Brickken maps decimal `8453` → internal hex `2105`; pass `8453` (or `0x2105`). Brickken's testnet is **Ethereum Sepolia (11155111)**, which is *not* Base's `base-sepolia` (84532) — there is no shared testnet, so this plugin targets `chains: [base]` (mainnet) only.
- **Reference addresses (Sepolia, for orientation only):** identity registry `0x8004A818BFB912233c491871b3d84c89A494BD9e`, reputation registry `0x8004B663056A597Dffe9eCcC1965A193B7388713`, agent-token factory `0xB082876148de3a8372d5fa333a9364f9eD16354B`. Get Base addresses from the `prepare` response `info`, not these.
- **CLI usage.** The CLI is allowed only for prepare-only calldata generation. Prepare-only commands cost nothing and must still be submitted through Base MCP `send_calls`.
