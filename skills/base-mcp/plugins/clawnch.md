---
title: "Clawnch Plugin"
description: "Skill plugin reference for discovering token launches on Base via the Clawnch API (recent + top-by-volume) and buying them with Base MCP's swap tool."
---

# Clawnch Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before
> calling any Clawnch flow. This plugin reads from the Clawnch public API and
> then routes the actual purchase through Base MCP's `swap` tool — there is no
> separate Clawnch MCP server.

[Clawnch](https://www.clawn.ch) is a launch and discovery surface for tokens on
Base. The public API exposes two complementary feeds:

  * **Recent launches** — every token deployed through the Clawnch launchpad
    (and other Clawnch-tracked sources: moltbook, 4claw, clawtomaton, clawmes),
    newest first. Roughly 140k tokens indexed at time of writing.
  * **Top by volume** — the same token set sorted by 24h trading volume, with
    live price / market cap / volume / 24h price change attached. This is the
    "what's hot right now" surface, distinct from "what just launched."

This plugin uses both feeds to surface tokens to the user, then buys the
selected token through Base MCP's `swap` tool — Clawnch is only the discovery
layer; the swap is a regular Base MCP `swap` call paying ETH (or USDC) for the
target ERC-20.

No additional MCP server is required.

**Prerequisite:** `www.clawn.ch` must be on the Base MCP `web_request`
allowlist. If requests are rejected, inform the user and fall back to the
harness's HTTP/fetch tool if one is available.

**Chain:** Base mainnet (chainId `8453` / `0x2105`).

---

## API

Base URL: `https://www.clawn.ch`

Use the `www.` host directly — `clawn.ch` returns a 307 redirect, which some
`web_request` implementations don't follow.

### `GET /api/launches`

Returns recent token launches on Base, newest first. No auth required.

Query parameters (all optional):

| Param     | Default | Notes                                                                |
| --------- | ------- | -------------------------------------------------------------------- |
| `limit`   | `50`    | Max `100`. Number of launches to return.                             |
| `offset`  | `0`     | For pagination through the full 140k+ index.                         |
| `agent`   | —       | Filter by `agentName` (string match).                                |
| `source`  | —       | Filter by deploy source: `moltbook`, `4claw`, `clawtomaton`, `clawmes`, `moltx`. |
| `address` | —       | Return a single launch by contract address. See dedicated endpoint below. |

```json
{
  "success": true,
  "launches": [
    {
      "contractAddress": "0xAD740994F3Ddc522DE7cd005891245b72634EdF0",
      "symbol": "CPMH",
      "name": "Complete Mayhem",
      "description": "",
      "agentName": "4claw_anon_thread:2",
      "source": "4claw",
      "postId": "thread:2ca1d363-5e23-429c-8e4b-14ffd7c0fa7e",
      "launchedAt": "2026-05-26T19:26:45.000Z",
      "createdAt": "2026-05-26T19:26:45.000Z",
      "clankerUrl": "https://clanker.world/clanker/0xAD740994F3Ddc522DE7cd005891245b72634EdF0",
      "chainId": 8453
    }
  ],
  "pagination": { "limit": 50, "offset": 0, "total": 140830, "hasMore": true }
}
```

Field notes:

  * `contractAddress` — the ERC-20 contract on Base. Pass verbatim to `swap` as
    `toAsset`. Addresses are returned in checksum case.
  * `symbol` / `name` — user-supplied; can collide across launches.
  * `agentName` / `source` — *who* deployed this. `source` is the platform
    integration that originated the deploy (`clawmes` = the Hermes Agent
    plugin, `moltbook` = Moltbook social, `4claw` = the 4claw bot, etc.).
    Useful for the user to filter "show me launches from X."
  * `launchedAt` — ISO timestamp; the array is sorted newest-first by this
    field.
  * `clankerUrl` — every Clawnch launch goes through the Clanker contract
    factory, so each token has a canonical Clanker page.
  * `chainId` — always `8453` (Base mainnet).

The default `limit=50` is generally too verbose for a chat surface — use
`limit=10` for "what's new" prompts and `limit=25` for deeper scrolls.

### `GET /api/launches?address=<contractAddress>`

Single-launch lookup by contract address. The address is case-insensitive.
Returns `{success: false, error: "Launch not found"}` with **HTTP 404** when
the address isn't in the index. `web_request` implementations that treat
non-2xx as a hard error may not surface that body — treat a 404 from this
endpoint as "not in the Clawnch index", not as an outage.

```text Example
GET https://www.clawn.ch/api/launches?address=0xa1F72459dfA10BAD200Ac160eCd78C6b77a747be
```

```json
{
  "success": true,
  "launch": {
    "contractAddress": "0xa1F72459dfA10BAD200Ac160eCd78C6b77a747be",
    "symbol": "CLAWNCH",
    "name": "CLAWNCH",
    "description": "Agent-only token launches for Moltbook. Deploy via Clanker, earn trading fees. Built for agents, by agents.",
    "agentName": "CLAWNCH",
    "launchedAt": "2026-01-31T03:13:57.572Z",
    "clankerUrl": "https://clanker.world/clanker/0xa1F72459dfA10BAD200Ac160eCd78C6b77a747be",
    "chainId": 8453
  }
}
```

Use this when the user names a token by **address** rather than picking from a
list, or to enrich an address pasted from elsewhere with launch metadata.

### `GET /api/tokens`

Token directory with live price + market data, sorted by 24h trading volume by
default. No auth required.

Query parameters:

| Param    | Default     | Notes                                                            |
| -------- | ----------- | ---------------------------------------------------------------- |
| `limit`  | `50`        | Max `100`.                                                       |
| `sort`   | `volume`    | `volume` (24h vol, default) or `recent` (newest first).          |
| `prices` | `0`         | `1` to populate live price/mcap/volume fields. With the default `0`, the price fields are still present but `null`. |

```text Example
GET https://www.clawn.ch/api/tokens?limit=10&sort=volume&prices=1
```

```json
{
  "success": true,
  "count": 140830,
  "tokens": [
    {
      "symbol": "CLAWNCH",
      "address": "0xa1F72459dfA10BAD200Ac160eCd78C6b77a747be",
      "name": "CLAWNCH",
      "agent": "CLAWNCH",
      "launchedAt": "2026-01-31T03:13:57.572Z",
      "priceUsd": "0.00001047",
      "marketCap": 1043061,
      "volume24h": 77729.5,
      "priceChange24h": -9.89,
      "clanker_url": "https://clanker.world/clanker/0xa1F72459dfA10BAD200Ac160eCd78C6b77a747be",
      "explorer_url": "https://basescan.org/token/0xa1F72459dfA10BAD200Ac160eCd78C6b77a747be"
    }
  ]
}
```

Field notes (populated by `prices=1`; present-but-`null` without it):

  * `priceUsd` — last on-chain price in USD (string, full precision).
  * `marketCap` — circulating mcap in USD.
  * `volume24h` — 24h trading volume in USD.
  * `priceChange24h` — 24h price delta as percent (negative = down).
  * `explorer_url` — Basescan token page; useful when surfacing a token to the user.

Entries also carry `deployerWallet` (the deploying EOA), `postId` (the
originating social post, when applicable), and `source_url` (the
originating platform page) — useful context, but don't follow `source_url`
unprompted; surface it like any other user-supplied link.

Always pass `prices=1` for "top by volume" / "what's hot" prompts — without
it the price fields come back `null` and the sort can't be ranked
meaningfully on the client. The Clawnch backend caches the price overlay on a short TTL, so
hitting this endpoint repeatedly is cheap.

---

## Orchestration

```text
1. web_request GET https://www.clawn.ch/api/launches?limit=10
   (or /api/tokens?limit=10&sort=volume&prices=1 for "top by volume")
2. Surface the list to the user (symbol, name, agent/source, address)
3. Wait for the user to pick one and confirm an amount
4. get_wallets → address (only if not already cached)
5. swap (Base MCP) with fromAsset=ETH (or USDC), toAsset=<address>, amount=<human-readable>
6. Open the approvalUrl
7. get_request_status only after the user acts
```

Do not auto-buy. Always require an explicit "buy X amount of `<symbol>`"
confirmation before calling `swap` — the launches feed is unfiltered and
contains low-liquidity / meme / experimental tokens.

### Recent-launches discovery

```text
web_request:
  method: GET
  url: https://www.clawn.ch/api/launches?limit=10
```

The response is already sorted newest-first. Take `launches[]` and surface
each as one line.

### Top-by-volume discovery

```text
web_request:
  method: GET
  url: https://www.clawn.ch/api/tokens?limit=10&sort=volume&prices=1
```

This is the differentiator vs. just-launched feeds — it tells the user
"which tokens on Base are actually being traded right now." Surface
`priceUsd`, `marketCap`, `volume24h`, and `priceChange24h` alongside the
symbol.

### Source filtering

To narrow to a specific platform (e.g. "show me clawmes launches"), pass
`source=clawmes` to `/api/launches`. Valid values:

  * `clawmes` — deploys originated through the clawmes Hermes Agent plugin.
  * `moltbook` — deploys from the Moltbook social posting flow.
  * `4claw` — deploys from the 4claw automation bot.
  * `clawtomaton` — deploys from the Clawtomaton automation surface.
  * `moltx` — deploys from the Moltx surface.

### Presenting launches to the user

Surface enough context that the user can judge whether to buy — at minimum:
symbol, name, source/agent, age, and contract address. Don't echo the full
description or all 50 entries; that's noise.

Example summary line per launch (recent feed):

```text
CPMH — Complete Mayhem · via 4claw · launched 3m ago
  0xAD740994F3Ddc522DE7cd005891245b72634EdF0
```

Example summary line per token (volume feed):

```text
CLAWNCH — $0.0000105 · mc $1.0M · vol24h $77.7k · 24h -9.9%
  0xa1F72459dfA10BAD200Ac160eCd78C6b77a747be
```

### Swap call

The actual purchase is a regular Base MCP `swap` call. Read the `swap` tool's
own parameter descriptions from the MCP — they are the source of truth.
Typical shape:

```json
{
  "chain": "base",
  "fromAsset": "ETH",
  "toAsset": "<token.address>",
  "amount": "0.001"
}
```

  * `fromAsset`: use a supported symbol like `ETH` or `USDC`, or a contract
    address when needed.
  * `toAsset`: use the Clawnch token's `contractAddress` (or `address` from
    the tokens endpoint).
  * `amount`: human-readable decimal amount of `fromAsset`. For 0.001 ETH
    pass `"0.001"`; for 5 USDC pass `"5"`.

The `swap` tool returns an `approvalUrl` and `requestId` like any other
write call. Surface the URL neutrally ("Approve Swap"), then poll
`get_request_status` once the user has acted.

---

## Launch flow (non-custodial)

In addition to discovery + buys, Clawnch exposes a non-custodial deploy
path: a GET endpoint returns unsigned Clanker factory calldata so the
user's own wallet pays gas and ends up as `tokenAdmin`. No Clawnch API
key, no captcha, no server-side deployer. The platform's 20% trading-fee
share is preserved in the rewards array of the prepared calldata.

> [!IMPORTANT]
> **Launching requires a verified CLAWNCH burn.** Every deploy through
> this path must include a `burnTxHash` proving the `from` wallet burned
> at least **1,000,000 CLAWNCH** (`0xa1F72459dfA10BAD200Ac160eCd78C6b77a747be`)
> to `0x000000000000000000000000000000000000dEaD` on Base within the last
> 24 hours. Calling the endpoint without one returns **HTTP 402** with
> `code: "burn_required"`. The same burn also grants the vault allocation
> (1M = 1%, scaling up to 10M = 10%), so the minimum burn is never wasted.

### `GET /api/prepare/deploy`

Query parameters:

| Param          | Required | Notes                                                                    |
| -------------- | -------- | ------------------------------------------------------------------------ |
| `from`         | yes      | The user's wallet address. Becomes `tokenAdmin` + 80% reward recipient.  |
| `name`         | yes      | Token name (≤ 64 chars).                                                 |
| `symbol`       | yes      | Ticker (≤ 16 chars).                                                     |
| `description`  | no       | Optional metadata.                                                       |
| `image`        | no       | Optional image URL.                                                      |
| `twitter`      | no       | Social URL.                                                              |
| `website`      | no       | Social URL.                                                              |
| `telegram`     | no       | Social URL.                                                              |
| `farcaster`    | no       | Social URL.                                                              |
| `discord`      | no       | Social URL.                                                              |
| `burnTxHash`   | yes      | Tx hash of a 1M+ CLAWNCH burn from `from` to the dead address within 24h. Mandatory — omitting it returns HTTP 402 `burn_required`. Also sets the vault %. |

Response (envelope shape — matches Base MCP custom-plugin pattern):

```json
{
  "ok": true,
  "data": {
    "to": "0xE85A59c628F7d27878ACeB4bf3b35733630083a9",
    "data": "0xdf40224a...<encoded deployToken calldata>",
    "value": "0x0",
    "chainId": 8453
  },
  "meta": {
    "tokenName": "MyCoin",
    "symbol": "MYC",
    "platformFeeBps": 2000,
    "userFeeBps": 8000,
    "vaultPercentage": 1,
    "vaultLockupSeconds": 604800,
    "source": "base-mcp",
    "from": "0x...",
    "platformFeeRecipient": "0x..."
  }
}
```

Error shape:

```json
{ "ok": false, "error": "burnTxHash failed verification: …", "code": "invalid_burn" }
```

Missing-burn shape (HTTP 402 — the response includes a `meta` block with
the requirements, so it can be surfaced to the user verbatim):

```json
{
  "ok": false,
  "error": "This launch path now requires a verified 1,000,000 $CLAWNCH burn. Burn 1M+ CLAWNCH to 0x000000000000000000000000000000000000dEaD from this wallet within 24h, then pass the tx hash as burnTxHash.",
  "code": "burn_required",
  "meta": {
    "minBurnTokens": "1000000",
    "burnAddress": "0x000000000000000000000000000000000000dEaD"
  }
}
```

Error codes and HTTP statuses:

| Code               | HTTP | Meaning                                                       |
| ------------------ | ---- | ------------------------------------------------------------- |
| `missing_required` | 400  | `from`, `name`, or `symbol` missing.                          |
| `invalid_from`     | 400  | Malformed or zero `from` address.                             |
| `invalid_name`     | 400  | Name > 64 chars.                                              |
| `invalid_symbol`   | 400  | Symbol > 16 chars.                                            |
| `burn_required`    | 402  | No `burnTxHash` supplied. See missing-burn shape above.       |
| `invalid_burn`     | 400  | `burnTxHash` malformed or failed verification.                |
| `rate_limited`     | 429  | Per-IP or per-wallet throttle hit. Back off and retry later.  |
| `misconfigured`    | 503  | Server-side fee recipient missing. Not actionable client-side.|
| `sdk_error` / `encode_error` | 500 | Calldata build failure. Surface `error` to the user. |

Note: `web_request` implementations that treat non-2xx as a hard error may
not hand back the JSON body. If the call "fails" with a 402/4xx and no body,
assume `burn_required` for a burn-less call and explain the burn requirement
to the user.

### Launch orchestration

```text
1. get_wallets → from
2. Confirm token params with the user (name, symbol, optional metadata)
3. Burn step (mandatory): the user burns ≥1,000,000 CLAWNCH from `from`
   to 0x000000000000000000000000000000000000dEaD on Base
   (ERC-20 transfer; can be sent via send_calls). Wait for confirmation
   and capture the tx hash. Skip only if the user already has a
   qualifying burn from the last 24h.
4. web_request GET https://www.clawn.ch/api/prepare/deploy?from=<addr>&name=<...>&symbol=<...>&burnTxHash=<0xburn...>
5. Parse the envelope — bail on `ok: false`, surface `error` and `code`
   (a 402 `burn_required` means the burn step was skipped or the hash
   wasn't passed; a 400 `invalid_burn` means verification failed)
6. send_calls (Base MCP) with chain="base", calls=[{ to: data.to, value: data.value, data: data.data }]
7. Open the approvalUrl
8. Poll get_request_status until confirmed
9. Surface tx hash + the new token's eventual Basescan URL
```

The burn is a real, irreversible spend of ~1M CLAWNCH. Always state this
explicitly and get a separate confirmation for the burn transaction before
sending it — do not bundle the burn confirmation into the deploy
confirmation.

### Burn-and-vault mechanics

The mandatory burn doubles as the vault claim. Vault tokens are
creator-locked supply released after a 7-day Clanker lockup:

```text
1. User burns CLAWNCH to 0x000000000000000000000000000000000000dEaD
   on Base. Minimum 1,000,000 CLAWNCH (required to launch) = 1% vault.
   Cap 10,000,000 = 10% vault.
2. User waits for the burn tx to confirm.
3. Call /api/prepare/deploy with ?burnTxHash=<burn-tx-hash> (plus the
   usual from/name/symbol params).
4. Server verifies the burn (sender = `from`, recipient = burn address,
   amount ≥ 1M, within 24h pre-launch window) and applies the vault
   percentage to the prepared calldata.
5. Continue with the standard send_calls flow.
```

Verification rejections surface as `{ ok: false, code: "invalid_burn" }`
(HTTP 400) with a specific message ("amount below minimum", "transaction
too old", "sender mismatch", etc.).

### Launch example prompts

**Launch a token called "Cool Project" with symbol $COOL**

1. `get_wallets` → `from`.
2. Confirm with the user: name, symbol, any optional metadata.
3. Explain the launch cost: a verified burn of ≥1,000,000 CLAWNCH from their wallet is required. Check they hold enough CLAWNCH (or route them through a `swap` to acquire it first).
4. On explicit confirmation of the burn: `send_calls` with an ERC-20 `transfer(0x000000000000000000000000000000000000dEaD, amount)` on the CLAWNCH contract. Wait for confirmation; capture `<burnTx>`.
5. `web_request` GET `https://www.clawn.ch/api/prepare/deploy?from=<addr>&name=Cool%20Project&symbol=COOL&burnTxHash=<burnTx>`.
6. Bail if `ok: false`; surface `error` and `code`.
7. Show the user: "Deploy `Cool Project` (`COOL`) on Base via Clanker? 80% fee share to you, 20% to Clawnch (standard launchpad fee), 1% vault from your burn. Approve?"
8. On confirmation: `send_calls` with the returned `data`. Open `approvalUrl`. Poll `get_request_status`.

**Deploy with a 5% vault claim using my prior CLAWNCH burn**

1. Confirm the burn tx exists + is the user's, and is < 24h old. (User pastes a tx hash.)
2. `web_request` GET `https://www.clawn.ch/api/prepare/deploy?from=<addr>&name=<...>&symbol=<...>&burnTxHash=<0xburn...>`.
3. Read `meta.vaultPercentage` from the response. If less than expected, surface the discrepancy and let the user re-confirm.
4. `send_calls` with the returned `data`. The vault clause is baked into the calldata.

---

## Example Prompts

**Show me the latest token launches on Clawnch**

1. `web_request` GET `https://www.clawn.ch/api/launches?limit=10`.
2. Surface the 10 launches with symbol, name, source/agent handle, age, address.
3. Do **not** auto-buy. Ask the user which one (and how much) they want.

**What's the top token on Base by volume right now?**

1. `web_request` GET `https://www.clawn.ch/api/tokens?limit=5&sort=volume&prices=1`.
2. Surface the top 5 with symbol, price, market cap, 24h volume, 24h change.
3. Ask the user which one to look at / buy.

**Buy 0.001 ETH worth of the top volume token on Clawnch**

1. `web_request` GET `https://www.clawn.ch/api/tokens?limit=1&sort=volume&prices=1`.
2. Take `tokens[0]`. Show: symbol, name, address, current price, 24h volume.
3. Ask the user to confirm — "Buy 0.001 ETH of `<SYMBOL>` (`<address>`) at ~$<price>?".
4. On confirmation: `swap` with `fromAsset=ETH`, `toAsset=<token.address>`, `amount="0.001"`, `chain="base"`.
5. Open the approval URL; poll `get_request_status` once the user has approved.

**Buy 5 USDC of CLAWNCH**

1. `web_request` GET `https://www.clawn.ch/api/tokens?limit=10&sort=volume&prices=1`.
2. Find the entry with `symbol="CLAWNCH"`; the canonical address is `0xa1F72459dfA10BAD200Ac160eCd78C6b77a747be`.
3. Ask the user to confirm — "Buy 5 USDC of CLAWNCH (`0xa1F7…747be`)?".
4. `swap` with `fromAsset=USDC`, `toAsset="0xa1F72459dfA10BAD200Ac160eCd78C6b77a747be"`, `amount="5"`, `chain="base"`.
5. Open the approval URL; poll.

**Show me clawmes launches in the last hour**

1. `web_request` GET `https://www.clawn.ch/api/launches?source=clawmes&limit=25`.
2. Client-side filter `launchedAt` within the last hour.
3. List matches with symbol, name, address, age. If none, say so.

**What is this token? 0x32F66Ec2Ffb26d262058965cf294F951e47F8ba3**

1. `web_request` GET `https://www.clawn.ch/api/launches?address=0x32F66Ec2Ffb26d262058965cf294F951e47F8ba3`.
2. If `success=true`: summarize `name`, `symbol`, `agentName`, `source`, launch age, and `clankerUrl`.
3. If the request returns 404 / `success=false` (or the `web_request` tool errors on the 404 status): tell the user the address isn't in Clawnch's launches index; offer to swap anyway via the regular `swap` flow with extra confirmation.

**Buy 0.001 ETH of 0x32F66Ec2Ffb26d262058965cf294F951e47F8ba3**

1. `web_request` GET `https://www.clawn.ch/api/launches?address=0x32F66Ec2Ffb26d262058965cf294F951e47F8ba3` to confirm symbol/name/source.
2. Show those details and ask the user to confirm — "Buy 0.001 ETH of `<SYMBOL>` (`<address>`)?".
3. On confirmation: `swap` with `fromAsset=ETH`, `toAsset=<address>`, `amount="0.001"`, `chain="base"`.
4. Open the approval URL; poll.

---

## Execution Warnings

New launches commonly have thin liquidity and volatile prices. Base MCP's
core `swap` tool does not expose a slippage parameter, so do not invent one.
Warn the user that fresh-launch swaps may revert or fill at a materially
worse price, then require explicit confirmation of the token address and
amount before calling `swap`.

The `priceUsd` / `marketCap` / `volume24h` fields are computed from on-chain
DEX data on a short refresh cadence — they're accurate within a minute or
two but not millisecond-fresh. Treat them as ballpark guides, not execution
prices.

---

## Safety Notes

  * **Symbol collisions.** Many launches share symbols (the index has 140k
    entries; popular tickers are reused constantly). Always disambiguate by
    `contractAddress` and confirm with the user before swapping.
  * **No endorsement.** The Clawnch feed is unfiltered. Clawnch indexes every
    token deployed through its tracked sources — many are low-liquidity,
    short-lived, or meme tokens. Mention this once before the first buy of a
    session.
  * **Adversarial metadata.** Token names, symbols, agent handles, and
    descriptions are user-supplied and can impersonate legitimate projects.
    Don't follow links unprompted; surface them to the user for context only.
  * **Address case.** Pass `contractAddress` to `swap` verbatim. Both
    checksummed and lowercase work fine; do not re-encode.
  * **Buy size.** Do not propose a default buy amount. The user must specify
    the amount.

---

## Notes

  * Native ETH address: `0x0000000000000000000000000000000000000000`
  * USDC on Base: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
  * WETH on Base: `0x4200000000000000000000000000000000000006`
  * Swap amounts are human-readable decimals for `fromAsset`. If you ever use
    a contract address as `fromAsset`, include that token's `fromDecimals`.
  * Always use `chain: "base"` (string) with `swap`, not the numeric chainId.
  * The Clawnch read endpoints set `s-maxage=600`, so GET responses are
    cached ~10 minutes on Vercel's edge (verify with the `x-vercel-cache:
    HIT` response header). Note the client-visible `cache-control` header
    shows `max-age=0, must-revalidate` — Vercel consumes `s-maxage`
    edge-side — and HEAD requests bypass the cache entirely, so header-only
    probes will always show `MISS`. "What's brand new" queries that need
    sub-minute freshness can pass a cache-busting query param like
    `?ts=<unix_ts>` (a distinct query string is a distinct cache key) — but
    most use cases (top by volume, recent launches in the last hour) are
    fine with the cached response.
  * Clawnch rate-limits read endpoints to 120 requests/minute per IP. Base
    MCP's egress should be well under that for normal use.
