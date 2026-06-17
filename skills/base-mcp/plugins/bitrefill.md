---
title: "Bitrefill Plugin"
description: "Buy gift cards, mobile top-ups, and eSIMs on Bitrefill via @bitrefill/cli (preferred when shell is available) or MCP on shell-less surfaces — authless by default — settling usdc_base x402 invoices through Base MCP on Base."
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
auth: none
risk: [pii, irreversible]
---

# Bitrefill Plugin

> [!IMPORTANT]
> Run Base MCP onboarding first (see SKILL.md). Default to **authless** guest checkout; escalate identity only for account-scoped features (`list-orders`, balance pay). When shell is available, prefer `@bitrefill/cli` via `npx` or a global install for **all** Bitrefill operations (see `## Detection`). Use Bitrefill MCP only on shell-less surfaces. Keep `buy-products` **out** of MCP `autoApprove`.

## Overview

[Bitrefill](https://www.bitrefill.com) sells digital goods — gift cards, mobile top-ups, and eSIMs — across 180+ countries and 1,500+ brands. Codes deliver instantly after payment confirms. This plugin routes catalog search and invoice creation through `@bitrefill/cli` when shell is available, otherwise through Bitrefill MCP, then settles `usdc_base` purchases through Base MCP's **x402 payment** tool on Base. Bitrefill does not produce unsigned onchain calldata; the Base MCP leg is a payment submission (`x402` or `send`), not `send_calls`. Payment methods other than `usdc_base` (`balance`, `lightning`, `bitcoin`, etc.) are out of scope for the Base MCP leg — note them to the user but do not route them through Base MCP.

Identity escalates only when needed: **Tier 1 authless** (default — browse and guest buy with no account) → **Tier 2 CLI auto `client_credentials`** (shell, zero human step) → **Tier 3 account binding** (`login` / `verify`, existing Bitrefill customers only). On shell surfaces, use the CLI for every Bitrefill call — it auto-provisions a headless machine session on the first command. On shell-less surfaces, use MCP with connector OAuth at install.

## Detection

Order. First match wins.

1. **Shell + npm?** `bitrefill --help` or `npx @bitrefill/cli@latest --help` → CLI for all ops. First cmd auto-provisions `client_credentials`. Guest buy = no sign-in. Prefer `npx` if no global install.
2. **No shell, MCP tools exposed?** (`search-products`, `product-details`, `buy-products`, …) → MCP.
3. **Neither** → shell: `npx @bitrefill/cli@latest --help` then CLI; shell-less: install MCP (`## Installation`), reconnect; **stop** if both fail. `https://www.bitrefill.com` = human browse only — no scrape.

## Installation

### CLI (shell — preferred)

`@bitrefill/cli` ≥ 0.3.0. Wraps same MCP; auto machine session. All Bitrefill ops when shell exists.

```bash
npx @bitrefill/cli@latest --help
npm install -g @bitrefill/cli    # global install alternative
```

### Shell-less vs headless auth

- **Shell + CLI:** all calls via CLI. First cmd → OAuth `client_credentials` → `~/.config/bitrefill-cli/<host>.v1.json`. Identity `unregistered` until `login`/`verify`. Zero human OAuth.
- **Shell-less + MCP:** connector OAuth at install; harness persists tokens ([../references/install.md](../references/install.md)). MCP only when no shell.

No API keys, env vars, direct HTTP. Shell available → never MCP even if MCP tools exposed.

### MCP (shell-less)

`https://api.bitrefill.com/mcp` — OAuth at connector setup.

- **Claude Code:** `claude mcp add bitrefill --url https://api.bitrefill.com/mcp`
- **Codex:** `~/.codex/config.toml`:

  ```toml
  [mcp_servers.bitrefill]
  url = "https://api.bitrefill.com/mcp"
  ```

  Then `codex mcp login bitrefill` once (terminal, outside chat).
- **Cursor / JSON:** `.cursor/mcp.json` or `~/.cursor/mcp.json`:

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

  `buy-products` **out** of `autoApprove`.
- **Claude.ai / Desktop:** Connectors → custom connector `bitrefill` → URL above.
- **ChatGPT:** Apps & Connectors → URL above, Auth **OAuth**, Developer Mode for writes.
- **Other:** Cursor JSON snippet; ask where MCP config lives.

Reconnect/restart after install. Seven tools — read MCP catalog at runtime. Docs-only: `https://docs.bitrefill.com/mcp` — not for purchases.

## Surface Routing

| Capability | Shell (CLI harness) | No shell (MCP) |
| --- | --- | --- |
| Search / browse | **CLI** (`npx @bitrefill/cli@latest`) | MCP |
| Invoice (`buy-products`) | **CLI** | MCP |
| Pay `usdc_base` | Base MCP x402 → `send` fallback | Same |
| Balance / lightning / other crypto | Bitrefill-native **CLI** — no Base MCP | MCP |
| Poll / redeem | **CLI** | MCP |
| Account (`list-orders`, `login`) | **CLI** | MCP |

Shell + npm → CLI every row, even if MCP also exposed.

**Tiers:** T1 authless (search, guest buy `--email`, invoice poll) · T2 CLI auto session (`whoami` → `unregistered` + `client_id`) · T3 `login`→`verify` (`list-orders`, balance pay, account orders; `whoami` → `registered`).

No shell, no MCP → install MCP + OAuth, reconnect, **stop**. No env/API/HTTP fallback. No scrape `www.bitrefill.com` (403 datacenter).

## Commands

Shell → `npx @bitrefill/cli@latest` or global `bitrefill`. `--json` before subcmd: result stdout, status stderr.

**Identity:** `whoami` · `login --email` · `verify --code [--otp]` · `logout` · `reset` · `manifest` · `llm-context`

```bash
npx @bitrefill/cli@latest --json whoami
npx @bitrefill/cli@latest login --email "user@example.com"
npx @bitrefill/cli@latest verify --code "123456"
npx @bitrefill/cli@latest verify --code "123456" --otp "654321"
npx @bitrefill/cli@latest logout && npx @bitrefill/cli@latest reset
npx @bitrefill/cli@latest manifest
npx @bitrefill/cli@latest llm-context -o BITREFILL-MCP.md
```

`whoami --json` → `{ identity, client_id?, email? }`. `browser_url` in login/verify → user opens passkey flow. `reset` rotates session; re-auth drops bound email.

**Search:** `--country` Alpha-2 uppercase. `--product_type` `giftcard`|`esim`.

```bash
npx @bitrefill/cli@latest search-products --query "Steam" --country US
npx @bitrefill/cli@latest --json search-products --query "eSIM" --product_type esim --country IT
```

**Details:** `package_value` → `package_id` in buy — only from response.

```bash
npx @bitrefill/cli@latest get-product-details --product_id "steam-usa" --currency USDC
```

**Guest buy:**

```bash
npx @bitrefill/cli@latest buy-products \
  --cart_items '[{"product_id":"steam-usa","package_id":5}]' \
  --payment_method usdc_base \
  --return_payment_link true \
  --email "user@example.com"
```

→ `invoice_id`, `payment_link`, `x402_payment_url`, `payment_info`.

**Track:**

```bash
npx @bitrefill/cli@latest get-invoice-by-id --invoice_id "UUID"
npx @bitrefill/cli@latest get-order-by-id --order_id "ID"   # T3
```

Invoices ~30 min TTL — stale → new invoice.

## Orchestration

### Search + buy (default, no account)

1. Base MCP onboarding done.
2. Transport per `## Detection`.
3. Search + details (CLI if shell else MCP, `currency=USDC`).
4. Quote → **explicit approval**.
5. `buy-products` `usdc_base` `return_payment_link=true`; CLI `--email`; MCP max 15 items.
6. Save `invoice_id`, `x402_payment_url`, `payment_info`.

### CLI headless session

First CLI cmd → `client_credentials`. Optional `whoami --json`. Stale auth → `reset` retry.

### Account flows (T3)

Before `list-orders` / balance / account orders: `login` → `verify` (+ `--otp` / `browser_url`). `whoami` = `registered`. Then account tools.

### Settle (`usdc_base`)

1. Base MCP x402 tool on `x402_payment_url`; else `send` (`## Submission`).
2. Approval URL → [approval-mode.md](../references/approval-mode.md).
3. `get_request_status` once after user approves.

### Poll + redeem

`get-invoice-by-id` until `complete` → `get-order-by-id` + redemption. Secure delivery (`## Risks`). Log invoice/product/amount/method/time.

## Submission

Payment submission, not calldata batch.

**Primary — x402:**

```json
{ "url": "<x402_payment_url from buy-products>" }
```

→ `approvalUrl`, `requestId`. [approval-mode.md](../references/approval-mode.md).

**Fallback — `send` USDC Base:**

```json
{
  "chain": "base",
  "to": "<payment_info.address>",
  "amount": "<payment_info.altcoinPrice or quoted USDC>",
  "asset": "USDC"
}
```

Match Base MCP `send` schema. Amount = quote.

**Not Base MCP:** balance+`auto_pay` (T3) · lightning/bitcoin/etc native · poll/redeem via CLI/MCP only.

## Example Prompts

### $25 Amazon US gift card, USDC Base (authless)

1. CLI search → details → confirm.
2. `buy-products` + `--email`.
3. Base MCP x402 → poll invoice → order redemption.

### 1GB Europe eSIM

1. CLI search IT esim → `"1GB, 7 Days"` exact.
2. Buy + x402 + poll → deliver eSIM URL secure.

### Invoice status

1. `get-invoice-by-id`. Complete → `get-order-by-id` if user asked redemption.

### Steam US browse (shell-less)

1. Install MCP + OAuth if missing.
2. MCP search. No auto-buy.

### Order history (T3)

1. CLI: `whoami` → `login`/`verify` if needed → `list-orders`.
2. MCP shell-less: auth connector → `list-orders`.

## Risks & Warnings

- **`pii`** — Redemption codes, eSIM QR URLs, PINs, and receipt emails are bearer/cash-like personal data. Never paste codes in group chats, public channels, logs, version control, or voice/TTS output. Prefer in-memory handling; advise the user to redeem ASAP. Only return a code when the user explicitly asks.
- **`irreversible`** — Digital goods deliver instantly and are non-refundable once fulfilled (EU change-of-mind does not apply). Always confirm product, denomination, price, and payment method before `buy-products`. Never auto-buy without explicit user approval for the current session.
- **Spending cap** — Use a dedicated, low-balance Base Account for `usdc_base` payments. This plugin is not a wallet — never give the agent seed phrases or high-balance accounts.
- **Invoice expiry** — Invoices expire (~30 min typical). If expired, create a new invoice; do not retry payment on a stale `x402_payment_url`.
- **Package IDs** — Only values from `product-details` / `get-product-details`. Case-sensitive (`"1GB, 7 Days"`, `"1 Month"`).
- **CLI session token** — `~/.config/bitrefill-cli/<host>.v1.json` sensitive; `reset` rotates.
- **Account binding loss** — Re-auth clears email; re `login`/`verify` before account tools.

## Notes

- USDC Base: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- Country: Alpha-2 uppercase
- `package_id`: numeric | duration string | named string; from `package_value`
- Identity: `unregistered` | `registered`; state `~/.config/bitrefill-cli/<host>.v1.json`
- Agent: `--json`, `manifest`, `llm-context`
- Docs: [github.com/bitrefill/agents](https://github.com/bitrefill/agents), [docs.bitrefill.com](https://docs.bitrefill.com)
