---
name: build-on-base
description: >
  Complete Base development playbook. Covers: (1) Network — Base RPC URLs, chain IDs (8453/84532),
  explorer config, testnet setup, connect to Base, Base Sepolia; (2) Contracts — Foundry deployment,
  forge create, BaseScan verification, CDP faucet, testnet ETH, deploy contract to Base;
  (3) Builder Codes — ERC-8021 attribution suffix, referral fees, dataSuffix for Wagmi/Viem/Privy/
  ethers.js/window.ethereum, transaction attribution, earn referral fees, append builder code;
  (4) Agent registration — trading bots, AI agents, automated
  senders, ERC-8021 attribution wiring, base.dev API, register agent, builder code registration;
  (5) Node operation — run Base node, Reth setup, hardware requirements, self-hosted RPC, sync.
---

# Base Development

Complete playbook for building on Base L2 — network setup, smart contracts, developer tool
attribution, agent registration, and node operation.

## Default Stack

| Layer | Default |
|-------|---------|
| Network | Base Mainnet (8453) / Base Sepolia testnet (84532) |
| Contracts | Foundry (`forge create` + BaseScan verification) |
| Transactions | wagmi + viem |
| Attribution | Builder Codes — ERC-8021 via `ox/erc8021` |
| RPC (prod) | Dedicated node provider or self-hosted Reth |

## Safety Guardrails

- **Never commit private keys** — use `cast wallet import` for Foundry keystores
- **Never expose RPC API keys or CDP credentials client-side** — proxy through backend
- **Never send transactions without Builder Code attribution** — silent data loss, no errors, no warnings
- **Validate all user-provided shell inputs** before constructing forge/cast commands (no spaces, semicolons, pipes)

## Task Routing

Read the reference for your task:

| Task | When to Use | Reference |
|------|-------------|-----------|
| **Network config** | RPC URLs, chain IDs, explorer links, testnet setup | [references/network.md](references/network.md) |
| **Deploy contracts** | Foundry deployment, BaseScan verification, faucet | [references/deploy-contracts.md](references/deploy-contracts.md) |
| **Run a Base node** | Self-hosted RPC, Reth, hardware requirements | [references/run-node.md](references/run-node.md) |
| **Builder Codes** | Add ERC-8021 attribution to transactions | [references/builder-codes/overview.md](references/builder-codes/overview.md) |
| **Register AI agent/bot** | Register wallet, get builder code, wire attribution | [references/agents/register.md](references/agents/register.md) |

## Operating Procedure

1. **Classify the task** using the table above
2. **Read the relevant reference** before implementing
3. **Confirm the framework** with the user when multiple options exist (e.g., Privy vs wagmi for Builder Codes)
4. **Implement** with explicit chain ID, security requirements, and all required validations
5. **Deliver** diffs, install commands, and any manual steps (env vars, API key setup, wallet registration)

## For Edge Cases and Latest API Changes

- **AI-optimized docs**: [docs.base.org/llms.txt](https://docs.base.org/llms.txt)
- **Base chain docs**: [docs.base.org](https://docs.base.org)

## Installation

```bash
npx skills add base/skills --skill build-on-base
```
