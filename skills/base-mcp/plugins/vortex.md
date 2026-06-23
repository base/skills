---
title: "Vortex Plugin"
description: "Create and operate Vortex fiat ramp flows from a trusted backend, using Base MCP only for Base Account wallet context and user-approved Base transactions."
tags: [payments, fiat, onramp, offramp]
name: vortex
version: 0.2.0
integration: http-api
chains: [base]
requires:
  shell: none
  allowlist: [api.vortexfinance.co, api-sandbox.vortexfinance.co]
  externalMcp: null
  cliPackage: null
auth: api-key
risk: [pii, slippage, irreversible]
---

# Vortex Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before using any Vortex flow. Vortex is a third-party service, not operated by Base. Keep Vortex `sk_*` partner secret keys server-side only; never place them in browser code, mobile apps, Base MCP prompts, logs, screenshots, support tickets, or user-visible messages.

## Overview

[Vortex](https://vortexfinance.co) is a crypto-to-fiat and fiat-to-crypto payment gateway. This plugin uses the Vortex SDK or REST API from a trusted backend to create quotes, register ramps, update route-specific signatures or transaction hashes, start ramps, and track status. Base MCP is used only for wallet context and user-approved Base transactions when the user's Base Account participates in a Vortex flow; Vortex itself does not run inside the Base MCP server.

The primary SDK package is `@vortexfi/sdk`. Use it in Node.js server runtimes when possible because it mirrors Vortex's reference behavior for ephemeral account generation and internal signing. For non-Node trusted backends, mirror the SDK behavior against the REST API and OpenAPI schema rather than inventing fields.

## Auth

Vortex partner integrations use a key pair:

| Key | Where it goes | Purpose |
| --- | --- | --- |
| `pk_live_*` / `pk_test_*` | Request body field `apiKey`; SDK config field `publicKey` | Partner attribution, tracking, and partner-specific quote behavior. |
| `sk_live_*` / `sk_test_*` | Server-side `X-API-Key` header; SDK config field `secretKey` | Partner authentication for ramp, webhook, status, history, and error-log operations. |

Rules:

- Keep all authenticated Vortex calls on the application backend or a trusted CLI-capable harness.
- Use live keys only with `https://api.vortexfinance.co` and test keys only with `https://api-sandbox.vortexfinance.co`.
- Do not ask the user to paste `sk_*` values into chat. If credentials are missing, tell them the backend must provide `VORTEX_SECRET_KEY` or equivalent.
- Public keys are not authentication. Do not use `pk_*` in the `X-API-Key` header.
- Amounts are decimal strings. Do not parse money amounts through JavaScript `Number`; use string-safe decimal handling.
- Quotes expire and are consumed at ramp registration. Check `expiresAt`; re-quote instead of reusing stale quotes.

SDK setup:

```js
import { VortexSdk } from "@vortexfi/sdk";

const vortex = new VortexSdk({
  apiBaseUrl: process.env.VORTEX_API_URL,
  publicKey: process.env.VORTEX_PUBLIC_KEY,
  secretKey: process.env.VORTEX_SECRET_KEY,
  storeEphemeralKeys: true
});
```

## Surface Routing

| Capability | Harness HTTP / server backend | Chat-only Base MCP surface |
| --- | --- | --- |
| Create quotes, register ramps, update ramps, start ramps, register webhooks | Use the application backend, SDK, or harness HTTP tool. This is the preferred path because Vortex POST requests require `X-API-Key` for partner flows. | Use Base MCP `web_request` only if the Vortex host is allowlisted and the current tool supports the needed method and headers. If unavailable, stop and tell the user a trusted backend or CLI-capable harness is required. |
| Discover fiat, crypto, countries, and payment methods | Use harness HTTP/backend first. | Use Base MCP `web_request` if allowlisted; GET-only user-paste fallback may work on restricted consumer surfaces. |
| Fetch Base Account address | Use Base MCP `get_wallets` only when the flow needs a destination or source wallet address. | Same. Do not fetch the wallet address just for onboarding. |
| User-wallet Base transactions returned by Vortex | Convert exact returned EVM `{ to, data, value }` fields into Base MCP `send_calls` only after user confirmation. | Same if Base MCP write tools are available. If returned transactions cannot be represented as Base MCP calls, stop and use the application's native wallet flow. |
| SDK-based BRL PIX onramp/offramp | Run `@vortexfi/sdk` on a trusted Node.js backend. | Unsupported directly in chat-only surfaces because the SDK manages ephemeral signing and server credentials. |

HTTP routing follows [../references/custom-plugins.md](../references/custom-plugins.md): harness HTTP/backend first, then Base MCP `web_request` if allowlisted, then GET-only user-paste fallback for discovery reads. Non-native POST APIs with custom headers usually cannot be completed on restricted chat-only surfaces.

## Endpoints

Base URLs:

| Environment | URL |
| --- | --- |
| Production | `https://api.vortexfinance.co` |
| Sandbox | `https://api-sandbox.vortexfinance.co` |

### `POST /v1/quotes`

Creates a quote for a known route and network. Include `apiKey` with the partner public key when partner attribution applies.

```json
{
  "rampType": "BUY",
  "from": "pix",
  "to": "base",
  "inputAmount": "100",
  "inputCurrency": "BRL",
  "outputCurrency": "USDC",
  "network": "base",
  "paymentMethod": "pix",
  "apiKey": "pk_live_..."
}
```

Response shape:

```json
{
  "id": "quote_...",
  "rampType": "BUY",
  "from": "pix",
  "to": "base",
  "inputAmount": "100",
  "inputCurrency": "BRL",
  "outputAmount": "19.42",
  "outputCurrency": "USDC",
  "fee": {
    "network": "0.42",
    "anchor": "1.50",
    "vortex": "0.75",
    "partner": "0.00",
    "total": "2.67",
    "currency": "BRL"
  },
  "expiresAt": "2025-05-18T12:35:00.000Z"
}
```

Response fields vary by route, but every quote includes the route, input and output amounts, fees, and expiry. Preserve all monetary fields as strings.

### `POST /v1/quotes/best`

Creates a best-route quote when Vortex should evaluate eligible routes. Omit `network`; optionally pass `networks`, for example `['base']`, to restrict eligible networks. The SDK does not call this endpoint today; use raw REST and then pass the returned quote into the SDK ramp flow.

Request example:

```json
{
  "rampType": "BUY",
  "from": "pix",
  "inputAmount": "100",
  "inputCurrency": "BRL",
  "outputCurrency": "USDC",
  "networks": ["base"]
}
```

Response shape matches `POST /v1/quotes`. If all eligible routes fail because of liquidity, surface the Vortex error to the user and suggest a smaller amount or retry later; do not invent a route.

### `GET /v1/quotes/{id}`

Retrieves a quote by ID. Quote IDs are not secrets, but do not expose them unnecessarily.

Path parameter: `id` is the quote ID returned by `POST /v1/quotes` or `POST /v1/quotes/best`. Response shape matches quote creation.

### `POST /v1/ramp/register`

Registers a ramp against a fresh quote. Direct API clients send the quote ID, route-specific `additionalData`, and public addresses for fresh ephemeral signing accounts. The matching ephemeral secret keys stay in the backend or SDK; never send them to Vortex, Base MCP, support, logs, or analytics.

BRL onramp `additionalData` requires:

```json
{
  "destinationAddress": "0x...",
  "taxId": "12345678900"
}
```

BRL PIX offramp `additionalData` requires:

```json
{
  "pixDestination": "user@example.com",
  "receiverTaxId": "12345678900",
  "taxId": "12345678900",
  "walletAddress": "0x..."
}
```

The response returns a `rampProcess`, any `depositQrCode` for PIX, and `unsignedTxs` that must be handled by the SDK, backend, or user's wallet according to signer.

Response shape:

```json
{
  "id": "ramp_...",
  "quoteId": "quote_...",
  "currentPhase": "initial",
  "status": "PENDING",
  "depositQrCode": "00020126...",
  "from": "pix",
  "to": "base",
  "inputAmount": "100",
  "inputCurrency": "BRL",
  "outputAmount": "19.42",
  "outputCurrency": "USDC",
  "walletAddress": "0x...",
  "unsignedTxs": []
}
```

`unsignedTxs` entries include their network, signer, phase, transaction format, and payload fields. Treat the returned payloads as the source of truth for signing or Base MCP submission.

### `POST /v1/ramp/update`

Submits signed ephemeral transactions and route-specific user transaction hashes. SDK-supported BRL buy flows call this internally during `registerRamp`; do not call a second onramp update when using the SDK. BRL sell/offramp flows usually require submitting the confirmed user-wallet transaction hash or hashes before `startRamp`.

Request shape:

```json
{
  "rampId": "ramp_...",
  "presignedTxs": [],
  "additionalData": {
    "squidRouterApproveHash": "0x...",
    "squidRouterSwapHash": "0x..."
  }
}
```

Use `presignedTxs` for ephemeral-signed payloads. Use `additionalData` for confirmed user-wallet transaction hashes keyed by returned phase. Response shape is the updated `rampProcess`.

### `POST /v1/ramp/start`

Starts a registered ramp after the required signatures, transaction hashes, and fiat steps are complete. For BRL onramp, call start only after the user completes the PIX payment.

Request shape:

```json
{
  "rampId": "ramp_..."
}
```

Response shape is the updated `rampProcess`. Do not report success until status polling or webhook delivery confirms completion.

### `GET /v1/ramp/{id}` and `GET /v1/ramp/{id}/errors`

Use status for live user-facing progress and errors for support diagnostics. Prefer webhooks for production reconciliation.

`GET /v1/ramp/{id}` returns the current `rampProcess`, including `status`, `currentPhase`, route amounts, and transaction hashes when present. `GET /v1/ramp/{id}/errors` returns structured errors with phase, timestamp, message, and recoverability where available. Use the same `rampId` returned by register.

### Discovery endpoints

Use discovery before presenting unknown options:

| Endpoint | Purpose |
| --- | --- |
| `GET /v1/supported-fiat-currencies` | Enabled fiat currencies. |
| `GET /v1/supported-cryptocurrencies?network=<network>` | Crypto tokens, optionally by network. |
| `GET /v1/supported-payment-methods?type=buy\|sell&fiat=<fiat>` | Payment methods and limits. |
| `GET /v1/supported-countries?fiatCurrency=<fiat>` | Countries by fiat. |

Discovery responses are arrays or objects of supported symbols, networks, countries, payment methods, and limit metadata. Treat response fields as Vortex-provided availability data and re-check with a quote before presenting a route as executable.

There is no single supported-corridors endpoint. For a specific combination, create a quote and handle unsupported-route or liquidity errors.

### Webhooks

Register a webhook with `POST /v1/webhook` and `X-API-Key: sk_*`:

```json
{
  "url": "https://your-app.example.com/vortex/webhook",
  "quoteId": "quote_...",
  "events": ["TRANSACTION_CREATED", "STATUS_CHANGE"]
}
```

The body must include exactly one of `quoteId` or `sessionId`. Deliveries include `X-Vortex-Signature` and `X-Vortex-Timestamp`; verify signatures over the raw request body using RSA-PSS with SHA-256 and the public key from `GET /v1/public-key`. Vortex retries failed webhook deliveries up to 5 times with 1s, 2s, 4s, 8s, and 16s backoff and a 30s timeout per attempt.

Webhook event shape:

```json
{
  "eventType": "STATUS_CHANGE",
  "timestamp": "2025-01-15T10:35:00.000Z",
  "payload": {
    "quoteId": "quote_...",
    "transactionId": "ramp_...",
    "sessionId": "session_...",
    "transactionStatus": "COMPLETE",
    "transactionType": "BUY"
  }
}
```

## Orchestration

### Quote flow

1. Run Base MCP onboarding first.
2. Identify direction: `BUY` is fiat to crypto; `SELL` is crypto to fiat.
3. Use discovery endpoints when the user has not specified a known fiat rail, token, country, or network.
4. Create a quote with `POST /v1/quotes` for a known route, or `POST /v1/quotes/best` for best-route selection.
5. Show the user a concise quote preview: direction, fiat rail, chain, input amount, expected output amount, fees, and expiry.
6. Require explicit confirmation before registering a ramp. If the quote expires, create a fresh quote.

### BRL PIX onramp to Base Account

1. Run Base MCP onboarding first.
2. Confirm KYC has already been completed through Vortex for the user's `taxId`. Do not invent or guess tax IDs.
3. Fetch the user's Base Account address with Base MCP `get_wallets` only if the destination wallet is the Base Account and the user did not provide a destination address.
4. Create a fresh `BUY` quote with `from: "pix"`, `inputCurrency: "BRL"`, target network such as `base`, and target asset such as `USDC`.
5. Register the ramp server-side with `destinationAddress` and `taxId`.
6. If using the SDK, rely on `registerRamp` to generate ephemerals, sign internal transactions, call `updateRamp`, and return the updated ramp process. If using raw REST, generate fresh ephemerals, sign the returned ephemeral-signed transactions exactly as returned, and submit them through `POST /v1/ramp/update` before starting.
7. Show the PIX QR code or copy-paste string from `rampProcess.depositQrCode`.
8. Wait until the user has paid PIX or the backend has observed payment.
9. Call `POST /v1/ramp/start` or `sdk.startRamp(rampProcess.id)`.
10. Track status with `GET /v1/ramp/{id}` or webhooks. Report success only when Vortex reports completion.

### BRL PIX offramp from Base Account

1. Run Base MCP onboarding first.
2. Confirm KYC has already been completed through Vortex for the sender `taxId`. Collect the recipient PIX key and `receiverTaxId`; do not fabricate either value.
3. Fetch the user's Base Account address with Base MCP `get_wallets` when it is the source wallet.
4. Create a fresh `SELL` quote with source network `base`, input asset, `to: "pix"`, and `outputCurrency: "BRL"`.
5. Register the ramp server-side with `pixDestination`, `receiverTaxId`, `taxId`, and `walletAddress`.
6. Inspect returned `unsignedTransactions` from the SDK, or the user-wallet subset of `rampProcess.unsignedTxs` from raw REST. If every user-wallet transaction is an EVM transaction representable as `{ to, data, value }`, map it into Base MCP `send_calls`. If not, stop and use the application's native wallet flow.
7. Present a concise preview of each transaction and ask for explicit confirmation.
8. Call Base MCP `send_calls` with `chain: "base"` and the mapped calls.
9. Surface the approval URL as a neutral "Approve Transaction" link, open it automatically in CLI-capable harnesses when possible, wait for the user to confirm they acted, and poll `get_request_status` once.
10. Collect the confirmed transaction hash or hashes and submit them to `POST /v1/ramp/update` according to the returned transaction `phase`.
11. Call `POST /v1/ramp/start` or `sdk.startRamp(rampProcess.id)`.
12. Track status with `GET /v1/ramp/{id}` or webhooks.

### Status and recovery

1. Poll `GET /v1/ramp/{id}` for live UI, or prefer webhooks in production.
2. Use `GET /v1/ramp/{id}/errors` when a ramp is stuck or failed.
3. Safe retries: create a new quote, get quote, get status, and update with the same accepted hashes or signed transactions.
4. Do not retry `registerRamp` against the same consumed quote after a ramp is created. If registration fails before a ramp is created, follow the SDK/backend error semantics and re-quote if needed.
5. Escalate to Vortex support if a ramp is stuck for more than 30 minutes, error logs repeat across attempts, or a complete ramp has no transaction hash after 10 minutes. Include `rampId`, environment, partner public key, redacted error logs, and transaction hash if present. Never include `sk_*`.

## Submission

Target Base MCP submission tool: **`send_calls`**, only for Vortex-returned Base EVM user-wallet transactions. Vortex API calls themselves are not submitted through Base MCP.

For a returned EVM user transaction:

```js
const calls = userWalletTxs.map(tx => ({
  to: tx.txData.to,
  data: tx.txData.data,
  value: tx.txData.value || "0x0"
}));
```

Then call Base MCP `send_calls` with the current tool schema, typically:

```json
{
  "chain": "base",
  "calls": [
    {
      "to": "0x...",
      "data": "0x...",
      "value": "0x0"
    }
  ]
}
```

Use only the fields returned by Vortex. Do not alter recipient, calldata, value, token, chain, amount, phase, or order. Preserve transaction order. If a returned transaction is not on Base or cannot be represented by Base MCP `send_calls`, stop and use the application's native wallet flow.

Map confirmed hashes back to Vortex by returned `phase`. Known user-wallet phase mapping:

| Returned user-wallet phase | `updateRamp` additionalData field |
| --- | --- |
| `squidRouterApprove` / `squidrouterApprove` | `squidRouterApproveHash` |
| `squidRouterSwap` / `squidrouterSwap` | `squidRouterSwapHash` |
| `squidRouterNoPermitTransfer` | `squidRouterNoPermitTransferHash` |
| `squidRouterNoPermitApprove` | `squidRouterNoPermitApproveHash` |
| `squidRouterNoPermitSwap` | `squidRouterNoPermitSwapHash` |
| `assethubToPendulum` | `assethubToPendulumHash` |

Submit user-wallet phases as confirmed onchain transaction hashes in `additionalData`, not as `presignedTxs`. The Vortex backend verifies submitted hashes against the unsigned blueprint issued during registration.

Follow [../references/approval-mode.md](../references/approval-mode.md) for the approval URL and request-status flow, and [../references/batch-calls.md](../references/batch-calls.md) for `send_calls` shape.

## Example Prompts

**Create a BRL PIX onramp to my Base Account**

1. Complete Base MCP onboarding.
2. Fetch the user's Base Account address only if needed as the destination.
3. Create a Vortex `BUY` quote for BRL PIX to the requested Base asset.
4. Register the ramp server-side with `destinationAddress` and KYC `taxId`.
5. Show the PIX payment instructions.
6. Wait for payment confirmation.
7. Start the ramp and track status.

**Offramp USDC from Base to BRL PIX**

1. Complete Base MCP onboarding.
2. Fetch the user's Base Account address only if needed as the source wallet.
3. Create a Vortex `SELL` quote from Base USDC to BRL PIX.
4. Register the ramp server-side with PIX destination, receiver tax ID, sender tax ID, and wallet address.
5. Convert returned Base user-wallet transactions into Base MCP calls only if fields map exactly.
6. Require user confirmation.
7. Open the Base MCP approval URL.
8. After confirmation, map transaction hashes by returned phase into `updateRamp`.
9. Call `startRamp`, then track status.

**What fiat and crypto options does Vortex currently support?**

1. Use discovery endpoints for fiat currencies, cryptocurrencies, payment methods, and countries.
2. Summarize returned options neutrally.
3. For a specific corridor, create a quote and handle unsupported-route or liquidity errors instead of hard-coding a corridor matrix.

**Set up Vortex webhooks for this quote**

1. Confirm the backend has `sk_*` available server-side.
2. Register `POST /v1/webhook` with exactly one of `quoteId` or `sessionId`.
3. Store the webhook ID.
4. Verify deliveries with `X-Vortex-Signature`, `X-Vortex-Timestamp`, RSA-PSS / SHA-256, and `GET /v1/public-key`.

## Risks & Warnings

- `pii`: Vortex BRL PIX flows handle tax IDs, PIX keys, KYC status, wallet addresses, and transaction records. Collect only what the flow requires. Do not echo full tax IDs or PIX keys unnecessarily, and never include them in logs or support tickets unless the user explicitly requests a redacted support handoff.
- `slippage`: Quotes pin expected output for a short time, but routes can expire or become unavailable due to liquidity. Do not reuse stale quotes, do not promise final output before Vortex confirms completion, and ask the user to re-quote if the route fails.
- `irreversible`: PIX payments and onchain transactions cannot be silently undone once sent or approved. Always show a concise preview and require explicit confirmation before any Base MCP `send_calls` flow, before registering a ramp from a quote, and before starting a ramp after payment/signing steps.

## Notes

- Vortex SDK: `@vortexfi/sdk`.
- Node SDK supported direct flow today is primarily BRL PIX. Docs and APIs expose broader route surfaces; use discovery endpoints and quote attempts for live availability rather than hard-coding a corridor matrix.
- The SDK is Node.js-only and opens chain-side connections for supported flows. Reuse one SDK instance per backend process when possible.
- The SDK does not retry HTTP requests, poll status, encrypt ephemeral backups, or drive BRL KYC. Production backends should add those operational layers.
- The SDK stores ephemeral keys in `ephemerals_{rampId}.json` when `storeEphemeralKeys` is enabled; secure or replace this storage in production.
- Direct API clients must generate fresh ephemeral accounts, store secrets securely, validate every payload before signing, and submit exactly the returned signed payloads or hashes.
- EVM ephemeral-signed phases require one primary signed transaction plus backup nonce variants returned under metadata. Treat this as backup material per ephemeral-signed phase, not as five independent user approvals.
- Do not present Vortex as a Base-operated service.
- Do not sign, broadcast, or manage private keys outside Base MCP for Base Account user-wallet transactions.
- Do not generate fake PIX keys, tax IDs, quote IDs, ramp IDs, or transaction hashes.
- Do not submit user-wallet phases as `presignedTxs`; submit confirmed transaction hashes in `additionalData`.
