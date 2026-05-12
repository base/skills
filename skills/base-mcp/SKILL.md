---
name: base-mcp
description: >
  Base Account MCP — gives your AI assistant a wallet via the Base Account MCP server (mcp.base.org).
  Tools: get_wallets (list wallets), get_portfolio (balances, any address), send (ETH/ERC-20 transfers),
  swap (token swaps via Coinbase), sign (EIP-712/personal_sign), send_calls (EIP-5792 batch),
  get_transaction_history (paginated tx history), get_request_status (poll approval), search_tokens (token lookup).
  Approval mode: send/swap/sign/send_calls require user approval at keys.coinbase.com; response includes approvalUrl + requestId.
  Plugins: Morpho lending protocol available via plugins/morpho.md.
---

# Base Account MCP

The Base Account MCP server gives your AI assistant direct access to the user's Base Account (smart wallet) on Base. Once connected at mcp.base.org, 9 tools are available with no additional setup.

## Connection

Server URL: `https://mcp.base.org`
Auth: OAuth via Coinbase Base Account (user must have a Coinbase account)

## Tool Routing

Read this table first. For the current task, load ONLY the matching reference file — do not preload all references.

| Task | Tool | Reference |
|------|------|-----------|
| List wallets / check delegation | `get_wallets` | [references/wallets.md](references/wallets.md) |
| Check balance / portfolio / token lookup | `get_portfolio`, `search_tokens` | [references/portfolio.md](references/portfolio.md) |
| Send ETH or ERC-20 | `send` | [references/send.md](references/send.md) |
| Swap tokens | `swap` | [references/swap.md](references/swap.md) |
| Sign a message or typed data | `sign` | [references/sign.md](references/sign.md) |
| Batch contract calls | `send_calls` | [references/batch-calls.md](references/batch-calls.md) |
| View transaction history | `get_transaction_history` | [references/history.md](references/history.md) |
| Check pending approval status | `get_request_status` | [references/approval-mode.md](references/approval-mode.md) |
| Resolve token by symbol | `search_tokens` | [references/tokens.md](references/tokens.md) |

## Approval Mode

All write tools (send, swap, sign, send_calls) operate in approval mode: the transaction is submitted to keys.coinbase.com and the response includes an `approvalUrl` the user must open and a `requestId` for polling. After the user approves, call `get_request_status` with the `requestId` to confirm completion. Load [references/approval-mode.md](references/approval-mode.md) for full details.

## Plugins

Additional protocol capabilities via plugin MCPs:

| Plugin | Protocol | Reference |
|--------|---------|-----------|
| Morpho | Lending / vaults on Base | [plugins/morpho.md](plugins/morpho.md) |

## Installation

```bash
npx skills add base/base-skills --skill base-mcp
```
