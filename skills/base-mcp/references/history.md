# get_transaction_history

Returns paginated transaction history for any wallet address in reverse chronological order. Onchain data is public — any address can be queried.

## When to use
- "Show my recent transactions", "What did I last do?", "Show my USDC sends"
- Investigating past activity for any address

## Parameters
- `address` — optional; defaults to session's agent wallet
- `chain` — optional: `base` or `ethereum` (defaults to base)
- `asset` — optional symbol filter (e.g. `USDC`, `ETH`)
- `limit` — 1–200, defaults to 50
- `cursor` — pagination cursor from previous response's `nextCursor`

## Return fields (per transaction)
- Transfer details, type classification, fees, USD values at time of transaction
- `hasMore` — whether more pages exist; continue paginating while `true`

## Key patterns
- Date range filtering is not supported — paginate to find transactions in a specific period
- Use `asset` filter to narrow results to a specific token
