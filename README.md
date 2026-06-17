# Base Skills

![Base](logo.webp)

[Agent Skills](https://agentskills.io) for building on [Base](https://base.org). These skills enable AI agents to connect to Base, deploy contracts, integrate wallets, run nodes, and more.

<!-- Badge row 1 - status -->

[![GitHub contributors](https://img.shields.io/github/contributors/base/skills)](https://github.com/base/skills/graphs/contributors)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/w/base/skills)](https://github.com/base/skills/graphs/contributors)
![GitHub repo size](https://img.shields.io/github/repo-size/base/skills)

<!-- Badge row 2 - links and profiles -->

[![Website base.org](https://img.shields.io/website-up-down-green-red/https/base.org.svg)](https://base.org)
[![Blog](https://img.shields.io/badge/blog-up-green)](https://base.mirror.xyz/)
[![Docs](https://img.shields.io/badge/docs-up-green)](https://docs.base.org/)
[![Discord](https://img.shields.io/discord/1067165013397213286?label=discord)](https://base.org/discord)
[![Twitter Base](https://img.shields.io/twitter/follow/Base?style=social)](https://twitter.com/Base)

<!-- Badge row 3 - detailed status -->

[![GitHub pull requests by-label](https://img.shields.io/github/issues-pr-raw/base/skills)](https://github.com/base/skills/pulls)
[![GitHub Issues](https://img.shields.io/github/issues-raw/base/skills.svg)](https://github.com/base/skills/issues)

## Recommended Skills

Two consolidated skills that cover the most common use cases. Each uses progressive reference loading — the skill loads a single entry point and pulls in detailed references only when needed.

| Skill | Install | Description |
| ----- | ------- | ----------- |
| [build-on-base](./skills/build-on-base/SKILL.md) | `npx skills add base/skills --skill build-on-base` | Complete Base development playbook: network, contracts, wallet auth, payments, attribution, and migrations. Consolidates all individual skills into one. |
| [base-mcp](./skills/base-mcp/SKILL.md) | `npx skills add base/skills --skill base-mcp` | Base MCP server — gives your AI assistant a wallet via mcp.base.org. Sending, swapping, signing, batched calls, balances, and partner plugins for lending, swaps, and more. |

## Installation

Install with [Vercel's Skills CLI](https://skills.sh):

```bash
npx skills add base/skills
```

## Usage

Skills are automatically available once installed. The agent will use them when relevant tasks are detected.

**Examples:**

```text
Deploy my contract to Base Sepolia
```

```text
How do I connect to Base mainnet?
```

```text
Add Sign in with Base to my app
```

```text
Convert my existing Farcaster miniapp to a standard app on Base
```

```text
Register my trading bot and add builder code attribution to its transactions
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the terms of the included LICENSE file.

---
[Base]: https://base.org
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

