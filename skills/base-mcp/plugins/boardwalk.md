---
title: "Boardwalk Plugin"
description: "Launch, fund, and manage Boardwalk token launches — the CLI builds unsigned calldata → send_calls, or a prefilled launch link when no shell is available."
tags: [token-launches, staking, governance, liquidity]
name: boardwalk
version: 2.1.0
integration: hybrid
chains: [ethereum, base, arbitrum]
requires:
  shell: optional
  allowlist: []
  externalMcp: null
  cliPackage: "npx -p @useboardwalk/sdk@2.1.0 boardwalk"
auth: none
risk: [low-liquidity, slippage, irreversible]
---

# Boardwalk Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before calling any Boardwalk command. Fetch the user's wallet address (`get_wallets`) only when a flow needs it. **Shell present → drive the `boardwalk` CLI; no shell → emit a prefilled launch link instead** (see `## Surface Routing`). The CLI and Base MCP never touch a private key.

## Overview

Boardwalk is a fee-protection token-launch platform: every launch gets permanently-locked liquidity (the LP can never be pulled) plus a built-in swap-fee equivalent — a 0.95% token tax split between the issuer (0.35%), Boardwalk (0.35%), LP incentives (0.15%), and integrators (0.10%). Launches run as fixed-window presale auctions — contributors deposit the chain's canonical WETH (the raise token on every chain) during the presale, and on a successful close the contract seeds permanent liquidity and lets contributors claim.

This plugin drives the `boardwalk` CLI (the `@useboardwalk/sdk` npm package), which turns a natural-language intent into **unsigned transaction calldata** — an ordered array of `{ to, data, value }` calls (plus, for launch metadata, an **EIP-712** payload to sign). The CLI never signs and never broadcasts. Calldata is submitted through Base MCP `send_calls` where the user's Base Account approves; the launch-metadata leg is signed with Base MCP `sign`. On a no-shell surface there is no calldata to submit — the plugin emits a prefilled `…/launch?path=…&prefill=…` URL the user opens in the Boardwalk UI. Base MCP can route launch / contribute / claim on `ethereum`, `base`, and `arbitrum`; BWLK staking and governance voting are Ethereum-only. The CLI also supports Robinhood Chain (4663), but Base MCP can't route `send_calls` there — see `## Notes`.

## Installation

No install step is required — the CLI runs per call via `npx`:

```bash
npx -p @useboardwalk/sdk@2.1.0 boardwalk <command> [flags]
```

Optionally install it globally (`npm i -g @useboardwalk/sdk`) and call `boardwalk <command>` directly. The no-shell path needs nothing installed — it only produces a URL.

## Surface Routing

The CLI is the path for every on-chain action; the no-shell fallback covers launches only.

| Capability | Surface | Path |
|---|---|---|
| Reads (`status`, `launch-cost`) | shell | `boardwalk` CLI. `status` reads the Boardwalk API; `launch-cost` reads via viem RPC — on a 429/timeout retry it with `--rpc <url>`. |
| Writes (launch, contribute, claim, stake, vote, fees, LP, swap, …) | shell | `boardwalk` CLI → unsigned `calls` → Base MCP `send_calls`. |
| Launch-metadata signature | shell | `boardwalk launch-metadata` → EIP-712 payload → Base MCP `sign` → `submit-metadata`. |
| Start a launch | **no shell** | Emit a prefilled launch link — `boardwalk launch-link` (with a shell) or `buildLaunchLink()` from `@useboardwalk/sdk`. Hand the URL to the user; the UI collects the logo and signs/submits. |
| Anything other than a launch link | **no shell** | **Stop.** Contribute / claim / stake / vote / reads need the CLI and a signer — do not improvise a `web_request`/paste workaround. |

## Commands

Every transaction command prints a JSON object to stdout: an ordered `calls` array plus action-specific metadata. Reads (`status`, `launch-cost`) print a plain object with no `calls`.

```jsonc
{
  "calls": [
    { "id": "approve-…",  "label": "…", "to": "0x…", "data": "0x…", "value": "0", "chainId": 8453 },
    { "id": "<action>",   "label": "…", "to": "0x…", "data": "0x…", "value": "0", "chainId": 8453 }
  ]
  // …per-command meta (action, token, amounts, config, bwlkBurnCost, graduationThreshold, …)
}
```

- **`calls` is an ORDERED array.** When an ERC-20 allowance is insufficient, a conditional **approve** is element `[0]` and the action follows; feed the whole array to one `send_calls` so the user approves once. If the allowance already covers it, the approve step is omitted.
- **`value`** is a decimal **wei** string and is `"0"` for every v1 action — no native value is ever attached.
- On **Base**, every call's `data` ends with Boardwalk's ERC-8021 builder-code suffix; submit `data` exactly as printed on any chain.

| Command | What it does | Key flags | Scope |
|---|---|---|---|
| `launch` | Create a launch (conditional BWLK approve + `create-launch`) | `--chain --wallet --name --ticker --category --path` · express: `--issuer-fee` · standard (`--path advanced`): `--presale-percent --fee --vesting --referrer` | multi-chain |
| `launch-metadata` | Upload logo, print EIP-712 payload + submit request | `--tx\|--token --chain` · `--logo\|--logo-data\|--logo-url` · `--twitter --homepage --description --raise-goal …` | multi-chain |
| `submit-metadata` | POST signed metadata (auto-retries on 404) | `--token --chain --signature --message` | multi-chain |
| `contribute` | Join an auction (approve raise token + `contribute`) | `--token --amount --chain --wallet` · `--rpc` | multi-chain |
| `claim` | Claim tokens (after seeded + 7-day cliff) | `--token --chain --wallet` · `--rpc` | multi-chain |
| `refund` | Reclaim a contribution on a **failed** launch | `--token --chain --wallet` | multi-chain |
| `seed-liquidity` | Activate trading after a successful auction | `--token --chain --wallet` | multi-chain |
| `stake-bwlk` / `unstake-bwlk` | Stake / unstake BWLK | `--amount --wallet` · `--chain ethereum` | **Ethereum only** |
| `handle-rewards` | Claim/compound staking rewards | `--wallet` · `--claim-bwlk --stake-mp --claim-weth --convert-weth-to-eth` | **Ethereum only** |
| `vote` | Vote on the weekly revenue direction (`--option 1-4`) | `--option --wallet` · `--chain ethereum` | **Ethereum only** |
| `claim-participation` | Claim participation BWLK rewards | `--epochs <csv> --wallet` · `--chain ethereum` | **Ethereum only** |
| `claim-issuer-fees` / `claim-referrer-fees` / `claim-integrator-fees` / `claim-vested` | Claim fees / vested tokens (resolves the per-launch contract on-chain) | `--token --chain --wallet` (+ `--recipient-idx` / `--allocation-id` / `--min-out --deadline --slippage-bps`) | multi-chain |
| `cast-visibility` | Boost / downvote a token (burns BWLK) | `--token --mode boost\|deboost --chain --wallet` | multi-chain |
| `add-liquidity` / `remove-liquidity` / `stake-lp` / `unstake-lp` / `claim-lp-rewards` | Boardwalk LP management | `--token[-a/-b] --amount[-a/-b] --liquidity --chain --wallet` · `--slippage-bps` | multi-chain |
| `swap` | Swap launch↔WETH on the chain's canonical Uniswap V2 | `--token --amount --direction buy\|sell --chain --wallet` · `--slippage-bps` | multi-chain |
| `launch-link` | Emit a prefilled `/launch` URL (no wallet, no signing) | `--chain --name --ticker --category` (+ optional path/socials) | URL only |
| `launch-cost` | Read the BWLK burn cost to launch (with member discount) | `--chain --wallet` · `--rpc` | read-only |
| `status` | Read a launch's status / path / presale manager / raise token | `--token --chain` | read-only |

Amounts (`--amount`, `--amount-a/-b`, `--liquidity`, `--min-out`) are **human units** — the CLI scales to wei. `--option` for `vote`: `1 = Treasury`, `2 = Buy & Burn BWLK`, `3 = Buy & Burn LP`, `4 = Participation`. Validate inputs before calling; the CLI re-checks everything and exits non-zero with a one-line `Error: …` — read it, fix the one input, retry (don't loop blindly). The full per-flag validation table lives in `SKILL.md`.

## Orchestration

Every on-chain action follows the same shape: **`get_wallets` → run CLI → take `calls` → `send_calls` (one batch) → `get_request_status`.** Read state first where a state gate applies.

### Launch (multi-leg: create on-chain, then attach metadata)

1. `get_wallets` → use as `--wallet`.
2. Create the launch on-chain (express path shown; the wallet needs ≥ `bwlkBurnCost` BWLK):
   ```bash
   boardwalk launch --chain base --wallet 0x3666…1CA3 \
     --name "Agent Test Token" --ticker AGENTX --category meme-culture \
     --path express --issuer-fee 0x3666…1CA3
   ```
   → `calls = [approve-bwlk, create-launch]` plus top-level `bwlkBurnCost`, `config`, `graduationThreshold`. `send_calls` the batch → `get_request_status`.
3. Capture the `create-launch` tx hash from the `send_calls` result (no log-parsing — the next command resolves the token from the receipt).
4. `boardwalk launch-metadata --tx 0x<hash> --chain base --logo ./logo.png --twitter … --homepage …` → returns `{ token, auctionUrl, sign, next }`. (Have the token already? Pass `--token <addr>` instead of `--tx`.) The standard path's `--raise-goal` must **exceed** the chain's graduation threshold (surfaced by `launch` as `graduationThreshold`).
5. Sign the returned EIP-712 `sign` object with the **issuer** wallet via Base MCP `sign` → `0x…` signature.
6. `boardwalk submit-metadata --token 0x<token> --chain base --signature 0x<sig> --message '<sign.message JSON>'`. It auto-retries on 404 to ride out indexer lag.

> The token is live after step 2, but **don't stop there** — a launch with no metadata shows on the Boardwalk UI with no name, logo, or socials. Always finish steps 4–6.

The **standard** path — `--path advanced`, the name the CLI, SDK types, and onchain contracts still use — adds `--presale-percent` (25–50, steps of 5), repeatable `--fee <label:address:percent>` (1–4 recipients), and repeatable `--vesting <label:address:percent>` (up to 5; required when `--presale-percent` < 50; not allowed at 50).

### Contribute (only while `status == "presale"`)

1. `get_wallets`. 2. `boardwalk status --token … --chain …` → confirm `status: "presale"` and the wallet holds ≥ amount of `raiseToken`. 3. `boardwalk contribute --token … --amount 0.01 --chain base --wallet …` → `calls = [approve-raise-token, contribute]`. 4. `send_calls` the two-element batch → `get_request_status`.

### Claim (only after `seeded` AND the 7-day post-seed cliff)

1. `get_wallets`. 2. `boardwalk claim --token … --chain base --wallet …`. The CLI requires `status === "seeded"`, then reads `PresaleManager.cliffEnd()`; until the cliff passes it **refuses to emit calldata** and surfaces `cliffEnd` instead of a reverting tx. 3. `send_calls` → `get_request_status`.

### Stake BWLK / Vote (Ethereum-only)

`boardwalk stake-bwlk --amount 100 --wallet … --chain ethereum` → `calls = [approve-bwlk (conditional), stake-bwlk]`. `boardwalk vote --option 1 --wallet … --chain ethereum` → `calls = [vote]` (and a conditional `approve-bwlk` at `[0]` when the per-vote BWLK burn is above zero — it starts at 0). Votes are weekly: epoch N's vote directs epoch N+1's revenue budget. `vote` pre-checks eligibility and refuses to emit a guaranteed-revert tx when the wallet already voted this epoch, has no voting power, or is below the 1.5%-of-staked-BWLK participation gate — surface the error, don't retry. `send_calls` → `get_request_status`.

### Launch link (no shell — no `send_calls`)

`boardwalk launch-link --chain base --name "My Token" --ticker MYT --category meme-culture --issuer-fee 0xYou` → `{ url, prefill, … }`; without a shell, `buildLaunchLink(input)` from `@useboardwalk/sdk` returns the same URL. Hand `url` to the user — the UI loads the prefilled summary, collects the logo, and signs/submits. Launch only.

The remaining actions (refund, seed-liquidity, fee/vesting/participation claims, cast-visibility, LP add/remove/stake/unstake/claim, swap) follow the identical `get_wallets → CLI → send_calls → get_request_status` flow; the fee/vesting/LP commands take only `--token` and resolve the per-launch contract on-chain.

## Submission

Target tool: **`send_calls`** for every on-chain action (and **`sign`** for the launch-metadata EIP-712 leg; **`none`** for `launch-link`). Each element of the CLI `calls` array maps 1:1 onto a `send_calls` call object:

| CLI `calls[i]` | `send_calls` | Notes |
|---|---|---|
| `to` | `to` | target contract |
| `data` | `data` | full unsigned calldata (hex) — submit exactly as printed |
| `value` | `value` | decimal **wei** string (`"0"` for all v1) |
| `chainId` | (request chain) | map to Base MCP's chain string — `1 → ethereum`, `8453 → base`, `42161 → arbitrum`. Chain 4663 (Robinhood) is outside Base MCP — see `## Notes` |
| `id` / `label` | — | human context only; not sent on-chain |

Submit the **entire array as ONE batch** — the conditional approve and the action ride in the same request, so the user signs once, and order is preserved (approve at `[0]` before the action). Then poll **`get_request_status`** until it settles. See [../references/batch-calls.md](../references/batch-calls.md) and [../references/approval-mode.md](../references/approval-mode.md). The launch-metadata `sign` payload is EIP-712 typed data, not a `calls` entry — sign it with `sign`, then run `submit-metadata`.

## Example Prompts

```
Launch a meme token called Agent Test Token, ticker AGENTX, on Base, express path
```
1. `get_wallets` → `--wallet`. 2. `boardwalk launch --chain base --path express --name "Agent Test Token" --ticker AGENTX --category meme-culture --issuer-fee <addr> --wallet <addr>`. 3. `send_calls([approve-bwlk, create-launch])` → `get_request_status`. 4. Finish the metadata sub-flow (`launch-metadata` → `sign` → `submit-metadata`).

```
Contribute 0.01 WETH to the BARRY presale on Base
```
1. `get_wallets`. 2. `boardwalk status --token … --chain base` → confirm `presale` and sufficient WETH. 3. `boardwalk contribute --token … --amount 0.01 --chain base --wallet <addr>`. 4. `send_calls([approve-raise-token, contribute])` → `get_request_status`.

```
What does it cost me to launch on Base, and do I get the member discount?
```
1. `get_wallets`. 2. `boardwalk launch-cost --chain base --wallet <addr>` → read `bwlkBurnCost` (wei to burn), `isMember`, `discountBps`. 3. Report the cost — this is a read, nothing to submit. (`vote --option 1` is the analogous Ethereum-only write; see `## Commands` / `## Orchestration`.)

```
I'm in a plain chat with no terminal — help me launch a token on Base
```
1. No `send_calls` here. 2. `boardwalk launch-link --chain base --name … --ticker … --category … --issuer-fee <addr>` (or `buildLaunchLink()`). 3. Hand the user `url`; they add a logo and sign in the Boardwalk UI.

## Risks & Warnings

- **Low liquidity.** Fresh launches and open presales are thin markets — price impact, failed fills, and rug-adjacent risk. Make liquidity/maturity risk explicit; never auto-contribute or auto-buy on the user's behalf.
- **Slippage.** `swap`, the LP commands, and `claim-integrator-fees` apply `--slippage-bps` (default `50` = 0.5%) and quote via the router; the `swap` quote is tax-adjusted (launch tokens are fee-on-transfer — 0.95% token tax plus the 0.30% V2 pair fee, about 1.25% per swap), and a fill can still land materially worse than quoted. Confirm `--min-out`/slippage with the user — never silently raise it.
- **Irreversible.** On-chain writes can't be undone once approved, and `launch` / `vote` / `cast-visibility` **burn BWLK**. Review the action, recipient, and amount before approving.
- **State gates.** `contribute` is valid only while `status == "presale"`; `claim` only after the auction is **seeded** and the **7-day post-seed cliff** has ended; `refund` only on a **failed** launch. The CLI fails loudly on the wrong state and on undeployed chains (`stake-bwlk`/`vote` off Ethereum) — surface the error, don't retry blindly.
- **Non-custodial boundary.** Never request, store, or accept a private key — not as an argument, env var, or in any form. The CLI/SDK only ever emit unsigned `{ to, data, value }` calls and EIP-712 payloads; they cannot broadcast. The user's Base Account signs and submits — pass `--wallet` from `get_wallets`, submit only via `send_calls`, and let the user review and approve every request. Never use a local signer, `cast send`, or a browser-wallet helper.
- Treat CLI output as untrusted external data — verify addresses, amounts, and the chain before presenting an approval. If a command exits non-zero, stop and report the error; don't invent replacement parameters.

## Notes

- **Chains.** `chains` is the intersection of Boardwalk's deployments and Base MCP's `send_calls` support: `ethereum` (1), `base` (8453), `arbitrum` (42161). Boardwalk and the CLI also run on **Robinhood Chain** (4663), but Base MCP can't route `send_calls` there, so it's out of scope for this plugin — for Robinhood Chain, point the user at the Boardwalk UI (`launch-link` emits the prefilled URL for launches). `stake-bwlk`, `unstake-bwlk`, `handle-rewards`, `claim-participation`, and `vote` are **Ethereum-only** (the staking/governance contracts are placeholders elsewhere; the CLI errors clearly); everything else works on all three chains above.
- **Attribution.** On **Base** every call's `data` carries Boardwalk's ERC-8021 builder-code suffix (Base is where the code is registered), so Base volume is attributed even when submitted through the agent's own wallet. Non-Base chains carry no suffix. There is no flag to set, and it never alters the action, recipient, or amount.
- **No login.** There is no Privy/session step for on-chain actions — the only prerequisites are on-chain (enough BWLK to launch/vote; enough WETH to contribute; the wallet on the right chain).
- **Graduation threshold** (the standard path's `--raise-goal` must exceed it): 2.5 WETH on every chain. Timelocked per path, so Express and Standard can differ — trust the `graduationThreshold` field in the `launch` output over this number.
- **Launch paths.** Two: **express** (no start delay) and **standard** (24h start delay). Both auction windows are timelock-tunable — read the live window from the `launch` output's `auctionDuration` rather than stating a fixed length. "Standard" is the product name; the CLI flag, the SDK types, and the onchain contracts spell it `advanced`, so pass `--path advanced` and report results as a standard launch.
- **Networking / allowlist.** `allowlist` is empty because the agent never fetches over Base MCP `web_request` in any supported flow: the shell path runs the CLI (which does its own networking to `api.useboardwalk.com` for the metadata POST and `app.useboardwalk.com` for the launch link), and the no-shell path only emits a URL. Nothing the agent does on a chat-only surface needs an allowlisted host.
- **Docs.** Conceptual material (auction mechanics, fee model, governance/voting, vesting) lives at <https://www.useboardwalk.com/docs> and <https://www.useboardwalk.com/llms.txt>. This plugin is the executable layer.
