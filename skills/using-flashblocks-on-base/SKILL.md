---
name: using-flashblocks-on-base
description: Explains how to integrate Flashblocks on Base for 200ms preconfirmations. Use when asked about Flashblocks, fast transaction confirmations, preconfirmations, real-time block streaming, pending block tags, or reducing transaction latency on Base. Covers phrases like "flashblocks", "preconfirmation", "200ms blocks", "pending tag", "flashblocks RPC", "flashblocks websocket", "baseSepoliaPreconf", or "fast transactions on Base".
---

# Using Flashblocks on Base

## What are Flashblocks?

Flashblocks are sub-blocks streamed every 200ms — 10x faster than Base's standard 2-second block time. They provide preconfirmations: fast signals that a transaction will be included before the next full block is sealed. Developed with Flashbots, Flashblocks launched on Base Mainnet in July 2025.

## Public Endpoints

### Mainnet
| Type | Endpoint |
|------|----------|
| RPC | `https://mainnet-preconf.base.org` |
| WebSocket | `wss://mainnet.flashblocks.base.org/ws` |

### Sepolia Testnet
| Type | Endpoint |
|------|----------|
| RPC | `https://sepolia-preconf.base.org` |
| WebSocket | `wss://sepolia.flashblocks.base.org/ws` |

> **Note:** Public endpoints are rate-limited. Use a node provider (Alchemy, QuickNode, Infura, dRPC) for production.

## RPC Integration

Use the `pending` block tag to query Flashblocks data:
```bash
# Get latest preconfirmed block
curl https://mainnet-preconf.base.org \
  -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["pending",true],"id":1}'

# Get preconfirmed balance
curl https://mainnet-preconf.base.org \
  -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getBalance","params":["0xYourAddress","pending"],"id":1}'
```

## Viem / Wagmi Integration
```typescript
import { createPublicClient, http } from 'viem'
import { baseSepoliaPreconf } from 'viem/chains'

// Use the preconf chain for Flashblocks
const client = createPublicClient({
  chain: baseSepoliaPreconf,
  transport: http('https://sepolia-preconf.base.org'),
})

// Automatically uses pending tag for all requests
const block = await client.getBlock({ blockTag: 'pending' })
```

For Wagmi:
```typescript
import { createConfig } from 'wagmi'
import { baseSepoliaPreconf } from 'viem/chains'
import { http } from 'viem'

export const config = createConfig({
  chains: [baseSepoliaPreconf],
  transports: {
    [baseSepoliaPreconf.id]: http('https://sepolia-preconf.base.org'),
  },
})
```

## WebSocket Streaming
```javascript
import WebSocket from 'ws'

const ws = new WebSocket('wss://mainnet.flashblocks.base.org/ws')

ws.on('message', (data) => {
  // Messages may be Brotli-compressed
  const flashblock = JSON.parse(data.toString())
  console.log('New flashblock:', flashblock.index) // 0-9 within a full block
})
```

## Supported RPC Methods

These standard Ethereum methods support the `pending` tag for Flashblocks:
- `eth_getBlockByNumber`
- `eth_getBalance`
- `eth_call`
- `eth_estimateGas`
- `eth_getTransactionCount`
- `eth_getTransactionReceipt` (always returns preconfirmed data)
- `eth_getTransactionByHash` (always returns preconfirmed data)

## Important Limitations

- **Preconfirmations are not final** — rare reorgs can cause differences between a Flashblock and the final block
- **Large transactions face constraints** — transactions with gas limits over 14M gas (1/10 of block gas limit) may have higher inclusion latency
- **Caching layers** — if you have a caching/routing layer in front of your nodes, you may need to modify behavior for Flashblocks-specific endpoints
- **Fallback behavior** — if Flashblocks infrastructure goes down, nodes fall back to standard 2-second block times automatically

## Node Providers Supporting Flashblocks

- Alchemy
- QuickNode
- Infura
- dRPC
- GetBlock
- Dwellir
