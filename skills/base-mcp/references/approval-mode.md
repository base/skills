# Approval Mode

All write tools (send, swap, sign, send_calls) operate in approval mode. The user must manually approve every transaction at keys.coinbase.com.

## Flow

1. **Call the write tool** (send, swap, sign, or send_calls)
2. **Response includes**:
   - `approvalUrl` — URL the user must open to approve
   - `requestId` — ID to poll for completion
3. **Direct the user** to open `approvalUrl` immediately. Say: "Please open this link to approve the transaction: [approvalUrl]"
4. **After user confirms they approved**, call `get_request_status` with the `requestId`
5. **Only report success** when `get_request_status` returns a completed/confirmed status

## get_request_status parameters
- `requestId` — the ID from the write tool response (required)

## Common mistakes
- Do NOT report success before calling `get_request_status` — the user may not have approved yet
- Do NOT skip showing the `approvalUrl` — the transaction cannot complete without user action
- Do NOT poll `get_request_status` in a tight loop — call once after user confirms they approved

## When approval is NOT needed
Agent wallets marked `inSession: true` (from `get_wallets`) can transact without approval in M2 mode. The `agentWalletId` parameter on send/swap enables this.

