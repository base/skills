# web_request

Make an HTTP request to a whitelisted partner API. The hostname must be in the MCP server's configured allowlist — requests to unlisted domains are rejected outright. This is why the tool exists: AI assistants on Claude Desktop, ChatGPT, and similar environments can't autonomously fetch arbitrary URLs, but `web_request` gives controlled access to trusted protocol APIs so the agent can retrieve calldata and pass it to `send_calls`.

## When to use

- Fetching unsigned transaction calldata from a partner protocol API (e.g. Moonwell `/prepare/supply`) before passing it to `send_calls`
- Reading on-chain data from a whitelisted protocol HTTP API (positions, balances, rates, health factor)

## Parameters

- `url` — full HTTPS URL; hostname must be in the allowlist (required)
- `method` — `GET` or `POST` (required)
- `headers` — optional key/value map of custom headers. **Prohibited:** `Authorization`, `Cookie`, `Host`, `X-Forwarded-*`
- `body` — JSON object for POST requests; ignored for GET

## Calldata pattern

```
web_request(GET or POST to whitelisted /prepare/* endpoint)
  → { data: { transactions: [ { to, data, value, chainId }, ... ] } }
      ↓
send_calls(chainId, calls mapped from transactions[])
  → approvalUrl + requestId
      ↓
User approves at keys.coinbase.com
      ↓
get_request_status(requestId) → confirmed
```

## Mapping response transactions to send_calls

Protocol `/prepare/*` responses return an ordered `transactions[]` array. Map each item directly:

```
transactions[i].to    → calls[i].to
transactions[i].data  → calls[i].data
transactions[i].value → calls[i].value   (0x-prefixed hex)
```

Pass the `chainId` from any `transactions[i].chainId` to `send_calls`. Execute all calls in order — steps like `approve` and `enter-market` must confirm before later steps succeed.

## Allowlist

The allowlist is configured server-side on the MCP. If a request fails with a domain rejection error, the hostname is not whitelisted — inform the user rather than retrying. Currently whitelisted partner protocols are documented in the plugin references (e.g. `plugins/moonwell.md`).
