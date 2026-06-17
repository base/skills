# VVVKernel Scam Scan — Base Agent Skill

A pre-flight risk gate for any Base ERC-20 token. Combines on-chain data, Clanker V4 detection, fee recipient tracing, Bankrbot Agent API, and Venice AI judgment in a single call.

Designed to compose with [base-mcp](https://github.com/base/skills/tree/main/skills/base-mcp) — VVVKernel scans, Base MCP executes.

## Installation

Once merged into [base/skills](https://github.com/base/skills):

```bash
npx skills add base/vvvkernel-scam-scan
```

## Example

> "Swap 0.1 ETH to 0x...ba3 on Base"

1. Skill detects unverified contract
2. Calls `POST https://vvvkernel.com/api/token/analyze`
3. Returns verdict (LOW/MEDIUM/HIGH/EXTREME)
4. Agent halts on HIGH/EXTREME or proceeds via Base MCP on LOW

## Why

90% of agent-initiated swaps on chain die because the agent has no risk gate. A scam scan as a callable skill makes that gap a primitive.

## Built on

- Venice AI (private inference)
- Bankrbot Agent API
- Clanker V4 onchain reads
- Base mainnet RPC

## Links

- Live demo: https://vvvkernel.com
- Source: https://gitlawb.com/node/repos/z6Mkw3V6/vvvkernel
- $VVVK: `0xb66e76f9ed3e13f24c5b68f68be631cd82affba3` (Base mainnet)
