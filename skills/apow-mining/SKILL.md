---
name: apow-mining
description: Mine AGENT tokens on Base using AI proof-of-work. Handles wallet creation, RPC setup, LLM configuration, minting a Mining Rig NFT, and starting the autonomous mining loop. Use when a user wants to mine AGENT, set up an AI miner on Base, earn tokens with proof-of-work, or run an autonomous mining agent. Covers phrases like "mine AGENT tokens", "set up apow miner", "AI mining on Base", "mint a mining rig", or "start mining with my agent".
---

# APoW Mining: AI Proof-of-Work on Base

Mine $AGENT tokens on Base L2 with Agentic Proof of Work. Prove your agent identity once by minting an ERC-8004 Mining Rig (requires LLM), then compete on hash power with no LLM needed for mining. Your agent can do everything autonomously: generate wallets, configure the miner, mint a rig, and mine. The only step requiring the user is funding the wallet with ETH on Base.

**Protocol:** [github.com/Agentoshi/apow-core](https://github.com/Agentoshi/apow-core) | **CLI:** [github.com/Agentoshi/apow-cli](https://github.com/Agentoshi/apow-cli) | **npm:** `apow-cli`

## What is APoW?

Agent Proof-of-Work (APoW) is a mining protocol on Base L2 where AI agents prove their identity once by minting an ERC-8004 Mining Rig NFT (requires LLM to solve an SMHL challenge), then compete on hash power to mine AGENT tokens. Mining requires owning a Miner NFT (ERC-721 with rarity-based hashpower); no LLM needed after minting. Rewards start at 3 AGENT per mine (scaled by hashpower) and decay by 10% every 500,000 network mines, with a hard cap of 21,000,000 AGENT.

## Contract Addresses (Base Mainnet)

| Contract | Address |
|----------|---------|
| AgentCoin (ERC-20) | `0x12577CF0D8a07363224D6909c54C056A183e13b3` |
| MiningAgent (ERC-721) | `0xB7caD3ca5F2BD8aEC2Eb67d6E8D448099B3bC03D` |
| LPVault | `0xDD47511d060eA4E955B95F6f43553414328648a6` |

## Quick Start

```bash
npx apow-cli setup     # interactive wizard -- wallet, RPC, LLM config
npx apow-cli fund      # fund wallet -- bridge from Solana or show deposit address
npx apow-cli mint      # mint a mining rig NFT
npx apow-cli mine      # start mining (auto-detects your best rig)
```

## Autonomous Agent Flow (non-interactive)

Skip the interactive wizard and write the `.env` directly:

```bash
# 1. Generate a wallet
npx apow-cli wallet new
# Captures address + private key from output (also saved to wallet-<address>.txt)

# 2. Write .env directly (no interactive prompts needed)
#    LLM config is only needed for minting (one-time) -- mining uses algorithmic solving
cat > .env << 'EOF'
PRIVATE_KEY=0x<from step 1>
RPC_URL=https://base-mainnet.g.alchemy.com/v2/YOUR_KEY
LLM_PROVIDER=openai               # Required for minting only
LLM_MODEL=gpt-4o-mini             # Required for minting only
LLM_API_KEY=<your key>            # Required for minting only
MINING_AGENT_ADDRESS=0xB7caD3ca5F2BD8aEC2Eb67d6E8D448099B3bC03D
AGENT_COIN_ADDRESS=0x12577CF0D8a07363224D6909c54C056A183e13b3
EOF

# 3. Ask user to fund the wallet with ≥0.005 ETH on Base

# 4. Mint + mine (fully autonomous from here)
npx apow-cli mint
npx apow-cli mine
```

**Important:** Use a dedicated RPC endpoint (free Alchemy key recommended). The default public RPC (`mainnet.base.org`) has rate limits that cause failures during sustained mining.

**Important:** Use a fast, non-thinking LLM for minting (gpt-4o-mini, gemini-2.5-flash, deepseek-chat). Thinking models are too slow for the 20-second mint challenge window.

## Prerequisites

| Requirement | Details |
|---|---|
| **Node.js** | v18 or higher |
| **Base wallet** | A private key with ETH on Base (for gas + mint fee) |
| **LLM access** | API key (OpenAI, Gemini, DeepSeek, Qwen, or Anthropic) or local Ollama. **Required for minting only.** |

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `PRIVATE_KEY` | Yes | - | Wallet private key (0x + 64 hex chars) |
| `RPC_URL` | Recommended | `https://mainnet.base.org` | Base JSON-RPC endpoint |
| `LLM_PROVIDER` | No | `openai` | `openai`, `gemini`, `deepseek`, `qwen`, `anthropic`, or `ollama` |
| `LLM_API_KEY` | Conditional | - | API key (not needed for `ollama`) |
| `LLM_MODEL` | No | `gpt-4o-mini` | Model identifier passed to the provider |
| `MINING_AGENT_ADDRESS` | Yes | - | `0xB7caD3ca5F2BD8aEC2Eb67d6E8D448099B3bC03D` |
| `AGENT_COIN_ADDRESS` | Yes | - | `0x12577CF0D8a07363224D6909c54C056A183e13b3` |

## LLM Provider Recommendations

| Provider | Model | Cost per call | Notes |
|---|---|---|---|
| OpenAI | `gpt-4o-mini` | ~$0.001 | Cheapest, fastest, reliable |
| Gemini | `gemini-2.5-flash` | ~$0.001 | Fast, good accuracy |
| DeepSeek | `deepseek-chat` | ~$0.001 | Fast, accessible in China |
| Qwen | `qwen-plus` | ~$0.002 | Alibaba Cloud, accessible in China |
| Anthropic | `claude-sonnet-4-5-20250929` | ~$0.005 | High accuracy |
| Ollama | `llama3.1` | Free (local) | Requires local GPU; variable accuracy |

## How Mining Works

1. **Ownership check:** verifies your wallet owns a Miner NFT
2. **Fetch challenge:** reads the current mining challenge from AgentCoin
3. **Solve SMHL:** generates a valid SMHL solution algorithmically (sub-millisecond, no LLM needed)
4. **Grind nonce:** multi-threaded brute-force search for a valid Keccak-256 proof-of-work
5. **Submit proof:** calls `mine(nonce, smhlSolution, tokenId)` on-chain
6. **Collect reward:** AGENT tokens minted directly to your wallet
7. **Wait for next block:** one mine per block network-wide, then repeat

## Minting a Mining Rig

```bash
npx apow-cli mint
```

The CLI calls `getChallenge()`, solves the SMHL challenge with your LLM, then calls `mint(solution)` with the mint fee. Challenge expires in 20 seconds, so use an API-based provider.

**Mint price:** Starts at 0.002 ETH, decays by 5% every 100 mints, floors at 0.0002 ETH.

| Rarity | Hashpower | Reward Multiplier | Probability |
|---|---|---|---|
| Common | 100 | 1.00x | 60% |
| Uncommon | 150 | 1.50x | 25% |
| Rare | 200 | 2.00x | 10% |
| Epic | 300 | 3.00x | 4% |
| Mythic | 500 | 5.00x | 1% |

**Max supply:** 10,000 Miner NFTs.

## Reward Economics

| Parameter | Value |
|---|---|
| Base reward | 3 AGENT per mine |
| Hashpower scaling | `reward = baseReward * hashpower / 100` |
| Era decay | 10% every 500,000 total network mines |
| Max mineable supply | 18,900,000 AGENT |
| Competition | One mine per block, network-wide |

## Scaling with Multiple Wallets

Run separate wallets for more chances to win each block:

```bash
# Generate + fund sub-wallets
npx apow-cli wallet new        # → address A + key A
npx apow-cli wallet fund 0xA   # send ETH from main wallet

# Mint + mine in parallel
PRIVATE_KEY=0xKEY_A npx apow-cli mint
PRIVATE_KEY=0xKEY_A npx apow-cli mine &
```

## Monitoring

```bash
npx apow-cli stats            # network stats + auto-detect your rig
npx apow-cli stats <tokenId>  # stats for a specific rig
```

## Troubleshooting

| Error | Fix |
|---|---|
| `Expired` | Switch to an API-based provider (openai/gemini/anthropic/deepseek/qwen) |
| `429 Too Many Requests` | Switch to a dedicated RPC (Alchemy/QuickNode, both free) |
| `SMHL solve failed after 3 attempts` | Try a more capable model (`gpt-4o` or `claude-sonnet-4-5-20250929`) |
| `Not your miner` | Verify `PRIVATE_KEY` matches the NFT owner |
| `Supply exhausted` | All 18.9M mineable AGENT minted; mining complete |
| `10 consecutive failures` | Check RPC, wallet balance, and LLM availability |

## Security

- Private keys are generated locally via `crypto.randomBytes(32)` and never transmitted
- LLM calls contain only generic word-puzzle prompts, with no wallet data exposed
- Zero telemetry: no analytics, no error reporting, no phone-home
- Open source and MIT licensed
- Wallet files created with `0o600` permissions (owner-only)

## Links

- **Website:** [apow.io](https://apow.io)
- **CLI source:** [github.com/Agentoshi/apow-cli](https://github.com/Agentoshi/apow-cli)
- **Contracts:** [github.com/Agentoshi/apow-core](https://github.com/Agentoshi/apow-core)
- **npm:** [npmjs.com/package/apow-cli](https://www.npmjs.com/package/apow-cli)
