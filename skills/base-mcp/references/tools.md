# Native Tools

All tools below are built and maintained by the Base core team via the Base MCP server.

---

## get_wallets

Returns all wallets in the user's wallet group.

**Parameters:** none

**Return fields (per wallet):** `id`, `type` (`base-account` or `agent-wallet`), `address`

**Key patterns:**
- Call at session start to confirm the MCP is connected and to retrieve the user's address(es)
- All write tools (send, swap, sign, send_calls) operate in approval mode — see [approval-mode.md](approval-mode.md)

---

## get_portfolio

Returns portfolio value and per-asset breakdown for any wallet address. Onchain data is public — any address can be queried.

**Parameters:**
- `address` — optional; defaults to session wallet
- `chain` — optional: `base` or `ethereum`
- `query` — optional token filter (e.g. `USDC`)
- `limit` / `offset` — pagination
- `includePnl` — include unrealized/realized P&L (default false)

**Key patterns:**
- Omit `address` to query the session wallet; pass it to query any other address
- Use `query` to filter to a specific token before displaying
- If a token isn't found, call `search_tokens` first to resolve its contract address

---

## search_tokens

Search for token metadata by symbol or name.

**Parameters:**
- `query` — required; symbol or name (e.g. `USDC`, `WETH`)
- `chain` — optional: `base` or `base-sepolia`

**Return fields (per result):** `name`, `symbol`, `address` (contract), `decimals`, `chain`

**Key patterns:**
- Always use the returned `address` AND `decimals` together when passing a contract address to `send`
- For ETH and USDC, pass the symbol directly to `send`/`swap` — no lookup needed
- If multiple results, prefer the `base` mainnet result unless the user specified otherwise

---

## send

Send native ETH or any ERC-20 token. Operates in approval mode.

**Required parameters:**
- `recipient` — 0x address, ENS name, basename (e.g. `vitalik.eth`), cb.id, or username
- `amount` — human-readable decimal (e.g. `1.5`)
- `asset` — symbol (`ETH`, `USDC`) or ERC-20 contract address
- `chain` — `base` or `base-sepolia`

**Optional parameters:**
- `decimals` — required when `asset` is a contract address (0–18)

**Key patterns:**
- For non-standard tokens, call `search_tokens` first to get `address` + `decimals`
- Basenames and ENS names resolve automatically — no need to look them up first
- Never report success before `get_request_status` confirms completion

---

## swap

Swap between two tokens via the Coinbase swap service. Mainnet only — testnets not supported. Operates in approval mode.

**Required parameters:**
- `fromAsset` — symbol or contract address
- `toAsset` — symbol or contract address
- `amount` — human-readable decimal amount of `fromAsset`
- `chain` — target chain (e.g. `base`); testnets are not supported

**Key patterns:**
- For unknown tokens, call `search_tokens` first to resolve the contract address
- If user requests a testnet swap, explain it is not supported
- Never report success before `get_request_status` confirms completion

---

## sign

Request a user-approved signature. Supports EIP-712 typed data and personal_sign. Operates in approval mode.

**Required parameters:**
- `type` — `0x01` for EIP-712 typed data, `0x45` for personal_sign
- `data`:
  - For `0x01`: EIP-712 TypedData object with `primaryType`, `types`, `domain`, `message`
  - For `0x45`: object with a `message` string field

**Key patterns:**
- Use `0x45` for simple text messages (SIWE, auth challenges)
- Use `0x01` for structured typed data (permit signatures, EIP-712 auth)
- Poll `get_request_status` after approval to retrieve the signature value

---

## send_calls

Submit a batch of EIP-5792 calls. See [references/batch-calls.md](batch-calls.md) for full details and the batching-preferred rule.

**Required parameters:**
- `chainId` — hex chain ID with 0x prefix (`0x2105` for Base mainnet, `0x14a34` for Base Sepolia)
- `calls` — array of `{ to, value, data }` objects

---

## get_transaction_history

Returns paginated transaction history for any wallet address in reverse chronological order.

**Parameters:**
- `address` — optional; defaults to session wallet
- `chain` — optional: `base` or `ethereum`
- `asset` — optional symbol filter (e.g. `USDC`)
- `limit` — 1–200, defaults to 50
- `cursor` — pagination cursor from previous response's `nextCursor`

**Key patterns:**
- Date range filtering is not supported — paginate to find transactions in a specific period
- Use `asset` to narrow results to a specific token
- Continue paginating while `hasMore` is true

---

## get_request_status

Poll the status of a pending approval request.

**Parameters:**
- `requestId` — required; from the write tool response

**Key patterns:**
- Call once after the user confirms they approved — do not poll in a tight loop
- Never report a write operation as successful before this returns a confirmed status
- See [references/approval-mode.md](approval-mode.md) for the full approval flow

---

## web_request

Make an HTTP request to a whitelisted partner API. The hostname must be in the MCP server's allowlist — requests to unlisted domains are rejected. This tool exists because AI assistants in most harnesses cannot fetch arbitrary URLs; `web_request` provides controlled access to trusted protocol APIs so the agent can retrieve calldata and pass it to `send_calls`.

**Parameters:**
- `url` — full HTTPS URL; hostname must be allowlisted (required)
- `method` — `GET` or `POST` (required)
- `headers` — optional key/value map. Prohibited: `Authorization`, `Cookie`, `Host`, `X-Forwarded-*`
- `body` — JSON object for POST requests; ignored for GET

**Calldata pattern:**
```
web_request → { data: { transactions: [ { to, data, value, chainId } ] } }
  ↓ map transactions[] to send_calls calls[]
send_calls → approvalUrl + requestId
  ↓ user approves
get_request_status → confirmed
```

Map each `transactions[i]` directly: `to → calls[i].to`, `data → calls[i].data`, `value → calls[i].value`. Pass `chainId` from any `transactions[i].chainId`.

**Key patterns:**
- If a request fails with a domain rejection, the hostname is not allowlisted — inform the user, do not retry
- Currently allowlisted partner protocols are documented in the plugin files under `plugins/`
- Always prefer `send_calls` batching when the response contains multiple transactions — see [references/batch-calls.md](batch-calls.md)

**Custom (non-native) plugins — domain not allowlisted:**

When a user asks you to interact with a protocol that is not one of the four native plugins (Morpho, Moonwell, Uniswap, Avantis) and `web_request` rejects the domain:

1. **Construct the calldata URL as a GET endpoint** — most protocol APIs expose a GET endpoint that encodes all parameters in the query string (address, amount, slippage, etc.). Build the full URL with all required parameters.
2. **Try to fetch it directly** — attempt to retrieve the URL using whatever HTTP fetch capability is available to you in the current harness.
3. **If you cannot fetch it** (e.g., the harness restricts fetching to URLs explicitly sent by the user in the chat): do NOT silently fail or retry with `web_request`. Instead, tell the user:
   - What the constructed URL is (show the full URL with parameters)
   - That you need them to paste it into the chat so you can read the response
   - Example message: _"I can't fetch external URLs directly in this environment. Please open this URL in your browser or paste it into the chat: `<url>`"_
4. Once the user sends the response (JSON or raw text), parse it and continue the normal `send_calls` flow.

This fallback applies **only to custom protocols**. Native plugins (Morpho, Moonwell, Uniswap, Avantis) are always allowlisted — use `web_request` for them without this fallback.
