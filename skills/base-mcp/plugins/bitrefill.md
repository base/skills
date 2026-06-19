---
title: "Bitrefill Plugin"
description: "Buy gift cards, mobile top-ups, and eSIMs via Bitrefill x402 — connect once (SIWX→JWT) for fee-free browse through Base MCP, or pay-per-call x402; CLI and MCP for existing Bitrefill accounts."
tags: [agent-commerce, gift-cards, esim, mobile-topup, payments]
name: bitrefill
version: 0.3.0
integration: hybrid
chains: [base]
requires:
  shell: optional
  allowlist: [api.bitrefill.com]
  externalMcp:
    name: bitrefill
    transport: http
    url: https://api.bitrefill.com/mcp
  cliPackage: "@bitrefill/cli@latest"
auth: siwe-jwt
risk: [pii, irreversible]
---

# Bitrefill Plugin

> [!IMPORTANT]
> Run Base MCP onboarding first (see SKILL.md). **Path 1** (connect→JWT) is the default for agent-commerce: one SIWX signature, then fee-free browse via `web_request` until the token expires (~2h). Fall back to **Path 2** (pay-per-call x402) for multi-wallet or stateless agents. Use **Path 3** (CLI) or **Path 4** (MCP) only when the user has an existing Bitrefill account. Keep `buy-products` **out** of MCP `autoApprove`.

## Overview

[Bitrefill](https://www.bitrefill.com) sells digital goods — gift cards, mobile top-ups, and eSIMs — across 180+ countries and 1,500+ brands. Codes deliver instantly after payment confirms.

Four execution paths, in preference order:

1. **Connect → JWT (x402-native, zero agent egress)** — `POST /x402/connect` with one SIWX signature mints a session JWT. Send it as `X-Access-Token` on every gated `web_request` to `api.bitrefill.com` — no per-route micro-fees, no re-signing until expiry (~2h). Only `invoice/pay` costs money (Base MCP `x402`). All HTTP goes through Base MCP `web_request`; signing through Base MCP `sign`.
2. **Pay-per-call x402** — each discovery route returns HTTP 402; Base MCP `x402` pays the micro-fee automatically. No session, no SIWX. Best for multi-wallet or stateless agents, or when SIWX helpers cannot run.
3. **CLI** (`@bitrefill/cli`, shell) — efficient for users with an existing Bitrefill account (`login`/`verify`, `list-orders`, balance pay).
4. **Bitrefill MCP** (`https://api.bitrefill.com/mcp`, shell-less) — best chat-client UX for existing Bitrefill users (OAuth at install).

All paths converge on Base MCP **`x402`** (→ `send` USDC Base fallback) for invoice payment. Bitrefill does not produce unsigned onchain calldata — payment submission, not `send_calls`. Payment methods other than USDC x402 (`balance`, `lightning`, `bitcoin`, etc.) are out of scope for the Base MCP leg.

## Detection

Pick a path before any Bitrefill call. Base MCP onboarding must be done first.

**Agent-commerce (pay with crypto, no Bitrefill account):**

1. Base MCP `sign` + `web_request` + `x402` available, agent can persist a token → **Path 1** (connect→JWT).
2. Otherwise, or multi-wallet / no session persistence → **Path 2** (pay-per-call x402 via Base MCP `x402` on each 402).
3. Cannot build SIWX message/header (sandbox blocks even the stdlib helpers in `## Auth`) → **Path 2** only; tell the user connect is unavailable.

**Existing Bitrefill account:**

4. Shell + npm (`npx @bitrefill/cli@latest --help`) → **Path 3** (CLI). First cmd auto-provisions `client_credentials`.
5. No shell, Bitrefill MCP tools exposed (`search-products`, `buy-products`, …) → **Path 4** (MCP).
6. Neither → install per `## Installation`, reconnect; **stop** if both fail.

Never scrape `https://www.bitrefill.com` (403 from datacenters). Never call `api.bitrefill.com` directly when the agent has no HTTP tool — route everything through Base MCP `web_request` (paths 1–2) or CLI/MCP (paths 3–4).

## Installation

### Path 1–2: x402-native (no install)

Requires Base MCP only. Host `api.bitrefill.com` must be on the Base MCP `web_request` allowlist.

### Path 3: CLI (shell)

`@bitrefill/cli` ≥ 0.3.0. No global install required.

```bash
npx @bitrefill/cli@latest --help
npm install -g @bitrefill/cli    # optional global install
```

First command auto-provisions OAuth `client_credentials` → `~/.config/bitrefill-cli/<host>.v1.json`. Identity `unregistered` until `login`/`verify`.

### Path 4: Bitrefill MCP (shell-less)

`https://api.bitrefill.com/mcp` — OAuth at connector setup ([../references/install.md](../references/install.md)).

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

Reconnect/restart after install. Read the MCP tool catalog at runtime — do not hardcode tool lists.

## Auth

Path 1 uses **SIWX → JWT**. Path 2 needs no auth. Path 3 uses CLI `client_credentials` (+ optional `login`/`verify`). Path 4 uses connector OAuth at install.

### Connect → JWT (Path 1)

1. `web_request` `POST https://api.bitrefill.com/x402/connect` (empty body) → **402** with `payment-required` header (also mirrored in JSON body). Parse base64 → `extensions["sign-in-with-x"]`.
2. `get_wallets` → `baseAccount.address` (often lowercase).
3. Pick the Base chain from `supportedChains`: `{ chainId: "eip155:8453", type: "eip191" }`.
4. Build the EIP-4361 message with the helpers below (address **must** be EIP-55 checksummed — server rejects lowercase).
5. Base MCP `sign` with `type: "personal_sign"`, `data: { message: <exact string> }` → approval URL → `get_request_status` → `signature`.
6. Assemble the **decomposed** payload (`domain`, `address`, `uri`, `version`, `chainId` as CAIP-2, `type`, `nonce`, `issuedAt`, optional fields, `signature` — **not** `{ message, signature }`). Base64-encode → `SIGN-IN-WITH-X` request header.
7. Re-`POST /x402/connect` with that header → `{ token, token_header: "X-Access-Token", expires_in }` (default ~7200 s).
8. Attach `X-Access-Token: <token>` (raw JWT, **no** `Bearer` prefix — Base MCP strips `Authorization`) on every subsequent gated `web_request`. Token bypasses micro-fees and SIWX re-signing; `invoice/pay` is never waived.

Smart-wallet note: Base Account signatures verify server-side via EIP-1271/6492; header `type` stays `"eip191"`.

**Path 2:** skip this section entirely — Base MCP `x402` handles each 402 micro-fee without SIWX.

### SIWX helpers (no external libraries)

Locked-down agent sandboxes may forbid `npm i` / `pip install`. These helpers use only built-ins. Verified against `siwe@2.3.2`, `@spruceid/siwe-parser`, and `@x402/extensions@2.3.0`. Base MCP `sign` performs the actual EIP-191 signing — the agent never holds a private key.

**JavaScript** (Node 18+ / modern browser; `BigInt` required for keccak):

```javascript
const RC = [0x0000000000000001n,0x0000000000008082n,0x800000000000808an,0x8000000080008000n,0x000000000000808bn,0x0000000080000001n,0x8000000080008081n,0x8000000000008009n,0x000000000000008an,0x0000000000000088n,0x0000000080008009n,0x000000008000000an,0x000000008000808bn,0x800000000000008bn,0x8000000000008089n,0x8000000000008003n,0x8000000000008002n,0x8000000000000080n,0x000000000000800an,0x800000008000000an,0x8000000080008081n,0x8000000000008080n,0x0000000080000001n,0x8000000080008008n];
const PI = [10,7,11,17,18,3,5,16,8,21,24,4,15,23,19,13,12,2,20,14,22,9,6,1];
const R = [1,3,6,10,15,21,28,36,45,55,2,14,27,41,56,8,25,43,62,18,39,61,20,44];
const MASK = (1n << 64n) - 1n;
function rotl(x, n) { n = BigInt(n); return ((x << n) | (x >> (64n - n))) & MASK; }
function keccakF(s) {
  const bc = new Array(5).fill(0n);
  for (let round = 0; round < 24; round++) {
    for (let i = 0; i < 5; i++) bc[i] = s[i]^s[i+5]^s[i+10]^s[i+15]^s[i+20];
    for (let i = 0; i < 5; i++) { const t = bc[(i+4)%5]^rotl(bc[(i+1)%5],1); for (let j = 0; j < 25; j += 5) s[j+i] ^= t; }
    let t = s[1];
    for (let i = 0; i < 24; i++) { const j = PI[i], tmp = s[j]; s[j] = rotl(t, R[i]); t = tmp; }
    for (let j = 0; j < 25; j += 5) { for (let i = 0; i < 5; i++) bc[i] = s[j+i]; for (let i = 0; i < 5; i++) s[j+i] ^= (~bc[(i+1)%5]) & bc[(i+2)%5]; }
    s[0] ^= RC[round];
  }
}
function keccak256Hex(input) {
  const bytes = typeof input === "string" ? new TextEncoder().encode(input) : input;
  const rate = 136, padded = new Uint8Array(Math.ceil((bytes.length + 2) / rate) * rate);
  padded.set(bytes); padded[bytes.length] = 0x01; padded[padded.length - 1] |= 0x80;
  const st = new Array(25).fill(0n);
  for (let off = 0; off < padded.length; off += rate) {
    for (let i = 0; i < rate / 8; i++) { let v = 0n; for (let b = 0; b < 8; b++) v |= BigInt(padded[off + i*8 + b]) << BigInt(b*8); st[i] ^= v; }
    keccakF(st);
  }
  let hex = "";
  for (let i = 0; i < 4; i++) for (let b = 0; b < 8; b++) hex += ((Number((st[i] >> BigInt(b*8)) & 0xffn)).toString(16)).padStart(2, "0");
  return hex;
}
function toChecksumAddress(addr) {
  const lower = addr.toLowerCase().replace(/^0x/, "");
  const hash = keccak256Hex(lower);
  let out = "0x";
  for (let i = 0; i < lower.length; i++) out += parseInt(hash[i], 16) >= 8 ? lower[i].toUpperCase() : lower[i];
  return out;
}
function buildSiweMessage(info, address, chainIdCaip2) {
  const chainNum = parseInt(/^eip155:(\d+)$/.exec(chainIdCaip2)[1], 10);
  const suffix = [`URI: ${info.uri}`,`Version: ${info.version}`,`Chain ID: ${chainNum}`,`Nonce: ${info.nonce}`,`Issued At: ${info.issuedAt}`];
  if (info.expirationTime) suffix.push(`Expiration Time: ${info.expirationTime}`);
  if (info.notBefore) suffix.push(`Not Before: ${info.notBefore}`);
  if (info.requestId) suffix.push(`Request ID: ${info.requestId}`);
  if (info.resources?.length) suffix.push(["Resources:", ...info.resources.map(r => `- ${r}`)].join("\n"));
  let prefix = `${info.domain} wants you to sign in with your Ethereum account:\n${address}`;
  if (info.statement) prefix = `${prefix}\n\n${info.statement}\n`;
  return `${prefix}\n${suffix.join("\n")}`;
}
function encodeSiwxHeader(payload) {
  const bytes = new TextEncoder().encode(JSON.stringify(payload));
  return btoa(Array.from(bytes, b => String.fromCharCode(b)).join(""));
}
```

**Python** (3.9+; stdlib only):

```python
import base64, json, struct
RC = [0x0000000000000001,0x0000000000008082,0x800000000000808A,0x8000000080008000,0x000000000000808B,0x0000000080000001,0x8000000080008081,0x8000000000008009,0x000000000000008A,0x0000000000000088,0x0000000080008009,0x000000008000000A,0x000000008000808B,0x800000000000008B,0x8000000000008089,0x8000000000008003,0x8000000000008002,0x8000000000000080,0x000000000000800A,0x800000008000000A,0x8000000080008081,0x8000000000008080,0x0000000080000001,0x8000000080008008]
PI = [10,7,11,17,18,3,5,16,8,21,24,4,15,23,19,13,12,2,20,14,22,9,6,1]
R = [1,3,6,10,15,21,28,36,45,55,2,14,27,41,56,8,25,43,62,18,39,61,20,44]
MASK = (1 << 64) - 1
def _rotl(x, n): n &= 63; return ((x << n) | (x >> (64 - n))) & MASK
def _keccak_f(st):
    bc = [0]*5
    for _ in range(24):
        for i in range(5): bc[i] = st[i]^st[i+5]^st[i+10]^st[i+15]^st[i+20]
        for i in range(5):
            t = bc[(i+4)%5] ^ _rotl(bc[(i+1)%5], 1)
            for j in range(0,25,5): st[j+i] ^= t
        t = st[1]
        for i in range(24): j, tmp = PI[i], st[PI[i]]; st[j] = _rotl(t, R[i]); t = tmp
        for j in range(0,25,5):
            for i in range(5): bc[i] = st[j+i]
            for i in range(5): st[j+i] ^= (~bc[(i+1)%5]) & bc[(i+2)%5]
        st[0] ^= RC[_]
def keccak256_hex(data):
    if isinstance(data, str): data = data.encode()
    rate = 136; padded = bytearray(data); padded.append(0x01)
    while len(padded) % rate != rate - 1: padded.append(0)
    padded.append(0x80)
    st = [0]*25
    for off in range(0, len(padded), rate):
        block = padded[off:off+rate]
        for i in range(rate//8):
            v = sum(block[i*8+b] << (b*8) for b in range(8))
            st[i] ^= v
        _keccak_f(st)
    return b"".join(struct.pack("<Q", st[i]) for i in range(4)).hex()
def to_checksum_address(addr):
    lower = addr.lower().replace("0x", "")
    h = keccak256_hex(lower)
    return "0x" + "".join(ch.upper() if int(h[i],16) >= 8 else ch for i, ch in enumerate(lower))
def build_siwe_message(info, address, chain_id_caip2):
    chain_num = int(chain_id_caip2.split(":")[1])
    suffix = [f"URI: {info['uri']}", f"Version: {info['version']}", f"Chain ID: {chain_num}", f"Nonce: {info['nonce']}", f"Issued At: {info['issuedAt']}"]
    if info.get("expirationTime"): suffix.append(f"Expiration Time: {info['expirationTime']}")
    if info.get("notBefore"): suffix.append(f"Not Before: {info['notBefore']}")
    if info.get("requestId"): suffix.append(f"Request ID: {info['requestId']}")
    if info.get("resources"): suffix.append("Resources:\n" + "\n".join(f"- {r}" for r in info["resources"]))
    prefix = f"{info['domain']} wants you to sign in with your Ethereum account:\n{address}"
    if info.get("statement"): prefix = prefix + "\n\n" + info["statement"] + "\n"
    return prefix + "\n" + "\n".join(suffix)
def encode_siwx_header(payload):
    return base64.b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()
```

**Decomposed header payload** (after `sign` returns `signature`):

```json
{
  "domain": "api.bitrefill.com",
  "address": "0x<EIP-55 checksummed>",
  "statement": "<info.statement if present>",
  "uri": "https://api.bitrefill.com/x402/connect",
  "version": "1",
  "chainId": "eip155:8453",
  "type": "eip191",
  "nonce": "<info.nonce>",
  "issuedAt": "<info.issuedAt>",
  "expirationTime": "<info.expirationTime if present>",
  "resources": ["https://api.bitrefill.com/x402/connect"],
  "signature": "0x<from get_request_status>"
}
```

## Surface Routing

HTTP routing for paths 1–2 follows [../references/custom-plugins.md](../references/custom-plugins.md): harness HTTP tool if available, else Base MCP `web_request` (allowlisted `api.bitrefill.com`). Chat-only surfaces without POST → paths 1–2 still work via `web_request`.

| Capability | Path 1 (connect→JWT) | Path 2 (pay-per-call) | Path 3 (CLI) | Path 4 (MCP) |
| --- | --- | --- | --- | --- |
| Connect / session | `sign` + `web_request` `/x402/connect` | — | — | — |
| Search / browse | `web_request` + `X-Access-Token` | `web_request` + `x402` per 402 | CLI | MCP tools |
| Product detail | `web_request` + token | `web_request` + `x402` | CLI | MCP |
| Invoice create | `web_request` + token | `web_request` + `x402` | CLI / MCP `buy-products` | MCP |
| Pay invoice | Base MCP `x402` on `/x402/invoice/pay` | Same | Base MCP `x402` on `x402_payment_url` | Same |
| Poll / redeem | `web_request` `/x402/invoice/status` | Same (+ SIWX for codes) | CLI | MCP |
| Order history (wallet) | `web_request` `/x402/my/orders` + token | SIWX per request | CLI `list-orders` (T3 login) | MCP `list-orders` |
| Account login | — | — | CLI `login`/`verify` | MCP OAuth |

Paths 1–2 work on chat-only surfaces (no shell). Path 3 requires shell. Path 4 requires the Bitrefill MCP connector.

## Endpoints

Paths 1–2 use the x402 storefront at `https://api.bitrefill.com` (no `/api` prefix). Every gated response embeds `next_step: { url, body }` chaining search → detail → create → pay → status.

**402 envelope:** `payment-required` header is base64 JSON (`x402Version`, `accepts[]`, `extensions`, …), mirrored into the JSON body for agents that cannot read headers.

**Multi-chain `accepts[]`:** micro-fees and invoice pay offer `exact` USDC on Base (`eip155:8453`), Arbitrum, Polygon, and Solana simultaneously. Amounts are 6-decimal base units (`2000` = $0.002). Base MCP `x402` picks the chain the wallet has funds on.

| Method | Path | Gate | Purpose |
| --- | --- | --- | --- |
| `GET` | `/x402/gift-cards/search` | $0.002 | Search gift cards (`q`, `country`) |
| `GET` | `/x402/esims/search` | $0.002 | Search eSIMs |
| `GET` | `/x402/topups/search` | $0.002 | Search mobile top-ups |
| `GET` | `/x402/products/detail` | $0.001 | Product detail + packages (`slug`) |
| `GET` | `/x402/checkout/info` | $0.001 | Route map / supported networks |
| `POST` | `/x402/invoice/create` | $0.002 | Price-locked quote (1–15 items, `package_value`) |
| `POST` | `/x402/invoice/pay` | Invoice amount | Settle with USDC x402 |
| `GET` | `/x402/invoice/status` | $0.001 or SIWX | Poll; redemption codes for SIWX payer only |
| `POST` | `/x402/connect` | SIWX | Mint session JWT |
| `GET` | `/x402/my/orders` | SIWX or JWT | Wallet-scoped order history |
| `GET` | `/x402/my/esims` | SIWX or JWT | Wallet-scoped eSIM list |

With a valid `X-Access-Token`, the gate hook bypasses micro-fees and SIWX on all gated routes except `/x402/connect` itself (cannot mint a token with a token) and `invoice/pay` (invoice amount never waived).

Paths 3–4 use CLI commands or MCP tools instead of these HTTP routes for catalog/invoice — but invoice payment still lands on `/x402/invoice/pay` via the `x402_payment_url` from `buy-products`.

## Commands

Path 3 only. `npx @bitrefill/cli@latest` or global `bitrefill`. `--json` before subcmd: result stdout, status stderr.

**Identity:** `whoami` · `login --email` · `verify --code [--otp]` · `logout` · `reset` · `manifest` · `llm-context`

```bash
npx @bitrefill/cli@latest --json whoami
npx @bitrefill/cli@latest login --email "user@example.com"
npx @bitrefill/cli@latest verify --code "123456"
```

`whoami --json` → `{ identity, client_id?, email? }`. T3 (`registered`) required for `list-orders` and balance pay.

**Search / buy / track:**

```bash
npx @bitrefill/cli@latest search-products --query "Steam" --country US
npx @bitrefill/cli@latest get-product-details --product_id "steam-usa" --currency USDC
npx @bitrefill/cli@latest buy-products \
  --cart_items '[{"product_id":"steam-usa","package_id":5}]' \
  --payment_method usdc_base \
  --return_payment_link true \
  --email "user@example.com"
npx @bitrefill/cli@latest get-invoice-by-id --invoice_id "UUID"
```

`package_id` only from `get-product-details` response (`package_value`). Invoices ~30 min TTL.

## Orchestration

### Path 1: Connect → browse → buy

1. Base MCP onboarding done.
2. Connect per `## Auth` → store `token`, note `expires_in`.
3. `web_request` `GET /x402/gift-cards/search?q=…&country=US` with `X-Access-Token` (or esims/topups routes).
4. Follow `next_step` → `GET /x402/products/detail` → confirm quote with user.
5. `POST /x402/invoice/create` with cart items (`slug`, `package_value`) + token.
6. `POST /x402/invoice/pay` via Base MCP `x402` (`## Submission`) → user approves.
7. `GET /x402/invoice/status` with token until `complete` → deliver redemption securely (`## Risks`).

### Path 2: Pay-per-call x402

1. Base MCP onboarding done.
2. `web_request` any gated route → 402 → Base MCP `x402` with the request URL (tool handles micro-fee payment) → retry with `payment-signature` header the tool provides.
3. Follow `next_step` chain through detail → create → pay.
4. Invoice pay: Base MCP `x402` on `/x402/invoice/pay` with `{ invoice_id }`.
5. Poll `/x402/invoice/status`; redemption codes require SIWX (same helpers as Path 1, or pay again).

### Path 3: CLI (existing account)

1. `npx @bitrefill/cli@latest` for all Bitrefill ops when shell exists.
2. T3: `login` → `verify` before `list-orders` / balance pay.
3. Search → details → `buy-products` `usdc_base` → Base MCP `x402` on `x402_payment_url` → poll → redeem.

### Path 4: MCP (existing account, shell-less)

1. Bitrefill MCP installed + OAuth ([../references/install.md](../references/install.md)).
2. MCP `search-products` → `product-details` → `buy-products` (explicit user approval).
3. Base MCP `x402` on returned `x402_payment_url` → MCP `get-invoice-by-id` → redemption.

## Submission

Payment submission, not calldata batch. Defer exact parameter names to the live Base MCP tool descriptions.

**Primary — `x402`:** micro-fees (Path 2) and invoice payment (all paths).

```json
{ "url": "https://api.bitrefill.com/x402/invoice/pay" }
```

Body includes `{ "invoice_id": "<uuid>" }` when the tool schema requires it. For micro-fee 402 loops, pass the gated URL that returned 402. → `approvalUrl`, `requestId`. [approval-mode.md](../references/approval-mode.md).

**SIWX connect — `sign`:** Path 1 only. `type: "personal_sign"`, `data: { message: <buildSiweMessage output> }` → approval → `get_request_status` → `signature`.

**Fallback — `send` USDC Base** (when `x402` unavailable):

```json
{
  "chain": "base",
  "to": "<payment_info.address>",
  "amount": "<payment_info.altcoinPrice or quoted USDC>",
  "asset": "USDC"
}
```

**Not Base MCP:** balance+`auto_pay` (T3 CLI/MCP) · lightning/bitcoin/etc · CLI/MCP poll/redeem without x402 HTTP.

## Example Prompts

### $25 Amazon US gift card — connect path (Path 1)

1. Connect per `## Auth` → JWT.
2. Search `gift-cards` US + token → detail → confirm price.
3. `invoice/create` → Base MCP `x402` `invoice/pay` → poll status → deliver code securely.

### Browse with multiple wallets, no session (Path 2)

1. `web_request` search → 402 → Base MCP `x402` pays micro-fee → retry.
2. Repeat per gated step; invoice pay via `x402`.
3. No `X-Access-Token`; each wallet pays its own fees.

### Order history — existing account, shell (Path 3)

1. `whoami` → `login`/`verify` if needed → `list-orders`.

### Buy Steam card — chat client, Bitrefill account (Path 4)

1. Install MCP + OAuth if missing.
2. MCP search → details → user approves → `buy-products` → Base MCP `x402` → poll invoice.

## Risks & Warnings

- **`pii`** — Redemption codes, eSIM QR URLs, PINs, and receipt emails are bearer/cash-like personal data. Never paste codes in group chats, public channels, logs, version control, or voice/TTS output. Only return a code when the user explicitly asks.
- **`irreversible`** — Digital goods deliver instantly and are non-refundable once fulfilled. Always confirm product, denomination, price, and payment method before purchase. Never auto-buy without explicit user approval.
- **Spending cap** — Use a dedicated, low-balance Base Account for USDC payments. Never give the agent seed phrases or high-balance accounts.
- **Invoice expiry** — Invoices expire (~15 min price lock, ~30 min typical). Stale `x402_payment_url` → create a new invoice.
- **Connect token** — `X-Access-Token` is a bearer secret (~2 h TTL). Never log it, commit it, or echo it in chat. Re-connect when expired.
- **EIP-55 checksum** — SIWX rejects lowercase addresses from `get_wallets`. Always run `toChecksumAddress` before `buildSiweMessage`.
- **Package values** — Only from product detail response. Case-sensitive (`"1GB, 7 Days"`, `"1 Month"`). MCP uses `package_value` (not composite `package_id`).
- **CLI session token** — `~/.config/bitrefill-cli/<host>.v1.json` sensitive; `reset` rotates.

## Notes

- USDC Base: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- x402 also accepts USDC on Arbitrum, Polygon, Solana in `accepts[]`; Base MCP `x402` selects by wallet funds
- Country: Alpha-2 uppercase (`US`, `IT`)
- `X-Access-Token` header (not `Authorization: Bearer`) — Base MCP strips `Authorization`
- Fee schedule: search $0.002 · detail/checkout $0.001 · invoice create $0.002 · status $0.001
- Connect-JWT TTL: `X402_CONNECT_TOKEN_TTL_MINUTES` (default 120)
- Docs: [github.com/bitrefill/agents](https://github.com/bitrefill/agents), [docs.bitrefill.com](https://docs.bitrefill.com)
