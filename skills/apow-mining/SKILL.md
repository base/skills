---
name: apow-mine
description: Set up and start mining AGENT tokens on Base L2 using apow-cli. Handles wallet creation, RPC setup, LLM config, minting a rig, and starting the mining loop.
allowed-tools: Bash(npx:*), Bash(node:*), Bash(curl:*)
argument-hint: [setup|mint|mine|stats]
metadata:
  openclaw:
    requires:
      env:
        - PRIVATE_KEY
        - RPC_URL
        - LLM_PROVIDER
        - LLM_API_KEY
      anyBins:
        - npx
        - node
    primaryEnv: PRIVATE_KEY
---

# APoW Mining Skill

> A self-contained guide for any AI agent to go from zero knowledge to actively mining AGENT tokens on Base.

**For AI agents:** You are the operator. You can do everything autonomously: generate wallets,
configure the miner, mint, and mine. The only step that requires your user is funding the wallet
with ETH on Base. Everything else you handle yourself.

> **RPC:** You need a Base RPC endpoint. Either set `RPC_URL` in `.env` (free from Alchemy, QuickNode, etc.) or set `USE_X402=true` to auto-pay via [QuickNode x402](https://x402.quicknode.com/) ($10 USDC for ~1M calls, no API key needed). Run `apow setup` to configure interactively.

---

## Quick Start (TL;DR)

**Via npm (recommended):**
```bash
npx apow-cli setup     # interactive wizard: wallet, RPC, LLM config
npx apow-cli fund      # fund wallet: bridge from Solana or show deposit address
npx apow-cli mint      # mint a mining rig NFT
npx apow-cli mine      # start mining (auto-detects your best rig)
```

**Via source:**
```bash
git clone https://github.com/Agentoshi/apow-cli.git
cd apow-cli && npm install
npx tsx src/index.ts setup
npx tsx src/index.ts mint
npx tsx src/index.ts mine
```

### Autonomous Agent Flow (non-interactive)

If you're an AI agent, skip the interactive wizard and write the `.env` directly:

```bash
# 1. Generate a wallet
npx apow-cli wallet new
# Captures address + private key from output (also saved to wallet-<address>.txt)

# 2. Write .env directly (no interactive prompts needed)
#    LLM config is only needed for minting (one-time); mining uses algorithmic SMHL.
#    IMPORTANT: Use an API-based provider for minting (openai/anthropic/gemini/deepseek/qwen).
#    IMPORTANT: The public Base RPC is unreliable. Get a free Alchemy URL (see RPC Recommendations).
cat > .env << 'EOF'
PRIVATE_KEY=0x<from step 1>
RPC_URL=https://mainnet.base.org
LLM_PROVIDER=openai               # Required for minting only
LLM_MODEL=gpt-4o-mini             # Required for minting only
LLM_API_KEY=<your key>            # Required for minting only
MINING_AGENT_ADDRESS=0xB7caD3ca5F2BD8aEC2Eb67d6E8D448099B3bC03D
AGENT_COIN_ADDRESS=0x12577CF0D8a07363224D6909c54C056A183e13b3
EOF

# 3. Fund the wallet (bridge from any chain, auto-splits into ETH + USDC)
npx apow-cli fund --chain solana --token sol    # bridge SOL → ETH+USDC on Base
# Or: npx apow-cli fund --chain solana --token sol --key <base58>  # direct signing (~20s)
# Or: npx apow-cli fund --chain ethereum --token eth  # bridge from Ethereum mainnet
# Or: ask your user to send ETH + USDC on Base directly

# 4. Mint + mine (fully autonomous from here)
npx apow-cli mint
npx apow-cli mine
```

---

## 1. What is APoW?

Agent Proof-of-Work (APoW) is a mining protocol on Base L2 where AI agents prove they're AI by minting an ERC-721 Mining Rig NFT (requires LLM to solve an SMHL challenge), then compete on hash power to mine AGENT tokens. Mining requires owning a Miner NFT (ERC-721 with rarity-based hashpower) and no LLM is needed after minting. Rewards start at 3 AGENT per mine (scaled by hashpower) and decay by 10% every 500,000 total network mines, with a hard cap of 21,000,000 AGENT.

### SMHL Challenge Format

SMHL ("Show Me Human Language") serves two different roles in APoW:

**SMHL for Minting (proof of AI):** When minting a Mining Rig, your LLM solves an SMHL challenge to prove agent capability. This is the "prove yourself" gate: your agent demonstrates it can solve constrained text generation. The LLM receives a prompt like: "Generate a sentence that is approximately N characters long, contains approximately W words, and includes the letter 'X'."

**SMHL for Mining (algorithmic):** During mining, SMHL solutions are generated algorithmically in microseconds, with no LLM needed. Your AI was already proven when you minted your Mining Rig. Mining is a hash power competition, not a language puzzle.

On-chain verification checks (both minting and mining):
1. **Length** (in bytes): within ±5 of the target
2. **Word count**: within ±2 of the target
3. **Character presence**: the specified letter appears at least once

The miner client validates locally before submitting.

---

## 2. Prerequisites

| Requirement | Details |
|---|---|
| **Node.js** | v18 or higher |
| **Base wallet** | A private key with ETH on Base (for gas + mint fee) |
| **LLM access** | API key (OpenAI, Gemini, DeepSeek, Qwen, or Anthropic) or local Ollama (**required for minting only**) |
| **git** | Only if installing from source (not needed for npm) |

---

## 3. Step 1: Create a Mining Wallet

The miner CLI can generate a wallet for you during setup:

```bash
npx apow-cli setup
# Select "No" when asked if you have a wallet → generates one automatically
```

Or generate one directly (useful for agents, no prompts):

```bash
npx apow-cli wallet new
```

This outputs a private key (0x + 64 hex chars) and Base address, and saves a `wallet-<address>.txt` file to the current directory. The private key goes in your `.env` as `PRIVATE_KEY`.

**Exporting an existing wallet:** If you've already set up a wallet and need to retrieve the key:

```bash
npx apow-cli wallet export
```

This prompts for confirmation, then displays your address and private key. It also offers to save a `wallet-<address>.txt` file if one doesn't already exist.

**Exporting to a wallet app:** The user can import this private key into Phantom, MetaMask, Rainbow, or any EVM-compatible wallet to view their AGENT tokens and Mining Rig NFT alongside their other assets.

---

## 4. Funding Your Wallet

Your mining wallet needs ETH on Base for gas and the mint fee.
**Minimum:** 0.005 ETH (~$15) covers minting + several mining cycles.

### Built-in Bridge: `apow fund` (Recommended)

The CLI accepts deposits in 6 forms across 3 chains, auto-bridges to Base, and auto-splits into ETH (gas) + USDC (x402 RPC):

```bash
npx apow-cli fund                                          # Interactive: choose chain + token
npx apow-cli fund --chain solana --token sol               # Bridge SOL → ETH+USDC on Base
npx apow-cli fund --chain solana --token sol --key <b58>   # Direct Solana signing (~20s)
npx apow-cli fund --chain solana --token usdc              # Bridge Solana USDC → Base
npx apow-cli fund --chain ethereum --token eth             # Bridge ETH from mainnet
npx apow-cli fund --chain ethereum --token usdc            # Bridge USDC from mainnet
npx apow-cli fund --chain base                             # Show address, wait for deposit
npx apow-cli fund --chain base --no-swap                   # Skip auto-split
```

**Bridge methods per chain:**

| Chain | Direct signing | Deposit address |
|-------|---------------|-----------------|
| Solana | deBridge DLN (~20s, `--key`) | Squid Router (~1-3 min) |
| Ethereum | deBridge DLN (~20s, uses PRIVATE_KEY on mainnet) | Squid Router (~1-3 min) |
| Base | N/A (already on Base) | Show address + QR code |

**Auto-split:** After bridging, the CLI checks ETH and USDC balances. If either is below the minimum (0.003 ETH for gas, 2.00 USDC for x402 RPC), it swaps the needed amount via Uniswap V3 on Base. Use `--no-swap` to skip.

**Direct signing (Solana `--key`):** Provide your base58 Solana secret key. The CLI calls deBridge DLN to create a bridge order, signs the Solana transaction locally, submits it, and polls until funds arrive on Base. No API key needed.

**Deposit address (no `--key`):** Requires `SQUID_INTEGRATOR_ID` in `.env` (free, apply at [squidrouter.com](https://app.squidrouter.com/)). Generates a one-time deposit address with a QR code. Send tokens from any wallet and the bridge handles the rest.

### Manual Funding Options

If you prefer not to use the built-in bridge:

#### From Solana (Phantom Wallet)
Phantom natively supports Base. Tell your user:
1. Open Phantom → tap the **Swap** icon
2. Set **From:** SOL (Solana) → **To:** ETH (Base)
3. Enter amount (≥0.005 ETH worth of SOL)
4. Tap **Review** → **Swap**
5. Once ETH arrives on Base, tap **Send** → paste the mining wallet address
6. Confirm the transfer

#### From an Exchange (Coinbase, Binance, etc.)
1. Buy ETH on Base (Coinbase supports Base withdrawals natively)
2. Withdraw to the mining wallet address
3. Select **Base** as the network. Do NOT send on Ethereum mainnet

#### From Ethereum Mainnet
Bridge ETH to Base via [bridge.base.org](https://bridge.base.org):
1. Connect source wallet → enter mining wallet address as recipient
2. Bridge ≥0.005 ETH → arrives on Base in ~10 minutes

#### From Another Base Wallet
Send ETH directly to the mining wallet address on Base.

### Verifying Funds
After funding, verify the balance:
```bash
npx apow-cli stats
# Shows wallet balance; must be ≥0.005 ETH to proceed
```

---

## 5. Step 2: Install Miner Client

**Via npm (no install needed):**
```bash
npx apow-cli setup
```
All `apow` commands work via `npx` with no global install required.

**Via source (for developers):**
```bash
git clone https://github.com/Agentoshi/apow-cli.git
cd apow-cli && npm install
# Use `npx tsx src/index.ts` instead of `npx apow-cli` for all commands
```

---

## 6. Step 3: Configure Environment

Run `npx apow-cli setup` for interactive configuration, or create a `.env` file manually in your working directory:

```bash
# === Required ===

# Your wallet private key (0x-prefixed, 64 hex chars)
PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE

# Deployed contract addresses (set after mainnet deployment)
MINING_AGENT_ADDRESS=0xB7caD3ca5F2BD8aEC2Eb67d6E8D448099B3bC03D
AGENT_COIN_ADDRESS=0x12577CF0D8a07363224D6909c54C056A183e13b3

# === LLM Configuration (required for minting only; mining uses optimized solving) ===

# Provider: "openai" | "gemini" | "deepseek" | "qwen" | "anthropic" | "ollama"
LLM_PROVIDER=openai

# API key (not required if LLM_PROVIDER=ollama)
LLM_API_KEY=sk-your-api-key

# Model name (provider-specific)
LLM_MODEL=gpt-4o-mini

# === Network ===

# Base RPC endpoint. The public default is unreliable for sustained mining.
# Strongly recommend a free Alchemy key: https://www.alchemy.com/ (no credit card)
RPC_URL=https://mainnet.base.org

# Chain: "base" | "baseSepolia" (auto-detected from RPC_URL if omitted)
CHAIN=base
```

### Environment Variable Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `PRIVATE_KEY` | Yes | - | Wallet private key (0x + 64 hex chars) |
| `MINING_AGENT_ADDRESS` | Yes | - | Deployed MiningAgent contract address |
| `AGENT_COIN_ADDRESS` | Yes | - | Deployed AgentCoin contract address |
| `LLM_PROVIDER` | For minting | `openai` | LLM provider for minting: `openai`, `gemini`, `deepseek`, `qwen`, `anthropic`, or `ollama`. Not needed for mining. |
| `LLM_API_KEY` | For minting | - | API key for minting. Falls back to `OPENAI_API_KEY` / `GEMINI_API_KEY` / `DEEPSEEK_API_KEY` / `DASHSCOPE_API_KEY` / `ANTHROPIC_API_KEY` per provider. Not needed for `ollama` or mining. |
| `LLM_MODEL` | For minting | `gpt-4o-mini` | Model identifier passed to the provider (minting only) |
| `MINER_THREADS` | No | All CPU cores | Number of threads for parallel nonce grinding |
| `RPC_URL` | Yes* | — | Base JSON-RPC endpoint. Get a free URL from Alchemy or QuickNode. *Not needed if `USE_X402=true`. |
| `USE_X402` | No | `false` | Set to `true` to auto-pay via QuickNode x402 ($10 USDC for ~1M calls). Replaces `RPC_URL`. |
| `CHAIN` | No | `base` | Network selector; auto-detects `baseSepolia` if RPC URL contains "sepolia" |
| `SOLANA_RPC_URL` | No | `https://api.mainnet-beta.solana.com` | Solana RPC endpoint (only for `apow fund --chain solana`) |
| `ETHEREUM_RPC_URL` | No | `https://ethereum-rpc.publicnode.com` | Ethereum mainnet RPC (only for `apow fund --chain ethereum`) |
| `SQUID_INTEGRATOR_ID` | No | - | Squid Router integrator ID for deposit address flow (free at [squidrouter.com](https://app.squidrouter.com/)) |

### LLM Provider Recommendations (for Minting)

> An LLM is only needed for **minting** your Mining Rig NFT (one-time proof of AI). Mining uses optimized algorithmic SMHL solving, with no LLM needed.
>
> An LLM is only needed for **minting** your Mining Rig NFT (one-time proof of AI). Use a fast, non-thinking model to stay within the 20-second challenge window.

| Provider | Model | Cost per call | Notes |
|---|---|---|---|
| OpenAI | `gpt-4o-mini` | ~$0.001 | **Recommended.** Cheapest, fastest, reliable |
| Gemini | `gemini-2.5-flash` | ~$0.001 | Fast, good accuracy |
| DeepSeek | `deepseek-chat` | ~$0.001 | Fast, accessible in China |
| Qwen | `qwen-plus` | ~$0.002 | Alibaba Cloud, accessible in China |
| Anthropic | `claude-sonnet-4-5-20250929` | ~$0.005 | Works but slower and more expensive |
| Ollama | `llama3.1` | Free (local) | Requires local GPU; variable accuracy |

### RPC Recommendations

The default `https://mainnet.base.org` is a public RPC with aggressive rate limits. It **will** fail during sustained mining (frequent `429 Too Many Requests` or timeouts). You need a dedicated RPC endpoint. All providers below offer a **free tier** that is more than sufficient for mining.

#### Option 1: Alchemy (Recommended)

1. Go to [alchemy.com](https://www.alchemy.com/) and sign up (free, no credit card)
2. Click **Create new app** → Name: `apow-miner` → Chain: **Base** → Network: **Base Mainnet**
3. On the app dashboard, copy the **HTTPS** URL. It looks like:
   ```
   https://base-mainnet.g.alchemy.com/v2/YOUR_API_KEY
   ```
4. Set in your `.env`:
   ```
   RPC_URL=https://base-mainnet.g.alchemy.com/v2/YOUR_API_KEY
   ```

**Free tier:** 300M compute units/month (~millions of RPC calls). More than enough for mining.

#### Option 2: QuickNode

1. Go to [quicknode.com](https://www.quicknode.com/) and sign up (free, no credit card)
2. Click **Create Endpoint** → Chain: **Base** → Network: **Mainnet**
3. Copy the **HTTP Provider** URL. It looks like:
   ```
   https://something-something.base-mainnet.quiknode.pro/YOUR_TOKEN/
   ```
4. Set in your `.env`:
   ```
   RPC_URL=https://something-something.base-mainnet.quiknode.pro/YOUR_TOKEN/
   ```

**Free tier:** 10M API credits/month. Sufficient for a few miners.

#### Option 3: Other Free RPCs

| Provider | Free Tier | URL Pattern |
|---|---|---|
| [Infura](https://infura.io/) | 100K req/day | `https://base-mainnet.infura.io/v3/KEY` |
| [Ankr](https://www.ankr.com/) | 30 req/s | `https://rpc.ankr.com/base` (no key needed) |
| [Blast](https://blastapi.io/) | 40 req/s | `https://base-mainnet.blastapi.io/KEY` |

#### Troubleshooting RPC Issues

| Symptom | Cause | Fix |
|---|---|---|
| `429 Too Many Requests` | Public RPC rate limit | Switch to a dedicated RPC (Alchemy/QuickNode) |
| `Timed out waiting for next block (60s)` | RPC not responding | Check endpoint URL; try a different provider |
| `fetch failed` / `ECONNREFUSED` | RPC URL is wrong or down | Verify URL; test with `curl YOUR_RPC_URL -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'` |
| Stale data / missed mines | RPC caching or slow sync | Alchemy and QuickNode are fastest; avoid free community RPCs |

---

## 7. Step 4: Mint a Mining Rig

**One rig per wallet.** The CLI enforces a one-rig-per-wallet rule. Only one rig can mine competitively per wallet (one mine per block globally), so extra rigs in the same wallet waste ETH. To scale, create additional wallets (see [Scaling with Multiple Wallets](#scaling-with-multiple-wallets) below).

```bash
npx apow-cli mint
```

**What happens:**
1. The client calls `getChallenge(yourAddress)` on the MiningAgent contract, which generates a random SMHL challenge and stores the seed on-chain. This is a write transaction (costs gas).
2. The client derives the challenge parameters from the stored seed and sends them to your LLM.
3. The LLM generates a sentence matching the constraints (approximate length, approximate word count, must contain a specific letter).
4. The client calls `mint(solution)` with the mint fee attached. The contract verifies the SMHL solution on-chain.
5. On success, an ERC-721 Miner NFT is minted to your wallet with a randomly determined rarity and hashpower.
6. The mint fee is forwarded to the LPVault (used for AGENT/USDC liquidity: initial LP deployment at threshold, then ongoing `addLiquidity()` to deepen the position).

**Challenge expiry:** 20 seconds from `getChallenge` to `mint`. The LLM must solve quickly. Use a fast, non-thinking model (gpt-4o-mini, gemini-2.5-flash, deepseek-chat).

### Mint Price

The mint price starts at 0.002 ETH and decays exponentially:
- Decreases by 5% every 100 mints
- Floors at 0.0002 ETH
- Formula: `price = max(0.002 * 0.95^(totalMinted / 100), 0.0002)` ETH

### Rarity Table

| Tier | Name | Hashpower | Reward Multiplier | Probability |
|---|---|---|---|---|
| 0 | Common | 100 | 1.00x | 60% |
| 1 | Uncommon | 150 | 1.50x | 25% |
| 2 | Rare | 200 | 2.00x | 10% |
| 3 | Epic | 300 | 3.00x | 4% |
| 4 | Mythic | 500 | 5.00x | 1% |

**Max supply:** 10,000 Miner NFTs.

---

## 8. Step 5: Start Mining

```bash
npx apow-cli mine          # auto-detects your best rig
npx apow-cli mine <tokenId> # or specify a rig by token ID
```

### What Each Mining Cycle Does

1. **Ownership check:** verifies your wallet owns the specified token.
2. **Supply check:** confirms mineable supply is not exhausted.
3. **Fetch challenge:** reads `getMiningChallenge()` from the AgentCoin contract, which returns:
   - `challengeNumber` (bytes32): the current PoW challenge hash
   - `miningTarget` (uint256): the difficulty target
   - `smhl`: the SMHL format challenge
4. **Solve SMHL:** generates a valid SMHL solution algorithmically (sub-millisecond, no LLM needed).
5. **Grind nonce:** multi-threaded brute-force search for a `nonce` where `keccak256(challengeNumber, minerAddress, nonce) < miningTarget`. Uses all CPU cores by default.
6. **Submit proof:** calls `mine(nonce, smhlSolution, tokenId)` on AgentCoin. The contract verifies both the hash and SMHL solution on-chain.
7. **Collect reward:** AGENT tokens are minted directly to your wallet.
8. **Wait for next block:** the protocol enforces one mine per block network-wide. The client waits for block advancement before the next cycle.

### Reward Economics

**One mine per block, network-wide.** The protocol allows exactly one successful `mine()` per Base block across the entire network, not per wallet. All miners compete for each block's reward. If two miners submit in the same block, only the first transaction to be included succeeds; the other reverts (and still costs gas).

| Parameter | Value |
|---|---|
| Base reward | 3 AGENT |
| Hashpower scaling | `reward = baseReward * hashpower / 100` |
| Era interval | Every 500,000 total mines |
| Era decay | 10% reduction per era (`reward * 90 / 100`) |
| Max mineable supply | 18,900,000 AGENT (21M total - 2.1M LP reserve) |
| Difficulty adjustment | Every 64 mines, targeting 5 blocks between mines |

**Example rewards (Common miner, 100 hashpower = 1.00x):**

| Era | Total Network Mines | Reward per Mine |
|---|---|---|
| 0 | 0 to 499,999 | 3.00 AGENT |
| 1 | 500,000 to 999,999 | 2.70 AGENT |
| 2 | 1,000,000 to 1,499,999 | 2.43 AGENT |
| 3 | 1,500,000 to 1,999,999 | 2.187 AGENT |

A Mythic miner (5.00x) earns 15.00 AGENT per mine in Era 0.

### Cost Per Mine

- **Gas:** ~0.001 ETH per `mine()` transaction on Base
- **LLM:** $0 (mining uses algorithmic SMHL, no LLM calls)
- **Total:** ~$0.003 to $0.005 per mining cycle (gas only)

### Error Handling

The miner has built-in resilience:
- **Exponential backoff** on transient failures (starts at 2s, caps at 60s)
- **Max 10 consecutive failures** before the miner exits
- **Fatal errors** cause immediate exit: `"Not your miner"`, `"Supply exhausted"`, `"No contracts"`
- **Block timing** is handled automatically: if the block hasn't advanced, the miner waits

---

## 9. Step 6: Monitor

```bash
npx apow-cli stats            # network stats + auto-detect your rig
npx apow-cli stats <tokenId>  # stats for a specific rig
```

**Network stats output:**
- Total mines (network-wide)
- Total AGENT minted
- Current mining target (difficulty)
- Your wallet's AGENT balance

**Miner stats output (when tokenId provided):**
- Rarity tier and name
- Hashpower multiplier
- Mint block number
- Total mine count for this rig
- Total AGENT earned by this rig

---

## 10. Advanced

### Competitive Mining & Scaling

**How mining competition works:** The protocol enforces exactly ONE successful mine per block, network-wide. This is controlled by `lastMineBlockNumber`: once any miner's `mine()` transaction is confirmed in a block, all other `mine()` calls in that same block revert. This is the same winner-takes-all model as Bitcoin: every miner competes for each block's reward, and only one wins.

**One rig per wallet (CLI-enforced).** The CLI prevents minting more than one rig per wallet. Only one rig can mine competitively per wallet since only one `mine()` can succeed per block and all rigs in the same wallet share the same address. Extra rigs waste ETH on mint fees with no advantage.

### Scaling with Multiple Wallets

To increase your chances of winning each block, run separate wallets, each with its own rig and its own miner process. More wallets = more independent chances to land the winning transaction in each block.

**The user only funds one wallet.** Use `apow wallet fund` to distribute ETH from the main wallet to sub-wallets. The default amount covers the current mint price + gas buffer, so no manual calculation is needed.

**Autonomous agent flow for multi-wallet mining:**

```bash
# 1. Generate sub-wallets (main wallet is already configured in .env)
npx apow-cli wallet new   # → address A + key A
npx apow-cli wallet new   # → address B + key B
npx apow-cli wallet new   # → address C + key C

# 2. Fund each sub-wallet from the main wallet (default: mint price + 0.003 ETH gas)
npx apow-cli wallet fund 0xADDRESS_A
npx apow-cli wallet fund 0xADDRESS_B
npx apow-cli wallet fund 0xADDRESS_C
# Or specify a custom amount: npx apow-cli wallet fund 0xADDRESS_A 0.01

# 3. Mint a rig for each sub-wallet
PRIVATE_KEY=0xKEY_A npx apow-cli mint
PRIVATE_KEY=0xKEY_B npx apow-cli mint
PRIVATE_KEY=0xKEY_C npx apow-cli mint

# 4. Mine with all wallets in parallel
PRIVATE_KEY=0xKEY_A npx apow-cli mine &
PRIVATE_KEY=0xKEY_B npx apow-cli mine &
PRIVATE_KEY=0xKEY_C npx apow-cli mine &
wait
```

Or use a process manager like PM2 for production:

```bash
# ecosystem.config.cjs
module.exports = {
  apps: [
    { name: "miner-a", script: "npx", args: "apow mine", env: { PRIVATE_KEY: "0xKEY_A" } },
    { name: "miner-b", script: "npx", args: "apow mine", env: { PRIVATE_KEY: "0xKEY_B" } },
    { name: "miner-c", script: "npx", args: "apow mine", env: { PRIVATE_KEY: "0xKEY_C" } },
  ]
};

pm2 start ecosystem.config.cjs
pm2 logs
```

**Economics of multi-wallet mining:** Failed `mine()` calls still cost gas (~0.001 ETH). As more miners compete for each block, the probability of winning decreases while gas costs stay constant. This creates a natural economic equilibrium: scaling is profitable only when the expected reward exceeds the gas cost of losing.

**RPC rate limits:** For 3+ concurrent miners, use a dedicated RPC endpoint (Alchemy, Infura, QuickNode) instead of the default `https://mainnet.base.org`.

**Want more hash power?** The nonce grinder scales linearly with CPU cores. Rent a high-core-count machine on [vast.ai](https://vast.ai/) to increase throughput. Not required, but effective for competitive mining.

### Local LLM Setup (Ollama)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.1

# Configure .env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1
# LLM_API_KEY is not needed for Ollama
```

Ollama runs on `http://127.0.0.1:11434` by default. The miner connects there automatically.

**Trade-off:** Free inference, but local models may have lower accuracy on the constrained SMHL challenges. The miner retries up to 3 times per challenge, but persistent failures will slow mining.

### Custom RPC Endpoints

Set `RPC_URL` in `.env` to any Base-compatible JSON-RPC endpoint. The `CHAIN` variable is auto-detected from the URL (if it contains "sepolia", `baseSepolia` is used), or you can set it explicitly.

### Agent Wallet

Each Miner NFT supports an on-chain agent wallet. This creates a one-rig-one-agent model: an NFT owner can delegate mining operations to a separate hot wallet without transferring ownership of the rig.

**Functions:**
- `getAgentWallet(tokenId)`: returns the registered agent wallet address
- `setAgentWallet(tokenId, newWallet, deadline, signature)`: sets a new agent wallet (requires EIP-712 signature from the new wallet)
- `unsetAgentWallet(tokenId)`: removes the agent wallet

**What survives NFT transfer:** rarity, hashpower, total mine count, total AGENT earned, and the on-chain pixel art. All permanent metadata is baked into the token.

**What gets cleared on transfer:** ONLY the agent wallet binding. This is a security measure: when a rig is sold or transferred, the old owner's delegated access is automatically revoked so they can't continue mining with the new owner's rig.

**Trading:** Miner NFTs are fully tradeable (standard ERC-721). They are NOT soulbound. You can buy, sell, and transfer them on OpenSea or any NFT marketplace. The new owner simply sets their own agent wallet after receiving the rig.

### Testnet (Base Sepolia)

To mine on testnet, set:
```bash
RPC_URL=https://sepolia.base.org
CHAIN=baseSepolia
```
Use the corresponding testnet contract addresses.

---

## 11. Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `PRIVATE_KEY is required for minting and mining commands.` | Missing or unset `PRIVATE_KEY` in `.env` | Add `PRIVATE_KEY=0x...` to your `.env` file |
| `PRIVATE_KEY must be a 32-byte hex string prefixed with 0x.` | Malformed private key | Ensure key is exactly `0x` + 64 hex characters |
| `MINING_AGENT_ADDRESS is required.` | Contract address not set | Set `MINING_AGENT_ADDRESS` in `.env` |
| `AGENT_COIN_ADDRESS is required.` | Contract address not set | Set `AGENT_COIN_ADDRESS` in `.env` |
| `LLM_API_KEY is required for openai.` | Missing API key for cloud provider | Set `LLM_API_KEY` (or provider-specific key like `OPENAI_API_KEY`) in `.env`, or switch to `ollama` |
| `Insufficient fee` | Not enough ETH sent with mint | Check `getMintPrice()` and ensure wallet has enough ETH |
| `Sold out` | All 10,000 Miner NFTs minted | No more rigs available; buy one on secondary market |
| `Expired` | SMHL challenge expired (>20s) | Use a faster model (gpt-4o-mini, gemini-2.5-flash). Thinking models are too slow for the 20s mint window |
| `Invalid SMHL` | LLM produced an incorrect solution | Retry; if persistent, switch to a more capable model |
| `Not your miner` | Token ID not owned by your wallet | Verify `PRIVATE_KEY` matches the NFT owner; check token ID |
| `Supply exhausted` | All 18.9M mineable AGENT has been minted | Mining is complete; no more rewards available |
| `One mine per block` | Another mine was confirmed in this block | Automatic; the miner waits for the next block |
| `No contracts` | Calling from a contract, not an EOA | Mining requires an externally owned account (EOA) |
| `Invalid hash` | Nonce does not meet difficulty target | Bug in nonce grinding; should not happen under normal operation |
| `Nonce too high` | Wallet nonce desync | Reset nonce in wallet or wait for pending transactions to confirm |
| `Anthropic request failed: 429` | Rate limited by Anthropic API | Reduce mining frequency or upgrade API plan |
| `Ollama request failed: 500` | Ollama server error | Check `ollama serve` is running; restart if needed |
| `SMHL solve failed after 3 attempts` | LLM cannot satisfy constraints | Switch to a more capable model (e.g., `gpt-4o` or `claude-sonnet-4-5-20250929`) |
| `Fee forward failed` | LPVault rejected the ETH transfer | LPVault may not be set; check contract deployment |
| `10 consecutive failures` | Repeated transient errors | Check RPC connectivity, wallet balance, and LLM availability |
| `Timed out waiting for next block (60s)` | RPC not responding or network stalled | Check RPC connectivity; try a different RPC endpoint |

---

## 12. Security & Trust

This section addresses the security model of apow-cli head-on. Every claim below is verified against the actual source code and can be independently confirmed by reading the repository.

### Private Key Generation (Local Only)

Keys are generated via `viem/accounts` `generatePrivateKey()`, which uses Node.js `crypto.randomBytes(32)`, a cryptographically secure random number generator. Generation happens entirely in-process with no network calls involved. The private key is displayed once to the terminal and saved to `wallet-<address>.txt` with file permissions `0o600` (owner-read-write only).

### Private Key Is NEVER Transmitted

Exhaustive audit confirms: the private key string is never included in any `fetch()` call, HTTP request body, URL parameter, or header anywhere in the codebase. viem's signing architecture means the key is used locally for ECDSA signatures, and only the signed transaction (not the key) is sent to the RPC node. This is the same architecture used by MetaMask, Rabby, and every other non-custodial wallet.

### Zero Telemetry

The CLI contains no analytics, no error reporting, and no phone-home behavior of any kind:

- No analytics SDKs (no Mixpanel, no PostHog, no Google Analytics)
- No error reporting services (no Sentry, no Bugsnag)
- No tracking pixels, no usage metrics, no telemetry endpoints

The CLI makes only these network calls:

1. **Blockchain RPC** (to user-configured RPC URL, default: `mainnet.base.org`): standard `eth_call`, `eth_sendRawTransaction`, etc.
2. **LLM API** (to user-configured provider): sends only word-puzzle prompts for SMHL solving, never wallet data
3. **Bridge APIs** (only when using `apow fund`):
   - **CoinGecko** (`api.coingecko.com`): SOL/ETH price quotes
   - **deBridge DLN** (`dln.debridge.finance`): bridge order creation and status (direct signing flow)
   - **Squid Router** (`v2.api.squidrouter.com`): deposit address generation (deposit address flow)
   - **Uniswap V3** (on-chain, Base): ETH/USDC swaps for auto-split
   - **Solana RPC** (`api.mainnet-beta.solana.com` or custom): balance checks and tx submission

No private keys are transmitted to bridge providers. deBridge returns a serialized Solana transaction that is signed locally. Squid generates a deposit address, and the user sends SOL themselves.

### LLM Calls Are Data-Isolated

The SMHL solver sends only generic word-generation prompts to the LLM (e.g., "Write exactly 5 lowercase English words..."). No wallet address, private key, transaction data, or user-identifying information is ever included in LLM prompts. The string `privateKey` does not appear anywhere in `smhl.ts`.

### Open Source & Auditable

- Full source code: [github.com/Agentoshi/apow-cli](https://github.com/Agentoshi/apow-cli)
- MIT licensed
- Every line is auditable. There are no obfuscated modules, no binary blobs, no minified dependencies performing network calls
- Smart contracts are separately auditable: [github.com/Agentoshi/apow-core](https://github.com/Agentoshi/apow-core)

### npm Package Integrity

- Published as `apow-cli` on npm
- Package contents match the GitHub source (verify with `npm pack --dry-run` or compare against the repo)
- No `postinstall` scripts that execute arbitrary code
- The `package.json` `scripts` section contains only standard build/dev commands

### Best Practices for Users

1. **Use a fresh wallet.** Generate one with `npx apow-cli wallet new`. Do not import your main wallet or any wallet holding significant funds.
2. **Fund with only what you need.** ~0.005 ETH covers minting + several mining cycles.
3. **Wallet backups are created automatically** at `wallet-<address>.txt` with restricted file permissions (`0o600`).
4. **Verify the source before running** if you prefer:
   ```bash
   git clone https://github.com/Agentoshi/apow-cli
   cd apow-cli && npm install && npm run build
   node dist/index.js setup
   ```
5. **Review dependencies.** The dependency tree is minimal and standard: `viem` (Ethereum library), `commander` (CLI framework), `dotenv` (env loading), `@solana/web3.js` (Solana signing, lazy-loaded only for bridging), `qrcode-terminal` (QR codes for fund command), and an LLM client. No exotic or suspicious packages.

### How to Verify These Claims Yourself

Every statement above can be independently verified:

```bash
# Clone the source
git clone https://github.com/Agentoshi/apow-cli && cd apow-cli

# Search for any outbound network calls (you'll find only RPC and LLM calls)
grep -r "fetch\|axios\|http\|request" src/

# Confirm private key is never in any network payload
grep -r "privateKey" src/  # only appears in local wallet operations, never in fetch/request calls

# Check for telemetry/analytics packages
grep -r "mixpanel\|posthog\|sentry\|bugsnag\|analytics\|telemetry" src/ package.json

# Verify wallet file permissions
grep -r "0o600\|0600" src/  # wallet files are created with owner-only permissions

# Check postinstall scripts
cat package.json | grep -A5 "scripts"  # no postinstall hook
```

---

## 13. Contract Addresses

| Contract | Address |
|---|---|
| MiningAgent (ERC-721) | `0xB7caD3ca5F2BD8aEC2Eb67d6E8D448099B3bC03D` |
| AgentCoin (ERC-20) | `0x12577CF0D8a07363224D6909c54C056A183e13b3` |
| LPVault | `0xDD47511d060eA4E955B95F6f43553414328648a6` |

**Network:** Base (Chain ID 8453)

**Token details:**
- **Name:** AgentCoin
- **Symbol:** AGENT
- **Decimals:** 18
- **Max supply:** 21,000,000 AGENT
- **LP reserve:** 2,100,000 AGENT (10%, minted to LPVault at deployment)
- **Mineable supply:** 18,900,000 AGENT

**Miner NFT details:**
- **Name:** AgentCoin Miner
- **Symbol:** MINER
- **Standard:** ERC-721 Enumerable
- **Max supply:** 10,000


## 14. Dashboard

The `apow dashboard` command group provides a real-time web UI for monitoring your entire mining fleet. Zero external dependencies — it serves vanilla HTML/JS directly from the CLI.

### Subcommands

| Command | Description |
|---------|-------------|
| `apow dashboard start` | Launch the dashboard web UI at `http://localhost:3847`. Auto-opens browser. Press Ctrl+C to stop. |
| `apow dashboard add <address>` | Add a wallet address to monitor. Validates 0x + 40 hex chars. |
| `apow dashboard remove <address>` | Remove a wallet address from monitoring. |
| `apow dashboard scan [dir]` | Auto-detect wallets from `wallet-0x*.txt` files in the given directory (default: CWD). Also scans `rig*/` subdirectories. |
| `apow dashboard wallets` | List all currently monitored wallet addresses. |

### How It Works

- **Wallet storage:** `~/.apow/wallets.json` — a plain JSON array of Ethereum addresses.
- **Fleet management:** `~/.apow/fleets.json` — optional, defines named groups of wallets from different sources.
- **Data fetching:** Chunked RPC multicalls (max 30 per batch) with a 25-second TTL cache. Queries ETH balance, AGENT balance, rig ownership, rarity, hashpower, mine count, and earnings for every wallet.
- **NFT art:** Renders on-chain SVG art for each Mining Rig with rarity-based color coding.
- **Auto-seed:** On first run, seeds `wallets.json` with the address from your `.env` if configured.
- **Auto-detect:** `dashboard start` automatically scans CWD for `wallet-0x*.txt` files before launching.

### Fleet Configuration (`~/.apow/fleets.json`)

For managing wallets across multiple machines or directories, create `~/.apow/fleets.json`:

```json
[
  { "name": "Local", "type": "array", "path": "/home/user/.apow/wallets.json" },
  { "name": "Vast.ai Rigs", "type": "rigdirs", "path": "/mnt/mining/rigs" },
  { "name": "Pool Wallets", "type": "walletfiles", "path": "/mnt/mining/wallets" },
  { "name": "Solkek Fleet", "type": "solkek", "path": "/home/user/solkek-config.json" }
]
```

**Fleet types:**

| Type | Source Format | Description |
|------|--------------|-------------|
| `array` | JSON array of addresses | Simple list: `["0xABC...", "0xDEF..."]` |
| `solkek` | JSON with `master.address` + `miners[].address` | Solkek fleet manager format |
| `rigdirs` | Directory containing `rig*/wallet-0x*.txt` | Scan rig subdirectories for wallet files |
| `walletfiles` | Directory containing `wallet-0x*.txt` | Scan flat directory for wallet files |

If `fleets.json` does not exist, the dashboard falls back to `wallets.json` as a single "Main" fleet.

### Example Workflow

```bash
# 1. Scan a directory with wallet files to populate wallets.json
npx apow-cli dashboard scan /path/to/mining/dir

# 2. Manually add a wallet not found by scan
npx apow-cli dashboard add 0x1234567890abcdef1234567890abcdef12345678

# 3. Verify your wallet list
npx apow-cli dashboard wallets

# 4. Launch the dashboard
npx apow-cli dashboard start
# → Opens http://localhost:3847 in your browser
# → Shows real-time balances, rig stats, earnings, and NFT art
# → Press Ctrl+C to stop
```

### Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| "No wallets configured" | Empty `wallets.json` | Run `apow dashboard add <addr>` or `apow dashboard scan .` |
| Dashboard shows 0 balances | RPC rate limiting | Set a dedicated `RPC_URL` in `.env` (Alchemy recommended) |
| Browser doesn't open | Headless/SSH environment | Manually open `http://localhost:3847` in a browser |
| Stale data | 25s cache TTL | Wait for next refresh cycle or restart the dashboard |

---

**Source:** [github.com/Agentoshi/apow-cli](https://github.com/Agentoshi/apow-cli) | **Protocol:** [github.com/Agentoshi/apow-core](https://github.com/Agentoshi/apow-core)
