---
name: base-mcp
description: >
  Base MCP — gives your AI assistant access to your Base account via the Base MCP server (mcp.base.org).
  Tools: get_wallets (list wallets), get_portfolio (balances, any address), send (ETH/ERC-20 transfers),
  swap (token swaps via Coinbase), sign (EIP-712/personal_sign), send_calls (EIP-5792 batch),
  get_transaction_history (paginated tx history), get_request_status (poll approval), search_tokens (token lookup),
  web_request (fetch whitelisted partner APIs to get calldata, then pass to send_calls — hostname must be in server allowlist).
  Approval mode: send/swap/sign/send_calls require user approval at keys.coinbase.com; response includes approvalUrl + requestId.
  Plugins: Morpho lending protocol available via plugins/morpho.md. Moonwell lending on Base/Optimism via plugins/moonwell.md. Uniswap swaps and LP on Base via plugins/uniswap.md. Avantis perpetual futures on Base via plugins/avantis.md.
---

# Base MCP

The Base MCP server gives your AI assistant access to your Base account on Base.

## Step 1 — Check if the MCP is installed

Before anything else, attempt to call `get_wallets`. If the tool is not available or the call fails with a connection error, the MCP server is not installed. Go to **Step 2**. If it succeeds, skip to **Step 3**.

## Step 2 — Install the MCP server

Tell the user the MCP is not connected and point them to [references/install.md](references/install.md) for step-by-step UI instructions. That file covers Claude Desktop, ChatGPT app, Claude.ai web, Claude Code CLI, and Cursor — with beginner-friendly walkthroughs for each.

Quick reference:
- **Claude Desktop** — Claude menu → Settings → Integrations → Add integration → `https://mcp.base.org`
- **ChatGPT app** — Settings → Connectors → Add connector → MCP server → `https://mcp.base.org`
- **Claude.ai web** — Settings → Integrations → Add integration → `https://mcp.base.org`
- **Claude Code CLI** — `claude mcp add base-account --transport http https://mcp.base.org`

After connecting, the user signs in to authorize via Base account — no Coinbase account required. Once installed, re-run `get_wallets` to confirm the connection, then continue to Step 3.

## Step 3 — Get wallets

Call `get_wallets` immediately at the start of any session involving transactions. This returns:
- The user's Base account address
- Any agent wallets and their delegation status
- `inSession: true/false` — determines whether approval mode is required

**If `inSession: true`** on an agent wallet: transactions can execute without manual approval (M2 mode). Pass `agentWalletId` to send/swap.

**If no wallet is `inSession: true`**: all write tools use approval mode — every transaction goes to keys.coinbase.com for the user to approve.

Load [references/wallets.md](references/wallets.md) for full field reference.

## Tool Routing

Read this table first. For the current task, load ONLY the matching reference file — do not preload all references.

| Task | Tool | Reference |
|------|------|-----------|
| Install the MCP / platform-specific setup | — | [references/install.md](references/install.md) |
| List wallets / check session status | `get_wallets` | [references/wallets.md](references/wallets.md) |
| Check balance / portfolio / token lookup | `get_portfolio`, `search_tokens` | [references/portfolio.md](references/portfolio.md) |
| Send ETH or ERC-20 | `send` | [references/send.md](references/send.md) |
| Swap tokens | `swap` | [references/swap.md](references/swap.md) |
| Sign a message or typed data | `sign` | [references/sign.md](references/sign.md) |
| Batch contract calls | `send_calls` | [references/batch-calls.md](references/batch-calls.md) |
| View transaction history | `get_transaction_history` | [references/history.md](references/history.md) |
| Check pending approval status | `get_request_status` | [references/approval-mode.md](references/approval-mode.md) |
| Resolve token by symbol | `search_tokens` | [references/tokens.md](references/tokens.md) |
| Fetch protocol API calldata (Moonwell, etc.) | `web_request` | [references/web-request.md](references/web-request.md) |

## Approval Mode

All write tools (send, swap, sign, send_calls) return an `approvalUrl` and `requestId`. Direct the user to open the URL to approve, then call `get_request_status` to confirm completion. Never report success before `get_request_status` returns confirmed.

Load [references/approval-mode.md](references/approval-mode.md) for full details.

## Plugins

Additional protocol capabilities — no extra MCP server needed for Moonwell (uses `web_request`); Morpho requires its own MCP server.

| Plugin | Protocol | Reference |
|--------|---------|-----------|
| Morpho | Lending / vaults on Base | [plugins/morpho.md](plugins/morpho.md) |
| Moonwell | Lending / borrowing on Base and Optimism | [plugins/moonwell.md](plugins/moonwell.md) |
| Uniswap | Token swaps and LP positions on Base | [plugins/uniswap.md](plugins/uniswap.md) |
| Avantis | Perpetual futures trading on Base | [plugins/avantis.md](plugins/avantis.md) |

## Installation

```bash
npx skills add base/skills --skill base-mcp
```
