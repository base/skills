# send

Send native ETH or any ERC-20 token to an address. Operates in approval mode: the response includes an `approvalUrl` and `requestId`.

## When to use
- "Send X to Y", "Transfer X USDC to...", "Pay X ETH to..."

## Required parameters
- `recipient` — 0x address, ENS name, basename (e.g. `vitalik.eth`), cb.id name, or wallet username
- `amount` — human-readable decimal (e.g. "1.5")
- `asset` — symbol (`ETH`, `USDC`) or ERC-20 contract address
- `chain` — `base` or `base-sepolia`

## Optional parameters
- `decimals` — required when `asset` is a contract address (not a symbol)
- `agentWalletId` — scope to a specific agent wallet (M2 mode only)

## Approval mode flow
1. Call `send` → get `approvalUrl` + `requestId`
2. Show the user: "Please approve this transaction: [approvalUrl]"
3. After user confirms, call `get_request_status` with `requestId`
4. Only report success when status is confirmed

## Key patterns
- For unknown tokens, call `search_tokens` first to get the contract address and decimals
- Never report success before `get_request_status` confirms completion
- Use basenames/ENS for recipient when provided — no need to resolve first
