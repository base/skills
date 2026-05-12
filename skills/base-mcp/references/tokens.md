# search_tokens

Search for token metadata by symbol or name. Returns contract address, decimals, and chain info needed to use a token with send/swap.

## When to use
- Before calling `send` with a non-standard token (not ETH or USDC) — need contract address + decimals
- User references a token by name/symbol and you need to resolve it
- Verifying a token exists on a specific chain

## Parameters
- `query` — required; token symbol or name (e.g. `USDC`, `uniswap`, `WETH`)
- `chain` — optional; `base` or `base-sepolia`

## Return fields (per result)
- `name`, `symbol` — display info
- `address` — ERC-20 contract address
- `decimals` — needed when passing a contract address to send
- `imageUrl` — token logo
- `chain` — which chain this token is on

## Key patterns
- Always pass the returned `address` AND `decimals` to `send` when using a contract address
- For common tokens (ETH, USDC), you can pass the symbol directly to send/swap — no lookup needed
- If multiple results, prefer the one on `base` mainnet unless user specified otherwise
