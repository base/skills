---
title: "Extra Finance xLend Plugin"
description: "Lending on Extra Finance xLend via the extrafi-prepare CLI → send_calls on Base."
tags: [lending, borrowing, yield]
name: extrafi-xlend
version: 0.2.0
integration: cli-only
chains: [base]
requires:
  shell: required
  allowlist: []
  externalMcp: null
  cliPackage: npx extrafi-prepare
auth: none
risk: [liquidation, irreversible]
---

# Extra Finance xLend Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before calling any Extra Finance xLend command. Fetch the user's wallet address only when a flow actually needs it, such as position reads or write preparation.

## Overview

Extra Finance xLend is an Aave V3-forked lending market on Base supporting USDC, WETH, wstETH, cbETH, and cbBTC. This plugin uses the `extrafi-prepare` CLI to query market rates and user positions and to build **unsigned transaction batches** for supply, withdraw, borrow, and repay operations, which are submitted through Base MCP's `send_calls`, where the user approves in Base Account. The CLI never signs and never broadcasts.

This is a **CLI-only plugin**: it only works in harnesses with shell/terminal access (Claude Code, Codex, Cursor, or similar). No additional MCP server is required.

**Chain:** Base mainnet only (`chainId` `8453`, Base MCP chain string `"base"`).

## Installation

No MCP registration or permanent install is required; the CLI runs per call via `npx extrafi-prepare`.

## Surface Routing

| Surface | Path |
|---|---|
| Shell-capable harness (Claude Code, Codex, Cursor) | Run `npx extrafi-prepare` commands, submit via `send_calls`. |
| Chat-only surface (Claude.ai, ChatGPT) | **Stop.** The CLI cannot run without a shell — tell the user to use the Extra Finance web UI or a shell-capable harness. Do not improvise a `web_request` workaround. |

## Commands

### Read commands

Query protocol state and user positions:

```bash
# Read protocol market rates and APYs
npx extrafi-prepare rates

# Read single reserve details (USDC, WETH, wstETH, cbETH, cbBTC)
npx extrafi-prepare single-reserve --asset USDC

# Read user positions, health factor, and collateral details
npx extrafi-prepare positions --from <address>
```

Market reads return active reserves, collateral factors, borrow/supply APYs, and total TVL.

### Prepare commands

Verbs: `supply`, `withdraw`, `borrow`, `repay`.

```bash
# Prepare a supply operation
npx extrafi-prepare supply --asset USDC --amount 100 --from <address>

# Prepare a withdrawal operation
npx extrafi-prepare withdraw --asset USDC --amount 50 --from <address>

# Prepare a borrow operation
npx extrafi-prepare borrow --asset USDC --amount 25 --from <address>

# Prepare a repay operation
npx extrafi-prepare repay --asset USDC --amount 25 --from <address>
```

### Key parameters

| Field | Notes |
|-------|-------|
| `--asset` | Symbol: `USDC`, `WETH`, `wstETH`, `cbETH`, `cbBTC` |
| `--amount` | Human-readable string, e.g. `100` |
| `--from` | User's wallet address (from `get_wallets`) |

## Orchestration

```
get_wallets -> user address
extrafi-prepare read command -> query market rates/positions
extrafi-prepare prepare command -> PreparedOperation JSON
review summary, simulationOk, outcome, warnings, transactions
send_calls(chain="base", calls from transactions[]) -> approval URL + request ID
user approves
get_request_status(request ID) -> confirmed
```

`extrafi-prepare` commands simulate by default. Check `simulationOk` before presenting an approval link. If `simulationOk` is `false`, inspect and report the revert reason instead of submitting the batch.

Before preparing a borrow, read the user's positions first and verify the health factor leaves room for the new debt (see [Risks & Warnings](#risks--warnings)).

## Submission

Writes land on Base MCP's **`send_calls`**. `extrafi-prepare` outputs a JSON payload with a `transactions` array:

```json
{
  "simulationOk": true,
  "transactions": [
    { "step": "approve", "to": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "data": "0x095d1a5b...", "value": "0x0" },
    { "step": "supply",  "to": "0x...", "data": "0x6156e79f...", "value": "0x0" }
  ]
}
```

Map the transactions directly to `send_calls`, preserving order:

```json
{
  "chain": "base",
  "calls": [
    {
      "to": "<transaction.to>",
      "value": "<transaction.value or 0x0>",
      "data": "<transaction.data>"
    }
  ]
}
```

`send_calls` returns an approval URL and request ID; follow the approval/polling flow in [references/approval-mode.md](../references/approval-mode.md).

## Example Prompts

**"Supply 100 USDC on xLend"**

1. `get_wallets` → address
2. Run `npx extrafi-prepare supply --asset USDC --amount 100 --from <address>`
3. Check JSON: `simulationOk` is `true`
4. `send_calls(chain="base", calls from transactions[])`
5. User approves → `get_request_status(requestId)`

**"Borrow 50 USDC against my collateral on Extra Finance"**

1. `get_wallets` → address
2. Run `npx extrafi-prepare positions --from <address>` → verify health factor > 1.5
3. Run `npx extrafi-prepare borrow --asset USDC --amount 50 --from <address>`
4. Check JSON: `simulationOk` is `true`
5. `send_calls(chain="base", calls from transactions[])`
6. User approves → `get_request_status(requestId)`

**"What are my xLend positions and health factor?"**

1. `get_wallets` → address
2. Run `npx extrafi-prepare positions --from <address>`
3. Show supply balances, borrow balances, and health factor

## Risks & Warnings

- **Liquidation** — borrow positions can be liquidated when the health factor drops below 1. Always read positions and surface the health factor before preparing a borrow or a collateral withdrawal, and warn the user when the resulting health factor would fall under 1.5.
- **Irreversible writes** — supplies, withdrawals, borrows, and repays are onchain transactions that cannot be undone once approved. Present the operation summary (asset, amount, resulting health factor) before submitting `send_calls`.

### Health factor guide

| Value | Status |
|-------|--------|
| `> 1.5` | Healthy |
| `1.1 – 1.5` | Caution |
| `< 1.1` | Liquidation risk |
| `null / 0` | No active borrows |

## Notes

- **Collateral enablement** — supplying assets automatically sets them as collateral unless the reserve's loan-to-value (LTV) is 0.
- **Liquidation threshold** — max borrow capacity is determined by the weighted average collateral factor of supplied assets.
- **WETH/ETH** — native ETH is supported; the runner handles wrapping/unwrapping internally.
