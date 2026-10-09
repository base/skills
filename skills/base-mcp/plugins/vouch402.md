---
title: "Vouch402 Plugin"
description: "x402-metered on-chain risk scores for Base addresses, with EAS fulfillment attestations: pay via send_calls, read the result over HTTP."
tags: [risk-scoring, attestations, agent-commerce, ai-agents]
name: vouch402
version: 0.2.0
integration: http-api
chains: [base]
requires:
  shell: none
  allowlist: [vouch402.fly.dev]
  externalMcp: null
  cliPackage: null
auth: none
risk: [irreversible]
---

# Vouch402 Plugin

> [!IMPORTANT]
> Run Base MCP onboarding first (see SKILL.md). No session/auth setup beyond onboarding: each request is paid individually via x402.

## Overview

Vouch402 is an x402-paid HTTP API that scores the on-chain risk of a Base
address (wallet age, transaction count, unique contract-interaction
diversity, and membership on a bundled flag list) and, on every successful
paid response, emits an EAS attestation recording what was delivered. It
returns **unsigned payment requirements first** (HTTP 402), then, once
paid, **JSON data**: it does not return calldata for the caller to submit
on its own behalf; the only Base MCP call in the flow is the USDC payment
itself.

## Surface Routing

| Capability | Claude Code / Codex / Cursor | Claude.ai / ChatGPT (chat-only) |
|---|---|---|
| Fetch a risk score (`GET /v1/risk-score/:address`, both the unpaid 402 call and the paid retry) | Harness HTTP tool | Base MCP `web_request` (host must be on the allowlist) |
| Pay for a resource (USDC transfer to `payTo`) | Base MCP `send_calls` | Base MCP `send_calls` |
| Fetch aggregate metrics (`GET /v1/metrics`, unpaid) | Harness HTTP tool | Base MCP `web_request` |
| File a dispute (`POST /v1/disputes`) | Harness HTTP tool + Base MCP `sign` for the proof signature | Base MCP `web_request` + `sign` |

## Endpoints

### `GET /v1/risk-score/:address`

x402-gated. First call, no `X-PAYMENT` header:

- Returns `402` with an x402 payment-requirements body:
  ```json
  {
    "x402Version": 1,
    "accepts": [{
      "scheme": "exact-direct",
      "network": "base",
      "maxAmountRequired": "10000",
      "resource": "https://vouch402.fly.dev/v1/risk-score/<address>",
      "description": "Vouch402 on-chain risk score for <address>",
      "mimeType": "application/json",
      "payTo": "0x...",
      "maxTimeoutSeconds": 300,
      "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
      "extra": { "name": "USDC", "resourceId": "0x<bytes32>" }
    }]
  }
  ```
  Pulled fresh from the live instance, not written from memory: as of
  the mainnet cutover this is Base mainnet + native mainnet USDC
  (`network`/`asset` are derived from live server config, not hardcoded,
  so this example stays accurate without further edits as long as it's
  re-checked against the live instance).
  `scheme: "exact-direct"`: the caller settles with a plain ERC-20
  `transfer`, not an EIP-3009 signature relayed through a facilitator.
  `resourceId` binds a specific payment to this specific quote; it
  expires after `maxTimeoutSeconds`.

- Retry with header `X-PAYMENT: base64(JSON.stringify({ resourceId, txHash, payer, jurisdictionAttestation: true }))`
  after the transfer confirms. `jurisdictionAttestation` is **required**,
  strictly `true` (not merely truthy): it certifies the caller (and
  whoever it's acting for) is not located in, and is not paying on behalf
  of anyone in, a Tier 1 restricted jurisdiction (see `## Risks &
  Warnings`). Since this flow is driven by an autonomous agent rather
  than a human clicking a checkbox, whatever orchestrates this plugin
  must set this field explicitly, never assume or hardcode it. Returns:
  - `200`: `{ "address": "0x...", "score": 0-100, "signals": { "walletAgeDays": number, "txCount": number, "uniqueContractInteractions": number, "flagged": boolean }, "attestationUid": "0x<bytes32>" }`
  - `402` again: quote expired/already consumed, tx not yet confirmed, or the payment doesn't match what was quoted (wrong amount/recipient/sender): server-verified, never trusts the retry's claims alone.
  - `403`: either the request's IP resolves to a Tier 1 restricted jurisdiction (technical geo-block, no exception), or `jurisdictionAttestation` was missing/`false` on the payload above (contractual gate, checked before payment verification).
  - `400`: malformed address, or `resourceId` doesn't match the `:address` in the URL.
  - `500`: an internal failure *after* payment was already verified, still recorded on-chain as a `status=error` fulfillment attestation (see `## Risks & Warnings`).

### `GET /v1/metrics`

Public, unpaid. Returns real (not estimated) aggregate counters:
`{ "uniquePayers": number, "totalRequestsServed": number, "totalVolumeUsdc": "<decimal string>", "attestationCount": number, "disputeCount": number }`.

### `POST /v1/disputes`

Body: `{ "refUID": "0x<bytes32>", "reasonCode": 0-3, "details": "string", "signature": "0x<hex>" }`.
`reasonCode`: `0=non-delivery, 1=malformed-response, 2=stale-data, 3=other`.
`signature` is an EIP-191 personal-sign over the literal string
`` `Vouch402 dispute\nrefUID: ${refUID}\nreasonCode: ${reasonCode}\ndetails: ${details}` ``:
the signer is recovered from the signature itself and must match the
`payer` recorded on the referenced fulfillment attestation; there is no
"claimed address" field to spoof. Returns `{ "disputeUid": "0x...", "disputant": "0x..." }` on success, `400` if the signature doesn't match.

## Orchestration

1. Build the resource URL: `<host>/v1/risk-score/<address>`.
2. `GET` it with no payment header, expect `402`; parse `accepts[0]` for `payTo`, `asset`, `maxAmountRequired`, `network`, and `extra.resourceId`.
3. Get the caller's wallet address (`get_wallets`).
4. Submit the payment via `send_calls`: one call, `{ to: asset, value: "0", data: <encoded transfer(payTo, maxAmountRequired)> }`, on `network`.
5. Wait for the payment call to confirm; capture its transaction hash.
6. `GET` the same resource URL again, with header `X-PAYMENT: base64(JSON.stringify({ resourceId, txHash, payer: <caller's address>, jurisdictionAttestation: true }))`.
7. On `200`, return `score`/`signals`/`attestationUid` to the user. On `402`, surface the reason (don't silently retry with a stale quote; go back to step 2 for a fresh one). On `403`, stop: this is not retryable with the same payload, see `## Risks & Warnings`.

## Submission

`send_calls`: a single unsigned call for the USDC payment (step 4 above): `{ to: <accepts[0].asset>, value: "0", data: encodeFunctionData({ abi: erc20TransferAbi, functionName: "transfer", args: [accepts[0].payTo, BigInt(accepts[0].maxAmountRequired)] }) }`, on `accepts[0].network`. The actual resource fetch (before and after payment) is plain HTTP, not a Base MCP submission: `## Surface Routing` covers how that HTTP call itself is made per surface.
For `POST /v1/disputes`, `sign` produces the personal-sign signature described in `## Endpoints`; the dispute submission itself is a plain HTTP POST, not a Base MCP write.

## Example Prompts

1. **"What's the risk score for 0xabc...123 on Base?"**
   -> Orchestration steps 1-7: quote, pay via `send_calls`, retry, return `score`/`signals`.
2. **"Check 0xabc...123 again."** (same address, new request)
   -> A fresh quote is required: `resourceId` is single-use. Repeat steps 1-7 from scratch; do not reuse a previous `resourceId` or `txHash`.
3. **"How much has Vouch402 processed so far?"**
   -> `GET /v1/metrics` directly (no payment) via the harness HTTP tool or `web_request`.
4. **"I paid for a score but got a 500 error, get my money back."**
   -> There is no refund path. Explain that the payment is irreversible and a `status=error` fulfillment attestation was recorded; walk the user through `POST /v1/disputes` (needs a `sign`-produced signature) instead of implying a refund is possible.

## Risks & Warnings

- **`irreversible`**: the USDC payment settles on-chain before the caller knows whether the resource server will actually fulfill successfully. If fulfillment fails after payment (a `500`), there is no refund mechanism: the recourse is `POST /v1/disputes` against the resulting `status=error` attestation, not a reversal. Never imply to the user that a failed fulfillment can be silently retried for free or refunded.
- **Jurisdiction restrictions**: Vouch402 cannot serve requests from, or on behalf of, a Tier 1 restricted jurisdiction (comprehensive-sanctions coverage under OFAC, plus mainland China on a separate legal basis; see `https://www.vouch402.xyz/legal` section 5). This is enforced two ways: an IP-level check on the server (returns `403` regardless of the payload), and the required `jurisdictionAttestation: true` field on the `X-PAYMENT` payload itself, which the caller (this plugin's orchestrator) must set explicitly and honestly. Do not set it to `true` on behalf of a user or agent whose location isn't actually known to be outside those jurisdictions.

## Notes

- The live instance (`vouch402.fly.dev`) runs on Base mainnet as of the
  Phase 3 cutover, matching `chains: [base]` above. Still worth checking
  a `402` response's `accepts[0].network` field directly rather than
  assuming, since that's what actually governs a given request.
- `score` is an explicitly-scoped v0 heuristic (wallet age, tx count, contract-interaction diversity, flag-list membership): not a complete risk model. The bundled flag list ships empty in this version (no unverified data bundled without a cited source); `flagged` will read `false` for every address until it's populated from a real source. Don't present `score` to end users as authoritative without this caveat.
- USDC on Base mainnet: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`.
- Fulfillment and dispute attestations are on EAS, native to Base (and Base Sepolia) as an OP Stack predeploy at `0x4200000000000000000000000000000000000021` (SchemaRegistry `0x4200000000000000000000000000000000000020`), resolvable via any standard EAS explorer/SDK, independent of this plugin.
