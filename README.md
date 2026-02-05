![Base](logo.webp)

# Base Skills

A collection of AI agent skills that extend Claude's capabilities for building on Base and the Coinbase Developer Platform.

<!-- Badge row 1 - status -->

[![GitHub contributors](https://img.shields.io/github/contributors/base/base-skills)](https://github.com/base/base-skills/graphs/contributors)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/w/base/base-skills)](https://github.com/base/base-skills/graphs/contributors)
[![GitHub Stars](https://img.shields.io/github/stars/base/base-skills.svg)](https://github.com/base/base-skills/stargazers)
![GitHub repo size](https://img.shields.io/github/repo-size/base/base-skills)
[![GitHub](https://img.shields.io/github/license/base/base-skills?color=blue)](https://github.com/base/base-skills/blob/main/LICENSE)

<!-- Badge row 2 - links and profiles -->

[![Website base.org](https://img.shields.io/website-up-down-green-red/https/base.org.svg)](https://base.org)
[![Blog](https://img.shields.io/badge/blog-up-green)](https://base.mirror.xyz/)
[![Docs](https://img.shields.io/badge/docs-up-green)](https://docs.base.org/)
[![Discord](https://img.shields.io/discord/1067165013397213286?label=discord)](https://base.org/discord)
[![Twitter Base](https://img.shields.io/twitter/follow/Base?style=social)](https://twitter.com/Base)

<!-- Badge row 3 - detailed status -->

[![GitHub pull requests by-label](https://img.shields.io/github/issues-pr-raw/base/base-skills)](https://github.com/base/base-skills/pulls)
[![GitHub Issues](https://img.shields.io/github/issues-raw/base/base-skills.svg)](https://github.com/base/base-skills/issues)

## Overview

Skills are modular, self-contained packages that extend Claude's capabilities with specialized knowledge, workflows, and tools for building on [Base]. Think of them as "onboarding guides" that transform Claude from a general-purpose agent into a specialized assistant equipped with procedural knowledge for Base development.

## Available Skills

| Skill | Category | Location | Description |
|-------|----------|----------|-------------|
| **Building with Base Account** | Base Account | `skills/base-account/` | Integrates Base Account SDK for authentication and payments. Covers Sign in with Base (SIWB), Base Pay, Paymasters, Sub Accounts, and Spend Permissions. |
| **Connecting to Base Network** | Base Chain | `skills/base-chain/` | Configure wallet connections and RPC endpoints for Base Mainnet and Sepolia testnet. |
| **Deploying Contracts on Base** | Base Chain | `skills/base-chain/` | Deploy and verify smart contracts on Base using Foundry, Hardhat, or Remix. |
| **Running a Base Node** | Base Chain | `skills/base-chain/` | Set up and operate a Base node for production infrastructure. |
| **MiniKit to Farcaster Migration** | Mini Apps | `skills/miniapps/convert_minikit_fc/` | Convert Mini Apps from MiniKit (OnchainKit) to native Farcaster SDK with complete hook mapping and migration guides. |
| **Security Best Practices** | Security | `skills/` | Critical security practices for private keys, smart contracts, and production RPC configuration. |

## What Skills Provide

- **Specialized Workflows** - Multi-step procedures for Base development tasks
- **Domain Expertise** - Base-specific knowledge, SDKs, and best practices
- **Tool Integrations** - Instructions for working with Base APIs and development tools
- **Bundled Resources** - Scripts, references, and templates for complex tasks

## Getting Started

1. Clone this repository
2. Navigate to the specific skill directory you want to use
3. Follow the instructions in each skill's markdown file

### Using with Claude

Skills are designed to be loaded into Claude's context when working on relevant tasks. The skill's frontmatter metadata helps Claude understand when to apply specific knowledge:

```yaml
---
name: building-with-base-account
description: Integrates Base Account SDK for authentication and payments...
---
```

## Creating New Skills

This repository includes a skill-creator tool in `.claude/skills/skill-creator/` that provides guidance for creating effective skills. Run the initialization script to bootstrap a new skill:

```bash
python .claude/skills/skill-creator/scripts/init_skill.py <skill-name> --path <output-directory>
```

## Requirements

- Node.js (v16 or higher) for JavaScript/TypeScript skills
- Python 3.8+ for Python scripts

## Contributing

Contributions are welcome! When adding new skills:

1. Follow the skill structure pattern (SKILL.md with frontmatter)
2. Keep skills concise and focused on Base specific skills
3. Include relevant examples and common pitfalls
4. Test skills with real-world use cases

## License

This project is licensed under the terms of the included LICENSE file.

---
[Base]: https://base.org
[Coinbase Developer Platform]: https://portal.cdp.coinbase.com
