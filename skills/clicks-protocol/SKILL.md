---
name: clicks-protocol
description: Autonomous yield infrastructure for AI agents. Earn yield on x402 payments with 80% liquid, 20% earning (no lockup). Built on Base with MCP server integration.
homepage: https://clicksprotocol.xyz
metadata: {
  "category": "payments",
  "subcategory": "yield",
  "chains": ["base"],
  "tokens": ["USDC"],
  "x402": true,
  "mcp": true,
  "sdk": true
}
---

# Clicks Protocol

Autonomous yield infrastructure for AI agents.

## What is Clicks Protocol?

Clicks Protocol provides yield infrastructure for AI agents on Base. Agents can earn yield on their x402 payments with:

- **80% liquid, 20% earning** – No lockup, immediate liquidity
- **Built on Base** – Native x402 integration
- **MCP server** – Direct agent integration
- **TypeScript SDK** – Easy integration

## Installation

```bash
npx skills add base/skills@clicks-protocol
```

Or install globally:

```bash
npx skills add base/skills@clicks-protocol -g
```

## Quick Start

### 1. Configure your agent wallet

Make sure your agent has a Base wallet with USDC (Bankr, CDP Agentic Wallet, or Sponge Wallet).

### 2. Discover Clicks Protocol

```bash
# Search for yield services
npx skills search yield

# Or directly use Clicks
npx skills add base/skills@clicks-protocol
```

### 3. Earn yield on x402 payments

When your agent receives x402 payments, Clicks automatically:
1. **Routes 20%** to yield strategies
2. **Keeps 80%** liquid for immediate use
3. **Accumulates yield** in USDC

### 4. Check yield status

```bash
# Check your agent's yield position
npx skills run clicks-protocol status
```

## Integration with x402

Clicks Protocol integrates natively with Base's x402 payment standard:

### For Service Providers (Earning yield)

When you receive x402 payments, Clicks automatically routes a portion to yield strategies.

### For Service Consumers (Paying for services)

No change needed – continue using x402 as normal. Clicks works transparently in the background.

## MCP Server Integration

Clicks Protocol includes a Model Context Protocol (MCP) server for direct agent integration:

```bash
# Install MCP server
npm install @clicks-protocol/mcp-server

# Or use with Claude Code / Cursor
npx @clicks-protocol/mcp-server
```

## SDK

```bash
npm install @clicks-protocol/sdk
```

```typescript
import { ClicksClient } from '@clicks-protocol/sdk';

const clicks = new ClicksClient({
  chainId: 8453, // Base
  wallet: yourAgentWallet
});

// Get yield info
const yieldInfo = await clicks.getYieldInfo();
console.log(`APY : ${yieldInfo.apy}%`);
```

## Contract Addresses (Base Mainnet)

Clicks Protocol contracts are deployed on Base Mainnet (Chain 8453):

- **Registry**: `0x23bb0Ea69b2BD2e527D5DbA6093155A6E1D0C0a3` (Clicks Protocol Registry)
- **Fee Contract**: `0xc47B162D3c456B6C56a3cE6EE89A828CFd34E6bE` (Fee Distribution)
- **YieldRouter**: `0x4E29571FCCE958823c0B184a66EEb7bCbe1c849F` (Yield Strategy Router)
- **Splitter**: `0x24323A30626BBE78C00beA45A3c0eE36bA31FcB4` (80/20 Splitter)
- **Deployer/Treasury**: `0xf873BB73e10D24cD3CF9bBed917F5E2d07dA8B80`

All contracts are verified on [Basescan](https://basescan.org).

## Resources

- **Website**: https://clicksprotocol.xyz
- **GitHub**: https://github.com/clicks-protocol
- **MCP Server**: https://www.npmjs.com/package/@clicks-protocol/mcp-server
- **SDK**: https://www.npmjs.com/package/@clicks-protocol/sdk
- **Documentation**: https://docs.clicksprotocol.xyz

## Support

- **Discord**: https://discord.gg/clicks-protocol
- **Twitter**: @ClicksProtocol
- **Email**: hello@clicksprotocol.xyz

---

*Clicks Protocol – Yield infrastructure for the agent economy.*