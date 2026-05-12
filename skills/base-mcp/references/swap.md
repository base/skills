# swap

Swap between two tokens via the Coinbase swap service. Only supported on mainnet chains (not testnets). Operates in approval mode.

## When to use
- "Swap X for Y", "Buy X ETH with USDC", "Trade X to Y"

## Required parameters
- `fromAsset` — symbol (ETH, USDC) or contract address
- `toAsset` — symbol or contract address
- `amount` — human-readable decimal amount of `fromAsset`
- `chain` — target chain (e.g. `base`); testnets not supported

## Approval mode flow
Same as send: get `approvalUrl` + `requestId`, direct user to URL, poll `get_request_status`.

## Key patterns
- For unknown tokens, call `search_tokens` first to resolve contract address
- Testnets are not supported — if user requests a testnet swap, explain this
- Never report success before `get_request_status` confirms completion
