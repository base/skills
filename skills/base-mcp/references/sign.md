# sign

Request a user-approved signature from the Base Account. Supports EIP-712 typed data and personal_sign. Operates in approval mode.

## When to use
- "Sign this message", "Sign this typed data", agent needs a signature for authentication

## Required parameters
- `type` — `0x01` for EIP-712 typed data, `0x45` for personal_sign
- `data`:
  - For `0x01`: EIP-712 TypedData object with `primaryType`, `types`, `domain`, `message`
  - For `0x45`: object with a `message` string field

## Approval mode flow
1. Call `sign` → get `approvalUrl` + `requestId`
2. Direct user to `approvalUrl`
3. Poll `get_request_status` to retrieve the signature after approval

## Key patterns
- Use `0x45` for simple text messages (e.g. SIWE, auth challenges)
- Use `0x01` for structured typed data (e.g. permit signatures, EIP-712 auth)
