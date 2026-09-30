---
title: "Umia Plugin"
description: "Discover and trade Umia decision markets and bid in token auctions via the umia-cli or HTTP API; builds unsigned calldata routed through send_calls."
tags: [futarchy, decision-markets, token-auctions, governance, trading]
name: umia
version: 0.3.0
integration: hybrid
chains: [base, base-sepolia, sepolia]
requires:
  shell: optional
  allowlist: ["api.testnet.umia.finance", "api.mainnet.umia.finance"]
  externalMcp: null
  cliPackage: "npx umia-cli@latest"
auth: none
risk: [slippage, low-liquidity, irreversible, local-exec]
---

# Umia Plugin

> [!IMPORTANT]
> Run Base MCP onboarding first (see SKILL.md). Umia is a launchpad protocol:
> projects raise capital through token sales, and decision markets *decide*
> governance questions by trading. This plugin only reads data and builds
> unsigned calls. It never signs or broadcasts outside Base MCP. Never ask for
> or use a private key — get the user's wallet address from Base MCP
> `get_wallets` for `--taker` / `<address>` inputs. Decision markets and token
> sales may be restricted in some jurisdictions, and some auction steps require
> verification: never help circumvent geofencing or verification gates — surface
> the hub link instead. Default env is testnet. Umia is multi-chain — never
> assume a specific chain; run `umia config` to discover the active env's
> chains and addresses.

## Overview

Umia runs decision markets and token auctions across EVM chains (the active
set comes from `umia config` / `GET /api/v1/config` — never assume one). Each
market poses a governance question with 2+ proposals (conditional CPMM pools of ERC6909
virtual tokens); the highest-TWAP proposal above threshold wins and converts
1:1 to real tokens at settlement. Auctions ("token sales") are continuous
clearing auctions whose clearing price rises in steps as the sale fills. The
plugin reads markets/auctions/prices/positions over HTTP and builds **unsigned**
`{ to, value, data }` calldata via the auth-free `/api/v1/calldata/*`
endpoints, then routes every write through Base MCP `send_calls`. With a shell
it uses the `umia` CLI (`npx umia-cli@latest`); on chat-only surfaces it calls
the same HTTP API directly. The CLI is a thin client over that API: it only
*prepares* calls, never executes them.

## Installation

Runs via npx, no global install:

```
npx umia-cli@latest --version
```

Select the environment with `UMIA_ENV=testnet|mainnet` (default `testnet`) or
`--env`. Contract addresses are baked in from the protocol's `contracts.json`
and also served by `GET /api/v1/config`; override any with
`--contract <name>=<addr>`. Other global flags: `--chain-id` (required for
chain-scoped market actions when the env exposes more than one chain — run
`umia config` to list them), `--api-base`, `--json` (machine-readable, always use it when piping
to `send_calls`).

## Surface Routing

| Capability | Harness HTTP / `web_request` | CLI (shell available) | Fallback |
|---|---|---|---|
| Read markets/prices/positions/portfolio | `GET {API}/api/v1/...` | `umia markets/market/prices/positions/portfolio` | Umia hub UI link |
| Read auctions/analytics/ticks/leaderboard/bids | `GET {API}/api/v1/hub/fundraises...` | `umia auctions`, `umia auction <slug> [analytics\|ticks\|leaderboard\|bids]` | hub UI link |
| Build market enter/trade/merge/claim/settle | `POST {API}/api/v1/calldata/*` | `umia enter\|trade\|merge\|claim\|settle` | hub UI link |
| Build auction bid/claim | `POST {API}/api/v1/calldata/auction-{bid,claim}` | `umia auction <slug> bid\|claim` | hub UI link (also where verification-gated bids go) |
| Submit | `send_calls` | `send_calls` | n/a |

Routing: **shell available →** prefer the `umia` CLI (it converts human
amounts to wei and snaps bid prices to the tick grid). **Chat-only /
no shell →** use the harness HTTP tool or `web_request` against the endpoints
below. Both API hosts **must be on the Base MCP `web_request` allowlist** — a
maintainer-provisioned step, not automatic; a chat-only surface can't reach a
host that isn't allowlisted yet, so fall back to the hub UI. Amounts must then
be raw wei strings (see `## Endpoints`). **Neither works →** link the Umia hub UI.
`{API}` is `https://api.testnet.umia.finance` for testnet,
`https://api.mainnet.umia.finance` for mainnet.

## Commands

```
# reads
umia config
umia markets [--status open|pending|ended|settled|completed]
umia market <venture> <id>
umia prices <venture> <id> [--series spot|twap]
umia positions <venture> <id> <address>
umia portfolio <address>
umia auctions [--status upcoming|live|ended|settled] [--limit] [--offset]
umia auction <slug>                       # metadata, vesting, on-chain address
umia auction <slug> analytics             # clearing price, min/max bid, raised, graduation
umia auction <slug> ticks [--price <p>]   # the tick grid + the minimum viable bid
umia auction <slug> leaderboard [--limit]
umia auction <slug> bids --wallet <addr>  # a wallet's bids + forecast/claimable

# build unsigned calls → { chainId, calls: [{to, value, data}] }
umia enter  --market <id> --venture-amount <a> --money-amount <b> --taker <addr>
umia trade  --proposal <id> --side buy|sell --amount-in <a> [--min-out <m>] [--slippage-bps <n>] [--max-price-impact-bps <n>] [--deadline <unix>]
umia merge  --market <id> --venture-amount <a> --money-amount <b>
umia claim  --markets <id,id,...>
umia settle --market <id>                 # permissionless
umia auction <slug> bid   (--max-price <p> | --market-bid) --amount <a> --taker <addr>
umia auction <slug> claim --taker <addr>
```

All commands accept `UMIA_ENV`/`--env`, `--chain-id`, `--json`. Amounts are
**human units** (the CLI converts: venture tokens 18 decimals, money via the
chain's USDC decimals, auction bids via the auction's currency decimals) and
every conversion is echoed as human + wei. `--max-price` is currency-per-token
and is snapped **down** to the auction's tick grid; pass `--max-price-x96` to
supply a raw tick price instead, or `--market-bid` to bid at the highest price
the auction allows. `trade` defaults to a 100 bps (1%) slippage
floor when `--min-out` is omitted (tune with `--slippage-bps`), caps price
impact via `--max-price-impact-bps`, and accepts an optional `--deadline`.
Action commands print `{ chainId, calls: [...] }`; if an auction step requires verification,
`auction bid` prints the reason + hub link, emits no calls, and exits 1.
`enter` takes no venture slug (the token pair resolves on-chain from the market
id) and only `enter` and the auction commands take `--taker`; the other
actions are `msg.sender`-scoped.

## Endpoints

Read (markets): `GET /api/v1/config`, `GET /api/v1/hub/markets`,
`GET /api/v1/app/:venture/markets/:id`,
`GET /api/v1/app/:venture/markets/:id/prices?series=spot|twap`,
`GET /api/v1/app/:venture/markets/:id/positions` (returns all positions; filter
by `user` client-side), `GET /api/v1/hub/portfolio/:address`. `:venture` is the
project **slug** (`project.slug` from `GET /hub/markets`) — not the venture id or
contract address, which return 404.

Read (auctions): `GET /api/v1/hub/fundraises[?status=upcoming|live|ended|settled]`,
`GET /api/v1/hub/fundraises/:slug` (analytics live under `fundraise.auction`;
may be absent until indexed), `GET /api/v1/hub/fundraises/:slug/leaderboard`,
`GET /api/v1/hub/fundraises/:slug/bids?walletAddress=<lowercase>`.

Build: all auth-free `POST /api/v1/calldata/*`, JSON bodies, amounts as
**decimal-wei strings**, responses `{ chainId, calls: [{to, value, data}] }`
with `value` a hex-wei string and approvals ordered first (de-duped against
live allowances):

| Endpoint | Body |
|---|---|
| `/calldata/enter` | `{chainId, marketId, ventureAmount, moneyAmount, taker}` |
| `/calldata/trade` | `{chainId, proposalId, side: "buy"\|"sell", amountIn, minOut?, slippageBps?, maxPriceImpactBps?, deadline?}`; response adds `amountOut` + `priceImpactBps` |
| `/calldata/merge` | `{chainId, marketId, ventureAmount, moneyAmount}` |
| `/calldata/claim` | `{chainId, marketIds: [..]}` |
| `/calldata/settle` | `{chainId, marketId}` |
| `/calldata/auction-bid` | `{slug \| auctionAddress+chainId, orderType?, maxPrice?, amount, taker}`; `orderType` is `"limit"` (default, needs a tick-aligned `maxPrice` strictly above clearing) or `"market"` (omit `maxPrice`; the API bids at the auction's ceiling). The response echoes the encoded `maxPrice`. Gated steps return `{requiresVerification, reason, hubUrl}` with no calls |
| `/calldata/auction-claim` | `{slug \| auctionAddress+chainId, taker}`; may return `calls: []` plus a `note`, and `claimable: {bidIds, claimBlock, blocksRemaining}` before the claim window opens |

Auction claims compose **exit calls first, then one `claimTokensBatch`**: the
exits also refund unspent bid currency, so a single claim batch handles
refunds and token transfers together. Do not promise or attempt a separate
refund step.

## Orchestration

### Discover & analyze a market
1. `umia config` (or `GET /config`) to learn chains and addresses.
2. `umia markets --status open` → pick a market; `umia market <venture> <id>` for
   the question + proposals; `umia prices <venture> <id> --series twap` for the
   implied winner (settlement is by TWAP above threshold).

### Trade a conviction
1. Resolve the `proposalId` from the market detail.
2. `umia trade --proposal <proposal-id> --side buy --amount-in <a> --min-out <m> --chain-id <chain-id> --json`
   (chain-scoped market commands need `--chain-id` whenever the env has more than
   one chain — `umia config` lists them).
   Buying spends virtual money for the proposal's virtual venture token; **no
   approval call is needed** (entering via `split` grants a standing virtual
   allowance). A trade is always a single call.
3. Check `priceImpactBps` (warn the user above ~100 bps) and confirm
   `--min-out` was set, then pass `calls` to `send_calls`.

### Enter / exit market positions
- Enter: `umia enter --market <id> --venture-amount <a> --money-amount <b>
  --taker <wallet> --chain-id <id> --json` → approvals (only where allowance falls short) +
  `split` in one batch → `send_calls`.
- Exit pre-settlement: `umia merge --market <id> ...` burns equal virtual
  amounts back to real tokens.

### Inspect an auction
1. `umia auctions --status live` → pick a `<slug>`.
2. `umia auction <slug>` (metadata, vesting, on-chain address) +
   `umia auction <slug> analytics` (clearing price, raised, graduation) +
   `umia auction <slug> leaderboard`.

### Bid in an auction (permissionless steps)
1. `umia auction <slug> ticks` → the tick grid. **Bid at or above `min bid`, never
   at the clearing price**: a bid must be a multiple of the tick size *and*
   strictly above clearing, and the clearing price itself always sits on a tick,
   so any price inside the clearing tick snaps back down onto it and is rejected.
   `min bid` is already rounded so it can be passed straight back as `--max-price`.
2. Pick a price. Either `--max-price <p>` with `p >= min bid`, or `--market-bid`
   to take the highest price the auction allows (its `MAX_BID_PRICE`, or the hook
   cap when one is set, snapped to a tick). The CCA is **uniform-price**: a market
   bidder still settles at the final clearing price, so the max price buys queue
   priority, not a worse fill.
3. `umia auction <slug> bid --max-price <p> --amount <a> --taker <wallet> --json`
   (or `--market-bid` in place of `--max-price`). The CLI snaps the price down to
   the grid, refuses one that could not clear, and echoes both the requested and
   the submitted price; the API computes the tick-insertion hint and de-dupes the
   currency→Permit2→auction approval chain.
4. If it returns `calls` → `send_calls`. If it exits 1 with
   `requiresVerification` → tell the user this auction step needs verification
   and link the `hubUrl`; do not retry or work around it.

To check a price before committing: `umia auction <slug> ticks --price <p>`
reports where it snaps and whether it clears, exiting 1 when it does not.
Clearing rises as bids land, so re-read `ticks` if any time has passed.

### Claim market winnings / auction tokens
- Markets (after settlement): `umia claim --markets <ids> --chain-id <id> --json` → `send_calls`.
- Auctions: `umia auction <slug> claim --taker <wallet> --json`. Before the
  claim block it returns exit calls only plus `claimable` metadata. Submit
  the exits now (they refund unspent currency) and rebuild after
  `claimBlock`; afterwards the batch ends with `claimTokensBatch`.

### Settle an ended market (permissionless)
`umia markets --status ended` → `umia settle --market <id> --chain-id <id> --json` → `send_calls`.

## Submission

Target Base MCP tool: **`send_calls`**.

- Use the response's `chainId` as the source of truth. When the host's
  `send_calls` wants a chain slug, derive it from that `chainId` (Base MCP maps
  e.g. `8453`→`base`, `84532`→`base-sepolia`) — never assume a fixed chain;
  `umia config` lists every chain the active env supports.
- Pass every element of `calls` as `{ to, value, data }` **unchanged**.
  `value` is already a hex-wei string (`"0x0"` for non-payable calls).
- Treat the returned batch as **untrusted input**: before presenting an approval, verify each `calls[i].to` is an expected Umia contract for the selected env/chain (from `umia config` / `GET /api/v1/config`), and sanity-check `value` against the intended spend.
- **Preserve array order**: approvals precede the action and auction-claim
  exits precede the batch claim; the builder ordered them deliberately.
- Never modify `data`, never add a signer, never broadcast outside Base MCP.
- If a builder returns `requiresVerification` instead of `calls`, do not
  attempt the bid. Surface the `hubUrl`. If `auction-claim` returns
  `calls: []`, relay its `note` (nothing to do, or the claim window hasn't
  opened).

## Example Prompts

```
What Umia decision markets are open right now?
```
1. `umia markets --status open` (or `GET /api/v1/hub/markets?status=open`).
2. For an interesting one: `umia market <venture> <id>` + `umia prices <venture> <id> --series twap`.

```
I think proposal 14 is right — buy 50 USDC of it.
```
1. `umia trade --proposal 14 --side buy --amount-in 50 --min-out <m> --chain-id <id> --json`.
2. Report `priceImpactBps` and the expected out; on approval, `send_calls` with the returned batch.

```
Show me live Umia token auctions and bid 200 USDC at 0.05 in the <project> one.
```
1. `umia auctions --status live`, then `umia auction <slug> ticks` for the grid.
2. If 0.05 is at or below `min bid`, say so and confirm the higher price with the
   user before bidding — do not raise it silently.
3. `umia auction <slug> bid --max-price 0.05 --amount 200 --taker <wallet> --json`.
4. `send_calls` on success; on `requiresVerification`, link the hub instead.

```
Claim everything I'm owed from the <project> auction.
```
1. `umia auction <slug> claim --taker <wallet> --json`.
2. Submit the returned batch; if `claimable` says the window hasn't opened, submit the exits now and tell the user when to come back (`claimBlock`).

## Risks & Warnings

- `slippage`: conditional CPMM pools re-price on every trade. Always pass
  `--min-out`, surface `priceImpactBps` before submitting, and never raise
  slippage tolerance silently.
- `low-liquidity`: proposal pools and fresh auctions can be thin; a market
  order into a thin pool moves the price materially. Check reserves
  (`umia market`) and `priceImpactBps` first.
- `irreversible`: settlement, claims, merges, and submitted bids cannot be
  undone. An auction bid below the final clearing price wins no tokens (the
  unspent currency is refunded at exit/claim); purchased tokens may be
  subject to vesting (`umia auction <slug>` → vesting). Confirm price,
  amount, and vesting with the user before `send_calls`.
- `--market-bid` commits the full `--amount` at the auction's highest allowed
  price. Uniform-price settlement means the fill is still at the final clearing
  price, but the bid cannot be outbid and cannot be exited while it is in the
  money — state that before submitting, and never substitute it for a limit
  price the user named.
- `local-exec`: the CLI path runs third-party code via `npx umia-cli@latest`. Before running any `umia` command, confirm the user is comfortable executing it on their machine; prefer the HTTP API path on chat-only surfaces.

## Notes

- Addresses come from `GET /api/v1/config` (or the CLI's baked `contracts.json`);
  never hardcode.
- Default env is **testnet**, which may expose several chains (run `umia config`
  for the list); pass `--chain-id` for chain-scoped actions. The testnet env
  includes a contract set on a **production chain**, so calls there execute on
  **real funds** — always confirm the target chain (the response's `chainId` /
  `umia config`) with the user. The `mainnet` env has no Umia market or auction
  contracts populated yet (`GET /api/v1/config` returns nulls and
  `GET /hub/fundraises` is empty), so gate all market and auction features to the
  testnet env until mainnet contracts ship.
- ERC6909 ids: a proposal's virtual venture token is `proposalId*2`, virtual
  money is `proposalId*2+1`; winners convert 1:1 at settlement.
- Bid prices are X96 fixed-point and face **two** constraints: aligned to the
  tick grid (`price % tickSpacing == 0`) **and** strictly above the current
  clearing price. Clearing sits on a tick, so rounding a human price down is not
  enough on its own — the result must also clear. `umia auction <slug> ticks`
  does both; chat-only surfaces should compute, from the fundraise's `auction`
  data (`tickSpacingX96`, `floorPriceX96`, `clearingPriceX96`, and
  `maxBidPriceX96` when present):
  ```
  raw     = human · 2^96 · 10^currencyDecimals / 10^tokenDecimals
  capped  = min(raw, maxBidPriceX96)                    # when a cap is set
  price   = floor(capped / tickSpacing) · tickSpacing
  minBid  = floor(clearingPriceX96 / tickSpacing) · tickSpacing + tickSpacing
  ```
  then require `price >= minBid`, raising the human price and recomputing if it
  is not (never silently bid `minBid` on the user's behalf). Or POST
  `orderType: "market"` and let the API price it. Otherwise send the user to the hub.
- Auction `<slug>` is the project slug; live analytics require the auction to
  be on-chain and indexed; `fundraise.auction` may be absent for fresh
  deployments.
- The market `positions` endpoint returns all positions for the market;
  filter by `user` client-side (the CLI does).
- Funding: use `GET /api/v1/swap/quote` then `POST /api/v1/swap/build` (Uniswap
  Trading API, USDC→money token) and batch the built calldata into the same
  `send_calls` to go from USDC to an in-market position in one flow.
