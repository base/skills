---
title: "Bitrefill Plugin"
description: "Buy gift cards, mobile top-ups, and eSIMs on Bitrefill via its MCP/CLI/REST, settling usdc_base x402 invoices through Base MCP's x402 payment on Base."
tags: [agent-commerce, gift-cards, esim, mobile-topup, payments]
name: bitrefill
version: 0.2.0
integration: hybrid
chains: [base]
requires:
  shell: optional
  allowlist: [api.bitrefill.com]
  externalMcp:
    name: bitrefill
    url: https://api.bitrefill.com/mcp
  cliPackage: "@bitrefill/cli@latest"
auth: oauth-on-install
risk: [pii, irreversible]
---

# Bitrefill Plugin

> [!IMPORTANT]
> Run Base MCP onboarding first (see SKILL.md). Bitrefill is **transport-dependent**: pick MCP, CLI, or REST based on the current surface (see `## Detection` and `## Surface Routing`). For USDC-on-Base checkout, authenticate Bitrefill once per session if the chosen path requires it — see `## Auth`.

## Overview

[Bitrefill](https://www.bitrefill.com) sells digital goods — gift cards, mobile top-ups, and eSIMs — across 180+ countries and 1,500+ brands. Codes deliver instantly after payment confirms. This plugin routes catalog search and invoice creation through Bitrefill's MCP (preferred), CLI, or REST API, then settles `usdc_base` purchases through Base MCP's **x402 payment** tool on Base. Bitrefill does not produce unsigned onchain calldata; the Base MCP leg is a payment submission (`x402` or `send`), not `send_calls`. Payment methods other than `usdc_base` (`balance`, `lightning`, `bitcoin`, etc.) are out of scope for the Base MCP leg — note them to the user but do not route them through Base MCP.

## Detection

Walk these checks **in order**. First match wins.

1. **Bitrefill MCP tools exposed?** If tools like `search-products`, `product-details`, or `buy-products` are callable, the Bitrefill MCP is installed → use the MCP path. Do not reach Bitrefill's REST API directly when the MCP is the supported path.
2. **Shell + npm available?** If `bitrefill --help` works (or `npx @bitrefill/cli@latest --help`), use the CLI path. Guest checkout needs no sign-in.
3. **Outbound HTTP only?** Use the REST API path via the harness HTTP tool or Base MCP `web_request` (host must be allowlisted).
4. **None of the above** on a chat-only surface with no MCP → tell the user Bitrefill requires MCP installation or a CLI harness, and link to `https://www.bitrefill.com`.

## Installation

### Bitrefill MCP (preferred)

URL: `https://api.bitrefill.com/mcp` (OAuth).

Detect the harness and walk through the matching step:

- **Claude Code:** `claude mcp add bitrefill --url https://api.bitrefill.com/mcp`
- **Codex:** add to `~/.codex/config.toml`:
  ```toml
  [mcp_servers.bitrefill]
  url = "https://api.bitrefill.com/mcp"
  bearer_token_env_var = "BITREFILL_API_KEY"
  ```
  OAuth: `codex mcp login bitrefill`.
- **Cursor / JSON-config harnesses:** add to `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global):
  ```json
  {
    "mcpServers": {
      "bitrefill": {
        "url": "https://api.bitrefill.com/mcp",
        "autoApprove": [
          "search-products", "product-details",
          "list-invoices", "get-invoice-by-id",
          "list-orders", "get-order-by-id"
        ]
      }
    }
  }
  ```
  Keep `buy-products` **out** of `autoApprove`.
- **Claude.ai web / Claude Desktop:** Customize → Connectors → Add custom connector, name `bitrefill`, URL `https://api.bitrefill.com/mcp`.
- **ChatGPT (Plus+):** Settings → Apps & Connectors → Add → URL `https://api.bitrefill.com/mcp`. Enable Developer Mode for write tools.
- **Other / unknown harness:** show the Cursor JSON snippet above and ask the user where their MCP config lives.

After install, ask the user to reconnect or restart the session so the new tools register.

The Bitrefill MCP advertises seven eCommerce tools: `search-products`, `product-details`, `buy-products`, `get-invoice-by-id`, `get-order-by-id`, `list-invoices`, `list-orders`. Read their descriptions from the MCP catalog — do not rely on a fixed parameter list in this file.

**Docs-only MCP:** `https://docs.bitrefill.com/mcp` indexes Bitrefill documentation. **Not for purchases.**

### Bitrefill CLI (shell path)

Requires `@bitrefill/cli` ≥ 0.3.0. No install step needed when using `npx`:

```bash
npx @bitrefill/cli@latest --help
```

Or install globally:

```bash
npm install -g @bitrefill/cli
```

## Auth

Bitrefill auth depends on the active transport:

| Transport | Auth model | Setup |
|---|---|---|
| MCP (interactive) | `oauth-on-install` | OAuth when the connector is installed; recommended for interactive use |
| MCP (headless) / REST (Personal) | `api-key` | Bearer token from [bitrefill.com/account/developers](https://www.bitrefill.com/account/developers); headless MCP via `bearer_token_env_var` (see `## Installation`) |
| CLI guest checkout | `none` | No sign-in — `buy-products --email` + crypto payment |
| CLI signed-in | OAuth + magic link | `bitrefill login --email` → `bitrefill verify --code` (see Bitrefill CLI docs for 2FA) |

For REST Business/Affiliate tiers, use Basic auth (`API_ID:API_SECRET`). Apply at [bitrefill.com/integrate](https://www.bitrefill.com/integrate) or [bitrefill.com/affiliate](https://www.bitrefill.com/affiliate).

**Never** auto-approve `buy-products` in any host's MCP config.

## Surface Routing

Reference the HTTP decision tree in [../references/custom-plugins.md](../references/custom-plugins.md).

| Capability | CLI harness (Codex, Claude Code, Cursor terminal) | Chat-only / MCP host (no shell) | HTTP-only (no MCP, no shell) |
|---|---|---|---|
| Search / browse catalog | Bitrefill MCP first → CLI → REST via harness HTTP tool | Bitrefill MCP → REST via `web_request` (allowlisted) | REST via `web_request` if allowlisted; else user-paste GET fallback for read-only endpoints |
| Create invoice (`buy-products`) | Bitrefill MCP first → CLI → REST POST via harness HTTP tool | Bitrefill MCP (install if missing) → REST POST via `web_request` | REST POST via harness HTTP tool or `web_request`; chat-only non-native hosts cannot POST — stop and explain |
| Pay with `usdc_base` | Base MCP x402 payment tool (primary) → `send` USDC fallback | Same — Base MCP x402 on every surface | Same |
| Pay with `balance` / `lightning` / other crypto | Bitrefill handles payment natively — **no Base MCP leg** | Same | Same |
| Poll / redeem | Active Bitrefill transport (`get-invoice-by-id`, `get-order-by-id`) | Same via MCP or `web_request` | Same |

**Shell-less surfaces without Bitrefill MCP:** help the user install the Bitrefill MCP (see `## Installation`), reconnect, then retry. Do not improvise a browser-scrape workaround — `www.bitrefill.com` returns 403 to datacenter IPs.

## Commands

CLI path — requires shell. Use `npx @bitrefill/cli@latest` or a global `bitrefill` install. Place `--json` before the subcommand for machine-readable stdout.

### Search

```bash
npx @bitrefill/cli@latest search-products --query "Steam" --country US
npx @bitrefill/cli@latest --json search-products --query "eSIM" --product_type esim --country IT | jq '.products'
```

`--country` = uppercase Alpha-2 (`US`, not `us`). `--product_type` = `giftcard` or `esim`.

### Product details

```bash
npx @bitrefill/cli@latest get-product-details --product_id "steam-usa" --currency USDC
```

Returns a `packages` array. Use `package_value` as `package_id` in `buy-products` — not the compound `<&>` key.

### Buy (guest — no login)

```bash
npx @bitrefill/cli@latest buy-products \
  --cart_items '[{"product_id":"steam-usa","package_id":5}]' \
  --payment_method usdc_base \
  --return_payment_link true \
  --email "user@example.com"
```

Response fields: `invoice_id`, `payment_link`, `x402_payment_url`, `payment_info` (`address`, `paymentUri`, `altcoinPrice`).

### Track / redeem

```bash
npx @bitrefill/cli@latest get-invoice-by-id --invoice_id "UUID"
npx @bitrefill/cli@latest get-order-by-id --order_id "ID"   # signed-in
```

Invoices expire after ~180 minutes.

## Endpoints

REST path — base URL `https://api.bitrefill.com/v2`. Auth: `Authorization: Bearer $BITREFILL_API_KEY` (Personal tier).

### `GET /ping`

Health check. Rate limit: 1 req / 3 s.

### `GET /products/search?q=...`

Keyword search. Returns product list.

### `GET /products/{id}`

Product details with `packages` array. Each package has a `package_id` in form `{product_id}<&>{value}`.

### `POST /invoices`

Create invoice (max 20 products).

```json
{
  "products": [{"product_id": "steam-usa", "package_id": "steam-usa<&>5", "quantity": 1}],
  "payment_method": "usdc_base",
  "return_payment_link": true
}
```

Response includes `invoice_id`, `x402_payment_url`, `payment_info`.

### `GET /invoices/{id}`

Poll payment status: `unpaid` → `payment_detected` → `payment_confirmed` → `complete`.

### `GET /orders/{id}`

Redemption info: `data.redemption_info.code`, `.link`, `.pin`, `.instructions`.

Rate limits: most endpoints 60 req / 10 min; `/products` and `/products/search` 60 req/min + 1000 product req/hr quota. Full table: [docs.bitrefill.com/docs/rate-limits](https://docs.bitrefill.com/docs/rate-limits).

## Orchestration

### Search and quote

1. Load this plugin after Base MCP onboarding.
2. Detect the active Bitrefill transport (`## Detection`).
3. Search: `search-products(query, country, product_type?)` via MCP, CLI, or `GET /products/search`.
4. Details: `product-details(product_id, currency="USDC")` — returns `packages` with denominations and pricing.
5. Present product, denomination, price, and payment method (`usdc_base`) to the user. **Wait for explicit approval** before creating an invoice.

### Create invoice

6. `buy-products(cart_items=[{product_id, package_id}], payment_method="usdc_base", return_payment_link=true)`.
   - MCP: max 15 items per call.
   - REST: max 20 products per `POST /invoices`.
   - CLI guest: include `--email` for the receipt.
7. Save `invoice_id`, `x402_payment_url`, and `payment_info` from the response.

### Settle via Base MCP (usdc_base only)

8. Read the Base MCP tool catalog for the x402 payment tool (advertised in SKILL.md onboarding).
9. Pay the `x402_payment_url` through Base MCP's x402 payment tool. If no x402 tool is exposed, fall back to `send` (see `## Submission`).
10. Show the approval URL per [../references/approval-mode.md](../references/approval-mode.md).
11. Poll `get_request_status` once after the user confirms approval.

### Poll and redeem

12. Poll Bitrefill `get-invoice-by-id(invoice_id)` until `status: "complete"`.
13. Call `get-order-by-id(order_id, include_redemption_info=true)` for the code, link, or eSIM install URL.
14. Deliver redemption material securely — see `## Risks & Warnings`.
15. Log the purchase: `invoice_id`, product, amount, payment method, timestamp.

## Submission

The Base MCP leg settles the Bitrefill invoice in USDC on Base. This is a payment submission, not calldata batching.

### Primary: x402 payment tool

Read the exact tool name and parameter schema from the Base MCP catalog. Typical mapping:

```json
{
  "url": "<x402_payment_url from buy-products response>"
}
```

The tool returns an `approvalUrl` and `requestId`. Follow [../references/approval-mode.md](../references/approval-mode.md): show the link, wait for user approval, poll `get_request_status` once.

### Fallback: `send` USDC on Base

If the x402 payment tool is unavailable, transfer USDC to the address in `payment_info`:

```json
{
  "chain": "base",
  "to": "<payment_info.address>",
  "amount": "<payment_info.altcoinPrice or quoted USDC amount>",
  "asset": "USDC"
}
```

Use the exact field names from the Base MCP `send` tool description. Confirm the amount matches the invoice quote before submitting.

### Not through Base MCP

- `payment_method: "balance"` + `auto_pay: true` — instant from pre-funded Bitrefill account; no Base MCP call.
- `payment_method: "lightning"` / `"bitcoin"` / other on-chain — Bitrefill-native payment; user or agent pays outside Base MCP.
- Redemption codes and order polling — Bitrefill transport only; **no** Base MCP submission.

## Example Prompts

**Buy a $25 Amazon US gift card with USDC on Base**
1. `search-products(query="Amazon", country="US", product_type="giftcard")` via Bitrefill MCP (or CLI/REST fallback).
2. `product-details(product_id="amazon-us", currency="USDC")` → pick the $25 package.
3. Present product, denomination, price, payment method. Wait for user confirmation.
4. `buy-products(cart_items=[{product_id, package_id}], payment_method="usdc_base", return_payment_link=true)`.
5. Pay `x402_payment_url` via Base MCP x402 payment tool → approval URL → `get_request_status`.
6. Poll `get-invoice-by-id` until `complete` → `get-order-by-id` for redemption code.

**Buy a 1GB Europe eSIM with USDC**
1. `search-products(query="eSIM", country="IT", product_type="esim")`.
2. `product-details` → select package `"1GB, 7 Days"` (exact, case-sensitive).
3. Confirm with user → `buy-products` with `payment_method="usdc_base"`.
4. Settle via Base MCP x402 → poll → deliver eSIM install URL securely.

**Check status of my Bitrefill invoice**
1. `get-invoice-by-id(invoice_id)` via active Bitrefill transport.
2. If `complete`: `get-order-by-id(order_id, include_redemption_info=true)`.
3. Return redemption info only if the user explicitly asked for it.

**What Steam gift cards are available in the US?** (browse-only, chat-only surface)
1. Detect transport — prefer Bitrefill MCP; else `web_request GET https://api.bitrefill.com/v2/products/search?q=steam` with Bearer auth.
2. Present matching products with denominations and prices.
3. Do **not** auto-buy. Ask if the user wants to proceed with a purchase.

## Risks & Warnings

- **`pii`** — Redemption codes, eSIM QR URLs, PINs, and receipt emails are bearer/cash-like personal data. Never paste codes in group chats, public channels, logs, version control, or voice/TTS output. Prefer in-memory handling; advise the user to redeem ASAP. Only return a code when the user explicitly asks.
- **`irreversible`** — Digital goods deliver instantly and are non-refundable once fulfilled (EU change-of-mind does not apply). Always confirm product, denomination, price, and payment method before `buy-products`. Never auto-buy without explicit user approval for the current session.
- **Spending cap** — Use a dedicated, low-balance Base Account for `usdc_base` payments. This plugin is not a wallet — never give the agent seed phrases or high-balance accounts.
- **Invoice expiry** — Invoices expire (~30 min guest CLI, ~180 min API). If expired, create a new invoice; do not retry payment on a stale `x402_payment_url`.
- **Package IDs** — Only values from `product-details` are accepted. Named/duration packages are exact and case-sensitive (e.g. `"1GB, 7 Days"`, `"1 Month"`).

## Notes

- USDC on Base: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- Country codes: uppercase Alpha-2 only (`US`, `IT`, `DE`).
- `package_id` formats: numeric (`5`, `50`), duration (`"1 Month"`), named (`"1GB, 7 Days"`). CLI uses `package_value`; REST uses `{product_id}<&>{value}`.
- Bitrefill source skill and upstream docs: [github.com/bitrefill/agents](https://github.com/bitrefill/agents), [docs.bitrefill.com](https://docs.bitrefill.com).
- Test products (Business/Affiliate only): [docs.bitrefill.com/docs/test-products](https://docs.bitrefill.com/docs/test-products).
