# Morpho Plugin

Morpho is a lending protocol on Base. The Morpho MCP server prepares lending operations (deposit, borrow, withdraw, repay, supply collateral) which are then executed via Base MCP's `send_calls`.

## MCP Server

URL: `https://mcp.morpho.org/`

## Installation (alongside Base MCP)

Add both servers to your MCP config:

```json
{
  "mcpServers": {
    "base-account": { "url": "https://mcp.base.org" },
    "morpho": { "url": "https://mcp.morpho.org/" }
  }
}
```

Claude Code: `claude mcp add morpho --transport http https://mcp.morpho.org/`

## Morpho Tools (17 total)

### Read
- `morpho_health_check` — server connectivity
- `morpho_get_supported_chains` — supported chains
- `morpho_query_vaults` — list vaults with filtering/sorting
- `morpho_get_vault` — details for a specific vault
- `morpho_query_markets` — list markets with filtering
- `morpho_get_market` — details for a specific market
- `morpho_get_positions` — all positions for an address (all vaults + markets)
- `morpho_get_token_balance` — token balance and approval state

### Write (prepare_ returns unsigned calls for send_calls)
- `morpho_prepare_deposit` — prepare vault deposit with approvals
- `morpho_prepare_withdraw` — prepare vault withdrawal (supports max)
- `morpho_prepare_supply` — prepare market supply with approvals
- `morpho_prepare_borrow` — prepare market borrow with health check
- `morpho_prepare_repay` — prepare market repay (supports max)
- `morpho_prepare_supply_collateral` — supply collateral to market
- `morpho_prepare_withdraw_collateral` — withdraw collateral with health check

### Simulate
- `morpho_simulate_transactions` — simulate with post-state analysis

## Orchestration Pattern

Morpho `prepare_*` tools return unsigned call data. Pass the result to Base MCP's `send_calls` to execute.

```
morpho_prepare_deposit(vaultAddress, amount) → { calls: [...], chainId }
↓
send_calls(chainId, calls) → approvalUrl + requestId
↓
User approves at keys.coinbase.com
↓
get_request_status(requestId) → confirmed
```

## Example Prompts

```
Find the best USDC vault on Base by APY and deposit 100 USDC
```
1. `morpho_query_vaults` (filter by USDC, sort by APY)
2. `morpho_prepare_deposit` (selected vault, 100 USDC)
3. `send_calls` (chainId + calls from prepare_deposit)
4. Direct user to approvalUrl, poll get_request_status

```
Show all my Morpho positions on Base
```
1. `get_wallets` (get user's address)
2. `morpho_get_positions` (user's address)

```
Check if my Morpho borrow position is healthy
```
1. `get_wallets` (get address)
2. `morpho_get_positions` (address)
3. Report health factor from position data

## Important Notes

- Morpho `prepare_*` tools simulate before returning — review simulation output before calling `send_calls`
- Always use `morpho_simulate_transactions` for novel or large operations
- Morpho operates on Base mainnet; check `morpho_get_supported_chains` for current list
