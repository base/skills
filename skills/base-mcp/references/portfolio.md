# get_portfolio

Returns portfolio value and per-asset breakdown for any wallet address. Onchain data is public — any address can be queried.

## When to use
- "What's my balance?", "How much USDC do I have?", "Show me my portfolio"
- Querying any wallet address's holdings (not just the user's)

## Parameters
- `address` — optional; defaults to session's agent wallet
- `chain` — optional filter: `base` or `ethereum`
- `query` — optional search filter (e.g. "USDC", "ETH")
- `limit` — max assets to return (default 20)
- `offset` — pagination offset
- `includePnl` — include unrealized/realized P&L (default false)

## Key patterns
- For "my balance" → call without address to get the session wallet
- For "balance of 0x..." → pass the address parameter
- Use `query` to filter to a specific token before displaying
- For tokens not found by `get_portfolio`, use `search_tokens` first to resolve the contract address
