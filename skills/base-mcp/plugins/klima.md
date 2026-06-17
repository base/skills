---
title: "Klima Plugin"
description: "Retire tokenized carbon credits on Base via the Klima HTTP API → send_calls, with Carbonmark certificate resolution."
tags: [carbon-credits, carbon-retirement, climate, discovery]
name: klima
version: 0.2.0
integration: http-api
chains: [base]
requires:
  shell: none
  allowlist: [x402.klimalabs.com]
  externalMcp: null
  cliPackage: null
auth: none
risk: [irreversible]
---

# Klima Plugin

> [!IMPORTANT]
> Complete the Base MCP onboarding flow defined in `SKILL.md` before calling any Klima endpoint. The user's wallet address — used as `retiringAddress` / `beneficiaryAddress` in the retirement `details` and as the account that signs `send_calls` — comes from `get_wallets`. Do not fabricate it.

## Overview

Klima retires tokenized carbon credits through the Klima Protocol Retirement Aggregator on Base. The plugin reads the credit catalog and live prices over the Klima HTTP API, fetches **unsigned calldata** for an ordered `[approve, retire]` batch, and executes it atomically via `send_calls`. Every API call is free — a small protocol fee is collected onchain by the Settlement Contract inside the retirement transaction itself (see [Notes](#notes)). After the transaction confirms, the API resolves the public Carbonmark certificate URL for the retirement.

**Supported chain:** Base mainnet (`8453`) only. Any other `chainId` is rejected with a 400 — Base Sepolia (`84532`) returns `unsupported_chain_id`, any other number returns `schema_validation`.

## Surface Routing

Klima is HTTP-only; every capability follows the standard HTTP routing in [../references/custom-plugins.md](../references/custom-plugins.md). Every endpoint is a **GET** with all parameters in the query string, so the GET-only user-paste fallback works on chat-only surfaces.

| Capability | Path |
| --- | --- |
| Read catalog / prices / certificates (`discover`, `quote`, `certificate`) | Harness HTTP tool if available, else `web_request` GET against `x402.klimalabs.com`. |
| Prepare a retirement (`prepare/retire`) | Harness HTTP tool or `web_request` GET → calldata → `send_calls`. |
| Chat-only surface where the host is not reachable | Construct the full GET URL, ask the user to paste it into the chat, then parse the response and continue. |

## Endpoints

Base URL: `https://x402.klimalabs.com/api`. All endpoints are GET and free; reads never move funds.

### `GET /discover`

```
GET /discover[?carbonClass=0x...][&creditToken=0x...][&maxUsdcPricePerTonne=20]
```

Lists carbon classes from the protocol subgraph — each with a live USDC/tonne reference price — plus the supported input tokens and contract addresses. The three optional filters are AND-combined: `carbonClass` keeps one class, `creditToken` keeps the class holding that credit (and trims it to that credit), and `maxUsdcPricePerTonne` keeps classes priced at or below that figure (human units: `20` = $20/tonne). These are the **only** accepted parameters — anything else (including `chainId`) returns a 400.

Use the response to size a retirement: each class lists `creditsDetailed[]` (registry, vintage, `tokenId`, and `liquidityFormatted` — the maximum retirable tonnes for that credit) plus `minRetirementTonnesFormatted`. Puro `batchId` and token standard are resolved server-side — callers never supply them.

### `GET /quote`

```
GET /quote?chainId=8453&inputToken=0x...&carbonClass=0x...&amount=1.5[&creditToken=0x...][&vintage=2022][&tokenId=<id>]
```

Live price quote for retiring `amount` tonnes. Returns the retirement price, the onchain settlement `fee`, `total` (price + fee), `suggestedMaxInput` (total + slippage), a `humanSummary`, plus `resolvedCredit` (the `creditToken` / `tokenId` / `vintage` the server selected) and `alternatives`.

Required: `chainId` (always `8453`), `inputToken` and `carbonClass` (addresses), `amount` (a decimal tonne string, `"1.5"`). The rest narrow **credit resolution** — when omitted, the server picks the most-liquid credit in the class that can cover `amount`:

- `creditToken` — only consider credits at that address.
- `vintage` — only that year; an unavailable year returns `400 vintage_not_found` listing `availableVintages`.
- `creditToken` + `tokenId` together — pin one exact credit (the ERC-1155 case); `vintage` is then ignored.

Amount rules: see [Notes](#notes).

### `GET /prepare/retire`

```
GET /prepare/retire?chainId=8453&inputToken=0x...&carbonClass=0x...&amount=1.5[&creditToken=0x...][&vintage=2022][&tokenId=<id>][&maxInputTokenIn=<atomic>][&details=<urlencoded JSON>]
```

Quotes onchain, then returns unsigned calldata as an **ordered batch**: an ERC-20 `approve` followed by the retirement. Credit resolution and amount rules are identical to `/quote` (prepare re-quotes server-side; the `quote` object in its response is the authoritative price). One retirement per call.

`maxInputTokenIn` (atomic units) overrides the default slippage ceiling of `(price + fee) × 1.04`. It is the total budget the Settlement Contract may spend; the fee and retirement cost come out of it and the remainder is refunded in the same transaction.

`details` is an optional URL-encoded JSON object. The schema is **strict**: exactly the keys below are accepted, and an unknown key returns a 400 naming it — do not invent fields.

| `details` field | Meaning |
| --- | --- |
| `retiringAddress` | address performing the retirement — the wallet from `get_wallets` |
| `beneficiaryAddress` | address credited on the certificate — usually the same wallet |
| `beneficiaryString` | beneficiary display name |
| `retiringEntityString` | retiring-entity display name |
| `retirementMessage` | public message shown on the certificate |
| `beneficiaryLocation` | Puro only — beneficiary location string |
| `consumptionCountryCode` | Puro only — ISO country code |
| `consumptionPeriodStart` / `consumptionPeriodEnd` | Puro only — unix timestamps (seconds) |

Every field is optional for standard credits (omitted fields default to empty / zero-address); use the user's wallet address (from `get_wallets`) for `retiringAddress` / `beneficiaryAddress` unless they specify otherwise. For **Toucan Puro** credits the four Puro fields are required — prepare returns `400 puro_details_required` with a `missing` array; collect those fields and re-prepare.

**Certificate attribution is required — collect it before preparing.** `beneficiaryString`, `retiringEntityString`, and `retirementMessage` are what appear on the public Carbonmark certificate, which **cannot be edited after the retirement confirms**. A `beneficiaryString` (beneficiary name) is **mandatory**: do not call prepare until the user supplies one, and never substitute the wallet address or a placeholder. This is non-negotiable — if the user tries to skip it, explain that the certificate must be attributed and ask again. `retirementMessage` (public message) and `retiringEntityString` (retiring entity, when it differs from the beneficiary) are optional, but **actively offer them with explicit prompts** rather than skipping silently. Like the beneficiary name they are permanently set on the certificate:

- `retirementMessage`: "Would you like to add a public message to your certificate?"
- `retiringEntityString`: "Should a retiring entity name appear on the certificate (if different from the beneficiary)?"

Accept "skip" / "no" for either. Fold whatever the user supplies into `details`.

Response:

```json
{
  "to": "0x<settlementContract>",
  "data": "0x...",
  "chainId": 8453,
  "chain": "base",
  "transactions": [
    { "step": "approve",       "to": "0x<inputToken>",          "value": "0x0", "data": "0x...", "chainId": 8453 },
    { "step": "prepareRetire", "to": "0x<settlementContract>",  "value": "0x0", "data": "0x...", "chainId": 8453 }
  ],
  "quote": { "humanSummary": "...", "tonnesFormatted": "1.5", "fee": "...", "total": "..." },
  "approvalRequired": true,
  "approvalInstructions": { "token": "0x...", "spender": "0x<settlementContract>", "amount": "...", "amountFormatted": "...", "note": "..." }
}
```

The `approve` step targets the input token; the `prepareRetire` step targets the Settlement Contract. Both USDC and kVCM approve the same spender, so there is always exactly one approval.

### `GET /certificate`

```
GET /certificate?txHash=0x...[&index=0]
```

After the retirement transaction confirms, resolves the public **Carbonmark certificate URL(s)**. `txHash` is the confirmed transaction hash (from `get_request_status`). `index` optionally selects one retirement out of a multi-retirement transaction; omit it to get all. These are the only accepted parameters (no `chainId`).

Returns `transactionHash`, `retirementCount`, and `retirements[]` — each with `certificateUrl` (the shareable page on `app.carbonmark.com`), `retirementId`, `retirementIndex`, `amountInTonnes`, `beneficiaryName`, `beneficiaryLocation`, `message`, `projectId`, `creditId`, `retiringAddress`, and `timestamp` (unix seconds).

A `404 retirement_not_found` right after confirmation means the subgraph hasn't indexed the transaction yet — wait a few seconds and retry. A 404 whose message names a valid index range means the `index` is wrong; don't retry.

## Orchestration

```
1. get_wallets → address                              (onboarding)
2. GET /discover → pick carbonClass (creditToken optional)
   - creditsDetailed[].liquidityFormatted = max retirable tonnes; Puro = whole tonnes only
3. Confirm the input token → if the user has NOT specified one, ASK: "Would you like to pay with USDC or kVCM?"
   - do not silently default to USDC; the user may not hold it, and switching only after a failed transaction is a poor experience
   - check the user's balance of the chosen token against quote.total before preparing where possible
4. GET /quote?chainId=8453&... → price it              (optional)
5. Collect certificate attribution → beneficiaryString is REQUIRED (do not proceed without it); retirementMessage / retiringEntityString optional
   - certificate is uneditable after confirmation; never substitute the wallet address for the name
   - actively offer the optional fields with explicit prompts (see Endpoints → /prepare/retire); don't silently skip them
6. GET /prepare/retire?chainId=8453&...&details=<urlencoded {"retiringAddress": address, "beneficiaryAddress": address, "beneficiaryString": ..., "retirementMessage": ...}>
   - 400 puro_details_required → collect the `missing` fields and re-prepare
7. Show quote.humanSummary to the user and confirm
8. send_calls(chain = response.chain, calls from transactions[])
9. User approves → get_request_status(requestId) until confirmed
10. GET /certificate?txHash=<confirmed hash> → share certificateUrl
   - 404 right after confirmation = not indexed yet; retry after a few seconds
```

## Submission

Target tool: **`send_calls`**.

Pass every `transactions[*]` through in order, using the top-level `chain` name (`base`):

```json
{
  "chain": "base",
  "calls": [
    { "to": "<transactions[0].to>", "value": "<transactions[0].value>", "data": "<transactions[0].data>" },
    { "to": "<transactions[1].to>", "value": "<transactions[1].value>", "data": "<transactions[1].data>" }
  ]
}
```

Drop the `step` and `chainId` fields — `send_calls` only needs `to` / `value` / `data`, and the chain is set once at the top level. `value` is `0x0` for every Klima call. Submit the full batch in one `send_calls` so the user approves once and approve + retire execute atomically. Then walk the approval flow (see [../references/approval-mode.md](../references/approval-mode.md)) and poll `get_request_status`.

## Example Prompts

### Retire 1 tonne of carbon

```
1. get_wallets → address
2. GET /discover → present classes with priceUsdcPerTonneFormatted; user picks one
3. Confirm input token (ask USDC or kVCM if unspecified) → collect beneficiaryString (required); offer retirementMessage / retiringEntityString
4. GET /prepare/retire?chainId=8453&inputToken=<USDC|kVCM>&carbonClass=<class>&amount=1&details=<urlencoded {"retiringAddress": address, "beneficiaryAddress": address, "beneficiaryString": ...}>
5. Show quote.humanSummary → user confirms
6. send_calls(chain="base", calls from transactions[]) → user approves → get_request_status
7. GET /certificate?txHash=<hash> → share certificateUrl
```

### Offset under a price cap ("retire 2 tonnes at no more than $15/tonne")

```
1. get_wallets → address
2. GET /discover?maxUsdcPricePerTonne=15 → only qualifying classes remain
3. Continue with /prepare/retire as above with amount=2
```

### Retire a Puro credit

```
1–3. As above; /prepare/retire returns 400 puro_details_required with missing: [...]
4. Ask the user for beneficiaryLocation, consumptionCountryCode, and the consumption period
5. Re-prepare with the completed details object (whole-tonne amounts only — see Notes)
6. send_calls → approval → certificate
```

### Look up a past certificate

```
1. GET /certificate?txHash=<hash from the user or get_request_status>
2. Share retirements[].certificateUrl
```

## Risks & Warnings

- **Irreversible.** A retirement permanently burns the carbon credit — there is no undo, refund, or resale once `send_calls` confirms. Always show `quote.humanSummary` (tonnes, price, fee, total) and get the user's explicit confirmation before submitting. Never auto-retry a `422 contract_revert` with modified parameters; surface `decoded.retryAdvice` to the user instead.

## Notes

**Key contracts (Base mainnet):**

| Contract | Address |
| --- | --- |
| Retirement Aggregator | `0xda0a793d7c32ab80bcdab7f8c725c96db22464f4` |
| Settlement Contract (retire target + token spender) | read from the prepare response (`to` / `approvalInstructions.spender`) — do not hard-code |
| Klima Protocol AAM | `0x1C24239309398220883207681602BfF4D10fbde1` |
| kVCM | `0x00fbac94fec8d4089d3fe979f39454f48c71a65d` |
| USDC | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |

**Input tokens:** USDC or kVCM only (addresses above).

**Fees:** API calls are free. Each retirement bakes in a protocol fee, computed and collected onchain by the Settlement Contract: `fee = max(floor, feeBps% of retirement cost)`, with the floor denominated in USDC (converted via the kVCM/USDC pool when paying in kVCM). The live fee is always included in `quote.fee` / `feeFormatted` and folded into `total` and `suggestedMaxInput` — never estimate it yourself. Onchain, the contract emits `RetirementSettled(payer, beneficiary, value, fee, retirementCost, refunded)`; the payer spends exactly `retirementCost + fee` and any approved budget beyond that is refunded in the same transaction.

**Amount rules:** `amount` is a decimal tonne string; minimum 0.001 tonnes (1 kg). **Puro credits retire in whole tonnes only** — fractional amounts return `422 amount_not_whole_tonnes` with the nearest valid amounts. Amounts above a credit's liquidity return `422 insufficient_liquidity`.

**Error reference:** failures return JSON with an `error` code plus actionable fields.

| Status + `error` | What to do |
| --- | --- |
| 400 `schema_validation` | A parameter is malformed or unknown — `issues[]` names it. Fix and retry. |
| 400 `unsupported_chain_id` | Use `chainId=8453` (Base mainnet only). |
| 400 `unsupported_input_token` | Use USDC or kVCM. |
| 400 `vintage_not_found` | Pick from `availableVintages`, or omit `vintage`. |
| 400 `puro_details_required` | Supply the `details` fields listed in `missing`, then re-prepare. |
| 404 `no_candidates` | Nothing retirable for that class/credit — re-check `/discover`. |
| 404 `retirement_not_found` | Certificate only — not indexed yet (retry shortly) or bad `index`. |
| 422 `amount_not_whole_tonnes` | Puro: request a whole number of tonnes (`nearestDownTonnes` / `nearestUpTonnes` are provided). |
| 422 `insufficient_liquidity` | Reduce `amount` (`bestAvailableAtomic` = the most any credit can cover, in 1e18 tonnes) or pick another class/credit. |
| 422 `amount_below_increment` | Amount converts to zero retirable units — increase it. |
| 422 `contract_revert` | Decoded onchain revert — follow `decoded.retryAdvice`. Don't blind-retry. |
