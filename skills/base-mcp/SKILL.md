---
name: base-mcp
description: >
  Base Account MCP — gives your AI assistant a wallet via the Base Account MCP server (mcp.base.org).
  Tools: get_wallets (list wallets), get_portfolio (balances, any address), send (ETH/ERC-20 transfers),
  swap (token swaps via Coinbase), sign (EIP-712/personal_sign), send_calls (EIP-5792 batch),
  get_transaction_history (paginated tx history), get_request_status (poll approval), search_tokens (token lookup),
  web_request (fetch whitelisted partner APIs to get calldata, then pass to send_calls — hostname must be in server allowlist).
  Approval mode: send/swap/sign/send_calls require user approval at keys.coinbase.com; response includes approvalUrl + requestId.
  Plugins: Morpho lending protocol available via plugins/morpho.md. Moonwell lending on Base/Optimism via plugins/moonwell.md.
---

# Base Account MCP

The Base Account MCP server gives your AI assistant direct access to the user's Base Account (smart wallet) on Base.

## Step 1 — Check if the MCP is installed

Before anything else, attempt to call `get_wallets`. If the tool is not available or the call fails with a connection error, the MCP server is not installed. Go to **Step 2**. If it succeeds, skip to **Step 3**.

## Step 2 — Install the MCP server

Tell the user the MCP is not connected and offer the right install command for their environment:

**Claude Code (CLI)**
```bash
claude mcp add base-account --transport http https://mcp.base.org
```

**Claude Desktop** — add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "base-account": { "url": "https://mcp.base.org" }
  }
}
```

**Other MCP-compatible clients** — server URL: `https://mcp.base.org`

After adding the server, the client will open an OAuth flow. The user authorizes via Base Account at mcp.base.org — no Coinbase account required.

Once installed, re-run `get_wallets` to confirm the connection, then continue to Step 3.

## Step 3 — Get wallets

Call `get_wallets` immediately at the start of any session involving transactions. This returns:
- The user's Base Account address
- Any agent wallets and their delegation status
- `inSession: true/false` — determines whether approval mode is required

**If `inSession: true`** on an agent wallet: transactions can execute without manual approval (M2 mode). Pass `agentWalletId` to send/swap.

**If no wallet is `inSession: true`**: all write tools use approval mode — every transaction goes to keys.coinbase.com for the user to approve.

Load [references/wallets.md](references/wallets.md) for full field reference.

## Tool Routing

Read this table first. For the current task, load ONLY the matching reference file — do not preload all references.

| Task | Tool | Reference |
|------|------|-----------|
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

## Installation

```bash
npx skills add base/skills --skill base-mcp
```
