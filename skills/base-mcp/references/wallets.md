# get_wallets

Returns all wallets in the user's wallet group: the Base Account (primary) plus any agent wallets.

## When to use
- User asks "show me my wallets", "what wallets do I have", "which wallet is active"
- You need to know if an agent wallet is authorized before a transactional call

## Parameters
None.

## Return fields (per wallet)
- `id` — wallet ID
- `type` — `base-account` or `agent-wallet`
- `address` — 0x address
- `inSession` — boolean; only `true` wallets can be used with transactional tools
- `delegationStatus` — whether the agent wallet has delegated authority from the Base Account
- `spendPolicy` — summary of spend limits (agent wallets only)

## Key patterns
- If no wallet is `inSession: true`, all transactional tools will use approval mode (keys.coinbase.com)
- Agent wallets with `inSession: true` can transact without manual approval (M2 mode)
- Always check `inSession` before deciding whether approval will be required
