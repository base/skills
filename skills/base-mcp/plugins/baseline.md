---
title: "Baseline Plugin"
description: "Launch Baseline tokens with the Baseline CLI, then submit unsigned calls through Base MCP send_calls."
tags: [token-launches, liquidity, ai-agents]
name: baseline
version: 0.2.0
integration: cli-only
chains: [base, base-sepolia, ethereum]
requires:
  shell: required
  allowlist: []
  externalMcp: null
  cliPackage: "npx @baseline-markets/cli@latest"
auth: none
risk: [low-liquidity, irreversible, local-exec]
---

# Baseline Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before calling any Baseline flow.

## Overview

Baseline is an onchain AMM for leveraged tokens. A Baseline token operates its own liquidity pool, so a creator or agent can launch without managing external LP positions, capture swap fees that would otherwise go to outside liquidity providers, and split those fees between a creator recipient and token stakers. This plugin launches a Baseline token on Ethereum mainnet, Base mainnet, or Base Sepolia by running the Baseline CLI to prepare unsigned launch calls, then submitting those calls through Base MCP's `send_calls`, where the user approves in Base Account.

This is a **CLI-only plugin**: it only works in harnesses with shell/terminal access (Codex, Claude Code, Cursor, or similar). It does not work on chat-only surfaces that cannot run commands. No additional MCP server is required.

**Chains:** Ethereum mainnet (`chainId` `1`, Base MCP chain string `"ethereum"`), Base mainnet (`chainId` `8453`, Base MCP chain string `"base"`), and Base Sepolia (`chainId` `84532`, Base MCP chain string `"base-sepolia"`).

## Installation

No MCP registration or permanent install is required; the CLI runs per call via `npx`.

Use an installed CLI when available:

```bash
baseline launch --help
```

Otherwise invoke the published package:

```bash
npx @baseline-markets/cli@latest launch --help
```

## Surface Routing

Baseline is **CLI-only**. Every launch calldata artifact is built by the Baseline CLI and therefore requires a harness with shell/terminal access.

| Surface | Path |
|---------|------|
| Shell-capable harness (Codex, Claude Code, Cursor, ...) | Run `baseline launch` or `npx @baseline-markets/cli@latest launch`, validate the artifact, submit via `send_calls`. |
| Chat-only surface (no shell) | Not supported. Tell the user this Baseline plugin requires CLI access and stop. **Do not** route through `web_request`, use a user-paste fallback, ask for private keys, or hand-build calldata. |

See [../references/custom-plugins.md](../references/custom-plugins.md) for the CLI-only routing rule.

## Commands

`baseline launch` writes an unsigned call artifact. The artifact is a superset of the `send_calls` payload: `chain` and `calls` are submitted directly, while `chainId`, `account`, and `bToken` are validation and reporting metadata.

```json
{
  "chainId": 84532,
  "chain": "base-sepolia",
  "account": "0xBaseAccount",
  "bToken": "0xBToken",
  "calls": [
    { "to": "0xTarget", "data": "0xCalldata", "value": "0x0" }
  ]
}
```

### Zero-Reserve Pool (ZRP) Launch

Zero-reserve pool launch (`zrp`) is the default mode. It deposits the full BToken supply into the pool without initial reserve liquidity.

Base Sepolia example:

```bash
baseline launch \
  --mode zrp \
  --chain-id 84532 \
  --account "$BASE_MCP_WALLET" \
  --name "$TOKEN_NAME" \
  --symbol "$TOKEN_SYMBOL" \
  --reserve 0xB85885897D297000A74eA2e4711C3Ca729461ABC \
  --total-supply "$TOTAL_SUPPLY" \
  --output .context/launches/baseline-launch.json
```

### Standard Launch

Standard launches include initial reserve liquidity. Require both the initial pool BToken amount and the reserve seed amount.

Base Sepolia example:

```bash
baseline launch \
  --mode standard \
  --chain-id 84532 \
  --account "$BASE_MCP_WALLET" \
  --name "$TOKEN_NAME" \
  --symbol "$TOKEN_SYMBOL" \
  --reserve 0xB85885897D297000A74eA2e4711C3Ca729461ABC \
  --total-supply "$TOTAL_SUPPLY" \
  --initial-pool-btokens "$POOL_BTOKENS" \
  --initial-pool-reserves "$RESERVE_SEED" \
  --output .context/launches/baseline-launch.json
```

### Chain and Reserve Selection

Use the chain ID and approved reserve token for the selected network:

| Network | `--chain-id` | `artifact.chain` | WETH reserve |
|---------|--------------|------------------|--------------|
| Ethereum mainnet | `1` | `ethereum` | `0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2` |
| Base mainnet | `8453` | `base` | `0x4200000000000000000000000000000000000006` |
| Base Sepolia | `84532` | `base-sepolia` | `0xB85885897D297000A74eA2e4711C3Ca729461ABC` |

Treat Ethereum mainnet and Base mainnet as production. Confirm the user explicitly requested production execution before preparing calls on either mainnet.

Do not pass `--execute`, `--private-key`, or `BASELINE_PRIVATE_KEY` in this plugin flow. Base MCP is the only submission path.

### Optional Launch Parameters

Use these flags when the user asks to customize launch ownership or fee routing:

| Flag | Purpose | Default |
|------|---------|---------|
| `--creator <address>` | Creator address recorded on the launch. | Launch account |
| `--fee-recipient <address>` | Address receiving the creator share of swap fees. | Creator |
| `--creator-fee-pct <percent>` | Creator share of swap fees, from `0` to `100`. | `50` |
| `--swap-fee-pct <percent>` | Swap fee charged by the pool. | `1` |
| `--salt <bytes32>` | Deterministic deployment salt. | Zero bytes32 |
| `--reserve-decimals <number>` | Decimal precision for `--initial-pool-reserves`. | `18` |

The remaining fee share goes to token stakers. With the default `--creator-fee-pct 50`, swap fees are split 50% to the creator fee recipient and 50% to stakers.

## Orchestration

### Launch

1. Complete Base MCP onboarding and confirm Base MCP tools are available.
2. Fetch the wallet address only when needed with `get_wallets`; use the in-session Base Account address as `BASE_MCP_WALLET`.
3. Gather token name, symbol, total supply, launch mode, chain, reserve token, creator, fee recipient, swap fee, and creator fee. Default to Base Sepolia `84532` and `zrp` unless the user explicitly chooses otherwise.
4. For `standard`, require both `POOL_BTOKENS` and a nonzero `RESERVE_SEED`. `POOL_BTOKENS` must be less than `TOTAL_SUPPLY` so some supply remains outside the initial pool.
5. Run `baseline launch` with `--output`. If the CLI exits nonzero, fix inputs and rerun; do not salvage partial output.
6. Parse the artifact JSON and validate it before submission:
   - `account` equals the connected Base Account.
   - `chainId` is `1`, `8453`, or `84532`.
   - `chain` is `ethereum`, `base`, or `base-sepolia`.
   - `chain` matches `chainId`.
   - `bToken` is a valid address.
   - `calls` is an ordered array and every call has `to`, `data`, and `value`.
   - No `execution` field is present.
   - `zrp` has three calls; `standard` has four calls.
7. For `chainId` `1` or `8453`, confirm the exact chain, token name, symbol, supply, reserve, fees, creator, and fee recipient immediately before `send_calls`.
8. Submit the calls through `send_calls` as described in [Submission](#submission).
9. Show the returned approval URL as an `[Approve Transaction](<approvalUrl>)` link, include the request ID, print the link as a fallback, and open it with the local shell when the harness supports that.
10. Wait for the user to confirm they approved in Base Account, then poll `get_request_status(requestId)`. If it is still pending, retry with a short delay; never report success until the request is completed.
11. After completion, run `baseline info "$BTOKEN" --chain-id "$CHAIN_ID"` using the artifact `bToken` and `chainId` when the command is available.

## Submission

Submit with Base MCP `send_calls`. Use `artifact.chain` directly and pass `artifact.calls` without editing calldata or changing order:

```json
{
  "chain": "base-sepolia",
  "calls": [
    { "to": "0xTarget", "data": "0xCalldata", "value": "0x0" }
  ]
}
```

Do not include `artifact.account` in the `send_calls` payload; Base MCP uses the connected Base Account session for approval and execution.

Expected call sequences:

- `zrp`: Relay `createBToken`, BToken `approve`, Relay `createPoolFromInvariant`.
- `standard`: Relay `createBToken`, BToken `approve`, reserve `approve`, Relay `createPool`.

Any `send_calls` approval URL follows the standard Base MCP approval flow: show the approval URL as an `[Approve Transaction](<approvalUrl>)` link, include the request ID, print the link as a fallback, wait for the user to approve in Base Account, then poll `get_request_status`. See [../references/approval-mode.md](../references/approval-mode.md) and [../references/batch-calls.md](../references/batch-calls.md).

## Example Prompts

Launch a Base Sepolia test token:

1. Get the Base Account with `get_wallets`.
2. Run the `zrp` Base Sepolia `baseline launch` command with the requested name, symbol, and supply.
3. Validate the artifact and call count.
4. Submit `artifact.calls` to `send_calls` with `chain: artifact.chain`.
5. Wait for approval, poll status, then run `baseline info`.

Launch a standard token with seed liquidity:

1. Require `POOL_BTOKENS` and `RESERVE_SEED`.
2. Run `baseline launch --mode standard`.
3. Confirm the artifact has four ordered calls.
4. Submit the batch with `send_calls`.
5. Wait for approval, poll status, then run `baseline info`.

Launch on Base mainnet:

1. Confirm the user explicitly requested Base mainnet production execution.
2. Use chain ID `8453` and reserve `0x4200000000000000000000000000000000000006`.
3. Validate the artifact carefully before `send_calls`.
4. Submit with `chain: "base"` only after the user confirms the mainnet launch.

Use from a chat-only app:

1. Stop.
2. Explain that this plugin is CLI-only and requires a shell-capable harness.
3. Do not use HTTP, pasted URLs, private keys, or hand-built calldata as a workaround.

## Risks & Warnings

- `low-liquidity`: New token pools may have thin liquidity and volatile prices. Do not imply liquidity depth, execution quality, or market safety beyond the explicit launch inputs.
- `irreversible`: A submitted launch cannot be undone through this plugin. Confirm chain, token name, symbol, supply, reserve, fees, creator, and fee recipient before `send_calls`.
- `local-exec`: The plugin runs the Baseline CLI on the user's machine. Use the installed `baseline` binary when trusted by the user, or the documented `npx @baseline-markets/cli@latest` package invocation.

## Notes

Constants:

```text
ethereum.chain: ethereum
ethereum.chainId: 1
ethereum.reserve: 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2
base.chain: base
base.chainId: 8453
base.reserve: 0x4200000000000000000000000000000000000006
baseSepolia.chain: base-sepolia
baseSepolia.chainId: 84532
baseSepolia.reserve: 0xB85885897D297000A74eA2e4711C3Ca729461ABC
relay: 0xc81Fd894C0acE037d133aF4886550aC8133568E8
zeroBytes32: 0x0000000000000000000000000000000000000000000000000000000000000000
```

Default launch assumptions:

- `zrp` is the default launch mode.
- Swap fee defaults to `1%`; protocol bounds are `0.15%` to `50%`.
- Creator fee share defaults to `50%`.
- Creator defaults to the launch account.
- Fee recipient defaults to creator.
- Salt defaults to zero `bytes32`.
- Reserve decimals default to `18`.
