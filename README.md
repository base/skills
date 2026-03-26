# Base Skills

![Base](logo.webp)

[Agent Skills](https://agentskills.io) for building on [Base](https://base.org). These skills enable AI agents to connect to Base, deploy contracts, integrate wallets, run nodes, and more.

<!-- Badge row 1 - status -->

[![GitHub contributors](https://img.shields.io/github/contributors/base/base-skills)](https://github.com/base/base-skills/graphs/contributors)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/w/base/base-skills)](https://github.com/base/base-skills/graphs/contributors)
![GitHub repo size](https://img.shields.io/github/repo-size/base/base-skills)

<!-- Badge row 2 - links and profiles -->

[![Website base.org](https://img.shields.io/website-up-down-green-red/https/base.org.svg)](https://base.org)
[![Blog](https://img.shields.io/badge/blog-up-green)](https://base.mirror.xyz/)
[![Docs](https://img.shields.io/badge/docs-up-green)](https://docs.base.org/)
[![Discord](https://img.shields.io/discord/1067165013397213286?label=discord)](https://base.org/discord)
[![Twitter Base](https://img.shields.io/twitter/follow/Base?style=social)](https://twitter.com/Base)

<!-- Badge row 3 - detailed status -->

[![GitHub pull requests by-label](https://img.shields.io/github/issues-pr-raw/base/base-skills)](https://github.com/base/base-skills/pulls)
[![GitHub Issues](https://img.shields.io/github/issues-raw/base/base-skills.svg)](https://github.com/base/base-skills/issues)

## Available Skills

| Skill | Description |
| ----- | ----------- |
| [Adding Builder Codes](./skills/adding-builder-codes/SKILL.md) | Appends Base builder codes to transactions across Privy, Wagmi, Viem, and standard Ethereum RPC implementations. Automatically detects the user's framework before applying the correct integration pattern. |
| [Building with Base Account](./skills/building-with-base-account/SKILL.md) | Integrates Base Account SDK for authentication and payments, including SIWB, Base Pay, Paymasters, Sub Accounts, and Spend Permissions. |
| [Connecting to Base Network](./skills/connecting-to-base-network/SKILL.md) | Provides Base Mainnet and Sepolia network configuration, RPC endpoints, chain IDs, and explorer URLs. |
| [Converting Farcaster Miniapp to App](./skills/convert-farcaster-miniapp-to-app/SKILL.md) | Converts Farcaster Mini App SDK projects into regular Base web apps, with an option to preserve a small separate Farcaster-specific surface when needed. |
| [Deploying Contracts on Base](./skills/deploying-contracts-on-base/SKILL.md) | Deploys and verifies contracts on Base with Foundry, plus common troubleshooting guidance. |
| [Running a Base Node](./skills/running-a-base-node/SKILL.md) | Covers production node setup, hardware requirements, networking ports, and syncing guidance. |
| [Converting MiniKit to Farcaster](./skills/converting-minikit-to-farcaster/SKILL.md) | Migrates Mini Apps from MiniKit (OnchainKit) to native Farcaster SDK with mappings, examples, and pitfalls. |
| [Migrating an OnchainKit App](./skills/migrating-an-onchainkit-app/SKILL.md) | Migrates apps from @coinbase/onchainkit to standalone wagmi/viem components, replacing the provider, wallet, and transaction components. |
| [Registering an Agent on Base](./skills/registering-agent-base-dev/SKILL.md) | Registers an agent wallet with the Base builder code API and wires ERC-8021 transaction attribution into viem, ethers, or managed signing services. |

## Installation

Install with [Vercel's Skills CLI](https://skills.sh):

```bash
npx skills add base/base-skills
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
