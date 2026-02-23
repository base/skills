# Prolinks (Shareable Payment Links)

## Table of Contents

- [Overview](#overview)
- [encodeProlink](#encodeprolink)
- [decodeProlink](#decodeprolink)
- [createProlinkUrl](#createprolinkurl)
- [Common Patterns](#common-patterns)

## Overview

Prolinks encode transaction requests (JSON-RPC) into compressed, URL-safe strings that can be shared as links. When a user opens a prolink URL, their Base Account app decodes and executes the request.

Use cases: shareable payment requests, pre-filled transaction links, QR codes for onchain actions.

The encoding is optimized per method type (`wallet_sendCalls`, `wallet_sign`, generic JSON-RPC) and uses gzip compression for payloads >= 1KB (50-80% size reduction).

## encodeProlink

Encodes a JSON-RPC request into a compressed, base64url-encoded prolink payload.

```typescript
import { encodeProlink } from '@base-org/account';

const prolink = await encodeProlink({
  method: 'wallet_sendCalls',
  params: {
    version: '2.0.0',
    chainId: '0x2105',
    calls: [{
      to: '0xUSDCAddress',
      data: '0xtransferCalldata',
      value: '0x0',
    }],
  },
});
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `method` | `string` | Yes | JSON-RPC method (`wallet_sendCalls`, `wallet_sign`, or any) |
| `params` | `unknown` | Yes | Method parameters |
| `chainId` | `number` | No | Required for generic methods; auto-extracted for `wallet_sendCalls`/`wallet_sign` |
| `capabilities` | `Record<string, unknown>` | No | Wallet capabilities (e.g., `dataCallback`) |

Returns: `Promise<string>` — base64url-encoded prolink payload.

### Examples

**ERC-20 Transfer (USDC):**

```typescript
const prolink = await encodeProlink({
  method: 'wallet_sendCalls',
  params: {
    version: '2.0.0',
    chainId: '0x2105',
    calls: [{
      to: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913', // USDC on Base
      data: '0xa9059cbb000000000000000000000000RECIPIENT0000000000000000000000000000000000000000000000000000000000989680', // transfer(address,uint256)
      value: '0x0',
    }],
  },
});
```

**With Capabilities (dataCallback):**

```typescript
const prolink = await encodeProlink({
  method: 'wallet_sendCalls',
  params: { /* ... */ },
  capabilities: {
    dataCallback: {
      callbackURL: 'https://your-api.com/callback',
      events: ['initiated', 'postSign'],
    },
  },
});
```

**Batch Calls (approve + swap):**

```typescript
const prolink = await encodeProlink({
  method: 'wallet_sendCalls',
  params: {
    version: '2.0.0',
    chainId: '0x2105',
    calls: [
      { to: '0xToken', data: '0xapproveData', value: '0x0' },
      { to: '0xDex', data: '0xswapData', value: '0x0' },
    ],
  },
});
```

## decodeProlink

Decodes a prolink payload back into a JSON-RPC request.

```typescript
import { decodeProlink } from '@base-org/account';

const decoded = await decodeProlink(payload);
// decoded.method → 'wallet_sendCalls'
// decoded.params → { version, chainId, calls }
// decoded.chainId → number | undefined
// decoded.capabilities → Record<string, unknown> | undefined
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `payload` | `string` | Yes | Base64url-encoded prolink payload |

Returns `ProlinkDecoded`:

| Field | Type | Description |
|-------|------|-------------|
| `method` | `string` | JSON-RPC method name |
| `params` | `unknown` | Method parameters |
| `chainId` | `number \| undefined` | Target chain ID |
| `capabilities` | `Record<string, unknown> \| undefined` | Wallet capabilities |

### Validation Before Execution

Always validate decoded prolinks before executing:

```typescript
const decoded = await decodeProlink(payload);

if (decoded.chainId !== 8453) throw new Error('Wrong chain');
if (decoded.method !== 'wallet_sendCalls') throw new Error('Unexpected method');

const { calls } = decoded.params;
const allowedContracts = ['0xUSDC...', '0xDex...'];
for (const call of calls) {
  if (!allowedContracts.includes(call.to)) {
    throw new Error(`Untrusted contract: ${call.to}`);
  }
}

await provider.request({ method: decoded.method, params: [decoded.params] });
```

## createProlinkUrl

Creates a complete URL with the prolink as a query parameter.

```typescript
import { createProlinkUrl } from '@base-org/account';

const url = createProlinkUrl(prolink, 'https://yourapp.com/pay');
// https://yourapp.com/pay?prolink=<encoded-payload>
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prolink` | `string` | Yes | Base64url-encoded prolink from `encodeProlink` |
| `url` | `string` | Yes | Base URL (default: `https://base.app/base-pay`) |
| `additionalQueryParams` | `Record<string, string>` | No | Extra query parameters |

Returns: Complete URL string.

## Common Patterns

### Payment Request Link

```typescript
const prolink = await encodeProlink({
  method: 'wallet_sendCalls',
  params: {
    version: '2.0.0',
    chainId: '0x2105',
    calls: [{ to: recipientAddress, data: transferCalldata, value: '0x0' }],
  },
});
const paymentUrl = createProlinkUrl(prolink);
// Share this URL or render as QR code
```

### Extract and Display Transaction Preview

```typescript
const decoded = await decodeProlink(payload);
const { calls } = decoded.params;

const preview = calls.map((call, i) =>
  `Call ${i + 1}: to=${call.to}, value=${call.value}`
).join('\n');
```
