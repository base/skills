# send_calls

Submit a batch of EIP-5792 wallet_sendCalls for user approval. Use for arbitrary contract interactions, multi-step transactions, or batched operations.

## When to use
- Protocol interactions not covered by send/swap (e.g. DeFi, NFT mints, approvals)
- Batching multiple operations into one user approval
- Morpho plugin: Morpho prepares `prepare_*` calls → pass the raw calls array to `send_calls`

## Required parameters
- `chainId` — hex chain ID with 0x prefix (`0x2105` for Base mainnet, `0x14a34` for Base Sepolia)
- `calls` — array of call objects, each with:
  - `to` — target address (0x-prefixed, required)
  - `value` — hex ETH in wei (e.g. `0x0`), optional
  - `data` — calldata hex (e.g. `0xa9059cbb...`), optional

## Approval mode flow
Same as send: get `approvalUrl` + `requestId`, direct user to URL, poll `get_request_status`.

## Common use case with Morpho plugin
1. Morpho `prepare_deposit` (or other prepare_* tool) returns `calls` array
2. Pass that array directly to `send_calls` with the appropriate `chainId`
3. Direct user to `approvalUrl` for signing
