---
name: base-mcp
description: >
  Base MCP — gives your AI assistant access to your Base account via the Base MCP server (mcp.base.org).
  Native tools (built and maintained by the Base core team): get_wallets, get_portfolio, send, swap, sign,
  send_calls, get_transaction_history, get_request_status, search_tokens, web_request.
  Approval mode: send/swap/sign/send_calls require user approval at keys.coinbase.com; response includes approvalUrl + requestId.
  Plugins (external partners): Morpho lending, Moonwell lending, Uniswap swaps/LP, Avantis perpetual futures — all on Base.
---

# Base MCP

## Detection

Call `get_wallets` immediately on session start.

- **Tool unavailable or connection error** → the MCP server is not installed. Tell the user clearly, direct them to install it at https://docs.base.org/ai-agents/quickstart, and stop. Do not attempt to offer any functionality without the MCP.
- **Call succeeds** → MCP is connected. Load `references/tone.md`, then continue to Onboarding.

## Tone

Load [references/tone.md](references/tone.md) at session start. Its rules apply for the entire conversation.

## Onboarding

Runs once per session after MCP is confirmed connected.

1. **Show wallet status** — the `get_wallets` call from Detection already ran; present the results:
   - User's Base account address(es)
   - If any wallet has `inSession: true`: confirm M2 mode is active — write operations run without manual approval for that wallet.
   - If no wallet has `inSession: true`: note that all write operations will require approval at keys.coinbase.com.

2. **Show capability summary** — present what is available:

   **Native tools** (built and maintained by the Base core team):
   - Send ETH or any token
   - Swap tokens via Coinbase
   - Sign messages and typed data
   - Batch contract calls
   - View portfolio and balances
   - View transaction history
   - Search tokens by symbol or name

   **Plugins** (APIs provided by external partners, subject to their own terms):
   - Morpho — lending and vaults on Base
   - Moonwell — lending and borrowing on Base and Optimism
   - Uniswap — token swaps and LP positions on Base
   - Avantis — perpetual futures trading on Base

3. **Show this disclaimer** — display it verbatim before proceeding:

   > By using the Base Account MCP, you agree to the Base Account and Base App Terms of Service. Plugins available in the Base repo are authored by Base, not by the third-party protocols they reference.

## Tools

Load [references/tools.md](references/tools.md) for the full tool catalogue. For the current task, load ONLY the relevant section — do not preload everything.

| Task | Tool | Reference |
|------|------|-----------|
| List wallets / check session status | `get_wallets` | [references/tools.md](references/tools.md) |
| Balance / portfolio / token lookup | `get_portfolio`, `search_tokens` | [references/tools.md](references/tools.md) |
| Send ETH or ERC-20 | `send` | [references/tools.md](references/tools.md) |
| Swap tokens | `swap` | [references/tools.md](references/tools.md) |
| Sign message or typed data | `sign` | [references/tools.md](references/tools.md) |
| Batch contract calls | `send_calls` | [references/batch-calls.md](references/batch-calls.md) |
| Transaction history | `get_transaction_history` | [references/tools.md](references/tools.md) |
| Poll approval status | `get_request_status` | [references/approval-mode.md](references/approval-mode.md) |
| Fetch protocol calldata | `web_request` | [references/tools.md](references/tools.md) |
| Platform install | — | [references/install.md](references/install.md) |
| Tone and language rules | — | [references/tone.md](references/tone.md) |

## Plugins

| Plugin | Protocol | Operated by | Reference |
|--------|----------|-------------|-----------|
| Morpho | Lending / vaults on Base | Morpho Labs | [plugins/morpho.md](plugins/morpho.md) |
| Moonwell | Lending on Base and Optimism | Moonwell team | [plugins/moonwell.md](plugins/moonwell.md) |
| Uniswap | Swaps and LP on Base | Uniswap Labs | [plugins/uniswap.md](plugins/uniswap.md) |
| Avantis | Perpetual futures on Base | Avantis team | [plugins/avantis.md](plugins/avantis.md) |

## Installation

```bash
npx skills add base/skills --skill base-mcp
```
