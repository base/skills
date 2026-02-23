# Base Skills

![Base](logo.webp)

A collection of reusable AI agent skills for building on [Base](https://base.org).

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

## Overview

Skills are modular, self-contained packages that extend AI agents with specialized knowledge, workflows, and tools for building on [Base]. Think of them as onboarding guides that transform a general-purpose agent into a specialized assistant for Base development tasks.

## Available Skills

| Skill | Category | Location | Description |
| ----- | -------- | -------- | ----------- |
| **Building with Base Account** | Base Account | `building-with-base-account/SKILL.md` | Integrates Base Account SDK for authentication and payments, including SIWB, Base Pay, Paymasters, Sub Accounts, and Spend Permissions. |
| **Connecting to Base Network** | Base Chain | `connecting-to-base-network/SKILL.md` | Provides Base Mainnet and Sepolia network configuration, RPC endpoints, chain IDs, and explorer URLs. |
| **Deploying Contracts on Base** | Base Chain | `deploying-contracts-on-base/SKILL.md` | Deploys and verifies contracts on Base with Foundry, plus common troubleshooting guidance. |
| **Running a Base Node** | Infrastructure | `running-a-base-node/SKILL.md` | Covers production node setup, hardware requirements, networking ports, and syncing guidance. |
| **Base Security** | Security | `base-security/SKILL.md` | Security best practices for private key handling, smart contract safety, and production RPC usage. |
| **Converting MiniKit to Farcaster** | Mini Apps | `miniapps/converting-minikit-to-farcaster/SKILL.md` | Migrates Mini Apps from MiniKit (OnchainKit) to native Farcaster SDK with mappings, examples, and pitfalls. |

## What Skills Provide

- **Specialized Workflows** - Multi-step procedures for Base development tasks
- **Domain Expertise** - Base-specific knowledge, SDKs, and best practices
- **Tool Integrations** - Instructions for working with Base APIs and development tools
- **Bundled Resources** - Scripts, references, and templates for complex tasks

## Getting Started

1. Clone this repository
2. Open the skill directory relevant to your task
3. Use the corresponding `SKILL.md` file as the primary guide
4. Follow linked references in the same directory when needed

### Using with AI Agents

These skills are designed to be loaded into an agent's context when working on relevant tasks. This repo uses a `SKILL.md` pattern with frontmatter metadata that many agent ecosystems recognize:

```yaml
---
name: building-with-base-account
description: Integrates Base Account SDK for authentication and payments...
---
```

This repository is currently organized with Claude Code compatibility in mind (including the local `.claude/` tooling), but the skill content itself is written to be reusable across modern AI agent workflows.

## Creating New Skills

This repository includes a skill-creator tool in `.claude/skills/skill-creator/` that provides guidance for creating effective skills. Run the initialization script to bootstrap a new skill:

```bash
python .claude/skills/skill-creator/scripts/init_skill.py <skill-name> --path <output-directory>
```

## Requirements

- Node.js (v22.11.0+) for the MiniKit to Farcaster conversion workflow
- Python 3.8+ for Python scripts

## Contributing

Contributions are welcome! When adding new skills:

1. Follow the skill structure pattern (SKILL.md with frontmatter)
2. Keep skills concise and focused on Base-specific procedural guidance
3. Include relevant examples and common pitfalls
4. Test skills with real-world use cases

## License

This project is licensed under the terms of the included LICENSE file.

---
[Base]: https://base.org
[Coinbase Developer Platform]: https://portal.cdp.coinbase.com
