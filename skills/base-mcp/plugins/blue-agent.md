---
title: "Blue Agent Plugin"
description: "Skill plugin for running Blue Agent's 33 AI-powered builder tools on Base — market fit analysis, token signals, competitive intelligence, fundraising memos, DeFi opportunities, community growth, agent economy tools, and more — paid automatically via x402 (USDC on Base)."
---

# Blue Agent Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before calling any Blue Agent tool. Blue Agent tools are called directly via HTTP — there is no separate Blue Agent MCP server. Payment for each tool is handled automatically by Base MCP's x402 payment flow.

[Blue Agent](https://blueagent.dev) is the AI founder console for Base builders. It provides 33 pay-per-use intelligence tools powered by a 3-agent collab (Blue Agent · Aeon · MiroShark) — covering market analysis, fundraising, token launches, competitive intelligence, DeFi opportunities, agent economy, community growth, and builder scores. Each tool is exposed as an x402 API: pay in USDC on Base, get a structured JSON response.

No additional MCP server is required. Calls go directly to the x402 endpoint; Base MCP's x402 payment capability handles the USDC charge.

**Prerequisite:** All tools require POST requests with a JSON body — they are **not** viable on consumer Claude or ChatGPT surfaces without a harness HTTP tool. If no harness HTTP tool is available (Claude Code, Cursor, Codex, etc.), tell the user they need a CLI harness.

**Chain:** Base mainnet (chainId `8453`)  
**Payment:** USDC on Base, charged per call via x402  
**API docs:** [blueagent.dev/api-docs](https://blueagent.dev/api-docs)

---

## API

Base URL: `https://x402.bankr.bot/0xf31f59e7b8b58555f7871f71973a394c8f1bffe5`

All endpoints accept `POST` with `Content-Type: application/json`. The x402 payment is made automatically by Base MCP before the tool responds.

### Full Tool Catalog

#### Intelligence & Market

| Tool | Endpoint | Price | Key inputs |
|------|----------|-------|------------|
| Market Fit Validator | `/market-fit` | $0.35 | `description`, `name?`, `stage?` |
| Token Pick Signal | `/token-pick-signal` | $0.20 | `chain?`, `min_mcap?`, `context?` |
| Narrative Position | `/narrative-position` | $0.25 | `topic?`, `focus?` |
| Token Momentum Scanner | `/token-momentum-scanner` | $0.25 | `chain?`, `min_mcap?` |
| Ecosystem Digest | `/ecosystem-digest` | $0.20 | _(none required)_ |
| Community Sentiment | `/community-sentiment` | $0.25 | `project?`, `description?` |

#### Builder & Fundraising

| Tool | Endpoint | Price | Key inputs |
|------|----------|-------|------------|
| Builder Deep DD | `/builder-deep-dd` | $1.00 | `target`, `type?`, `context?` |
| Competitor Scan | `/competitor-scan` | $0.75 | `project`, `competitors?`, `description?` |
| Investor Memo | `/investor-memo` | $0.75 | `project`, `description`, `ask?`, `stage?`, `traction?` |
| Fundraise Timing | `/fundraise-timing` | $0.50 | `project?`, `description?`, `ask?`, `stage?` |
| Pitch Intelligence | `/pitch-intelligence` | $0.35 | `project?`, `description?`, `pitch_summary?`, `ask?`, `stage?` |
| Base Grant Finder | `/base-grant-finder` | $0.35 | `project?`, `description?`, `stage?`, `sector?` |
| Repo Health | `/repo-health` | $0.35 | `repo?`, `description?` |
| Builder Brand Score | `/builder-brand-score` | $0.35 | `builder?`, `project?`, `handle?` |
| Base Builder Network Match | `/base-builder-network-match` | $0.35 | `builder?`, `project?`, `looking_for?`, `skills?` |

#### Product & Launch

| Tool | Endpoint | Price | Key inputs |
|------|----------|-------|------------|
| Token Launch Readiness | `/token-launch-readiness` | $0.50 | `name?`, `project?`, `ticker?`, `description?`, `traction?` |
| Stack Recommender | `/stack-recommender` | $0.35 | `project?`, `description?`, `team_size?`, `timeline?` |
| Roadmap Validator | `/roadmap-validator` | $0.50 | `project?`, `roadmap?`, `timeline?` |
| GTM Brief | `/gtm-brief` | $0.50 | `project?`, `description?`, `target?` |
| Token Distribution Plan | `/token-distribution-plan` | $0.35 | `token?`, `ticker?`, `total_supply?`, `description?` |
| Thread Intelligence | `/thread-intelligence` | $0.35 | `topic?`, `audience?`, `goal?` |
| Community Growth Playbook | `/community-growth-playbook` | $0.50 | `project?`, `description?`, `current_size?`, `goal?` |

#### DeFi & Trading

| Tool | Endpoint | Price | Key inputs |
|------|----------|-------|------------|
| DeFi Opportunity | `/defi-opportunity` | $0.35 | `strategy?`, `risk_tolerance?` |
| Portfolio Rebalancer | `/portfolio-rebalancer` | $0.50 | `holdings?`, `risk_profile?`, `goal?` |
| Wallet Strategy Analyzer | `/wallet-strategy-analyzer` | $0.50 | `address?`, `focus?` |
| Whale Copy Signal | `/whale-copy-signal` | $0.35 | `token?`, `wallet?` |
| Protocol Risk Monitor | `/protocol-risk-monitor` | $0.35 | `protocol?`, `position?` |
| Base Protocol Comparison | `/base-protocol-comparison` | $0.50 | `protocol_a?`, `protocol_b?`, `category?`, `use_case?` |

#### Agent Economy

| Tool | Endpoint | Price | Key inputs |
|------|----------|-------|------------|
| Agent Revenue Optimizer | `/agent-revenue-optimizer` | $0.50 | `agent?`, `description?`, `current_revenue?`, `model?` |
| Agent Token Strategy | `/agent-token-strategy` | $0.50 | `agent?`, `description?`, `token_name?`, `total_supply?` |
| Agent Collab Match | `/agent-collab-match` | $0.35 | `agent_a?`, `agent_b?`, `collab_goal?` |
| Agent Performance | `/agent-performance` | $0.35 | `handle?`, `repo?` |
| Multi-Agent Workflow | `/multi-agent-workflow` | $0.50 | `goal?`, `agents?`, `constraints?` |

---

## Key Tool Details

### `POST /market-fit` — $0.35

GO / WAIT / PIVOT verdict for a project idea. Blue Agent expands the brief, Aeon analyzes narrative positioning, MiroShark scores across 4 personas (Analyst 1.8×, Influencer 2.8×, Retail 1.0×, Observer 0.5×).

**Request:**
```json
{ "description": "Decentralized reputation engine for Base builders", "name": "BuilderScore", "stage": "idea" }
```

**Response:**
```json
{
  "verdict": "GO",
  "score": 74,
  "summary": "...",
  "dimensions": { "market_timing": 18, "differentiation": 16, "base_fit": 20, "execution_risk": 12, "community_pull": 8 },
  "risks": ["..."],
  "next_actions": ["..."]
}
```

---

### `POST /token-pick-signal` — $0.20

One actionable token pick with retail consensus. Aeon scans movers + narrative setups; MiroShark applies retail + analyst personas.

**Request:**
```json
{ "chain": "base", "min_mcap": 1000000, "context": "asymmetric setups under $10M mcap" }
```

**Response:**
```json
{ "pick": "TOKEN", "address": "0x...", "mcap": "$8M", "thesis": "...", "entry": "...", "target": "...", "risk": "HIGH|MEDIUM|LOW", "consensus": "BULL|BEAR|NEUTRAL", "confidence": 72 }
```

---

### `POST /narrative-position` — $0.25

Current CT narrative map with FRONT-RUN / RIDE / FADE / IGNORE calls.

**Request:**
```json
{ "topic": "AI agents on Base" }
```

**Response:**
```json
{ "narratives": [{ "name": "Agent Economy", "position": "FRONT-RUN", "momentum": "rising", "rationale": "..." }], "summary": "..." }
```

---

### `POST /builder-deep-dd` — $1.00

Comprehensive due diligence on a builder, agent, or project. Aeon deep-research ×2 + Blue audit + MiroShark analyst.

**Request:**
```json
{ "target": "jessepollak", "type": "builder", "context": "Base ecosystem contributions" }
```

`type`: `"builder"` | `"project"` | `"agent"` (default: `"project"`)

---

### `POST /investor-memo` — $0.75

Full investor memo: market framing, investment grade (A–D), VC targets, competitive landscape.

**Request:**
```json
{ "project": "BuilderScore", "description": "Reputation engine for Base builders", "ask": "$500K", "stage": "pre-seed", "traction": "120 DAU, 3 integrations" }
```

---

### `POST /defi-opportunity` — $0.35

Current DeFi opportunities on Base: yield farming, lending, LP positions, and asymmetric setups.

**Request:**
```json
{ "strategy": "yield farming", "risk_tolerance": "medium" }
```

---

### `POST /agent-revenue-optimizer` — $0.50

Revenue model analysis for AI agents: pricing, monetization strategies, x402 integration, token model options.

**Request:**
```json
{ "agent": "Blue Agent", "description": "AI founder console for Base builders", "current_revenue": "$2K/month via x402", "model": "pay-per-use" }
```

---

## Orchestration

### x402 payment flow

```text
1. Identify the right tool from the user's request (see routing table below)
2. Tell the user: tool name + price ("Market Fit Validator — $0.35 USDC")
3. Wait for explicit confirmation before making the paid call
4. POST to the endpoint with the required body (use harness HTTP tool)
5. Parse the JSON response and present results
```

Do not chain multiple paid calls without per-call confirmation. Each POST charges the user's Base Account separately.

### Tool routing

| User request | Tool |
|---|---|
| "validate my idea", "PMF check", "go or no-go" | `/market-fit` |
| "what token should I buy", "asymmetric play" | `/token-pick-signal` |
| "scan top movers", "what's pumping" | `/token-momentum-scanner` |
| "what narratives are running on CT" | `/narrative-position` |
| "what happened in Base this week" | `/ecosystem-digest` |
| "what does CT think about my project" | `/community-sentiment` |
| "research this builder / project", "DD on X" | `/builder-deep-dd` |
| "write an investor memo", "fundraising narrative" | `/investor-memo` |
| "when should I raise", "fundraise timing" | `/fundraise-timing` |
| "scan my competitors" | `/competitor-scan` |
| "help me pitch to VCs", "pitch deck help" | `/pitch-intelligence` |
| "find grants for my project" | `/base-grant-finder` |
| "is my GitHub healthy" | `/repo-health` |
| "am I ready to launch my token" | `/token-launch-readiness` |
| "what stack should I use" | `/stack-recommender` |
| "validate my roadmap" | `/roadmap-validator` |
| "write my GTM plan" | `/gtm-brief` |
| "design my token distribution" | `/token-distribution-plan` |
| "help me write a thread" | `/thread-intelligence` |
| "how do I grow my community" | `/community-growth-playbook` |
| "find DeFi opportunities", "best yields on Base" | `/defi-opportunity` |
| "rebalance my portfolio" | `/portfolio-rebalancer` |
| "analyze my wallet strategy" | `/wallet-strategy-analyzer` |
| "copy this whale", "what's whale X buying" | `/whale-copy-signal` |
| "monitor this protocol for risk" | `/protocol-risk-monitor` |
| "compare protocol A vs B" | `/base-protocol-comparison` |
| "optimize my agent's revenue" | `/agent-revenue-optimizer` |
| "design my agent's token strategy" | `/agent-token-strategy` |
| "should agents X and Y collaborate" | `/agent-collab-match` |
| "score my agent's performance" | `/agent-performance` |
| "design a multi-agent workflow" | `/multi-agent-workflow` |
| "find builders to work with" | `/base-builder-network-match` |
| "score my builder brand" | `/builder-brand-score` |

---

## Example Prompts

**Validate my project idea**
> "Validate my idea: gig marketplace for Base builders with USDC escrow and onchain reputation."

1. Confirm: "Market Fit Validator — $0.35 USDC. Proceed?"
2. `POST /market-fit` with `description` from the user.
3. Present: verdict (GO/WAIT/PIVOT), score out of 100, risks, next actions.

**Get a token pick**
> "Give me a token pick on Base under $10M mcap."

1. Confirm: "Token Pick Signal — $0.20 USDC. Proceed?"
2. `POST /token-pick-signal` with `chain: "base"`, `min_mcap: 1000000`, and any user context.
3. Present: pick, thesis, entry, risk, consensus score.

**Research a builder**
> "Do a deep DD on @jessepollak."

1. Confirm: "Builder Deep DD — $1.00 USDC. Proceed?"
2. `POST /builder-deep-dd` with `target: "jessepollak"`, `type: "builder"`.
3. Present: builder score, tier, strengths, risks, verdict.

**Write an investor memo**
> "Write an investor memo for my project. We're raising $500K pre-seed. 3 integrations live."

1. Confirm: "Investor Memo — $0.75 USDC. Proceed?"
2. `POST /investor-memo` with `project`, `description`, `ask`, `stage`, `traction`.
3. Present: investment grade, memo, VC targets.

**Find DeFi opportunities**
> "What are the best yield opportunities on Base right now for medium risk?"

1. Confirm: "DeFi Opportunity — $0.35 USDC. Proceed?"
2. `POST /defi-opportunity` with `strategy: "yield farming"`, `risk_tolerance: "medium"`.
3. Present: current opportunities with APY estimates and protocol names.

**Optimize agent revenue**
> "How should Blue Agent monetize better? We're doing $2K/month via x402."

1. Confirm: "Agent Revenue Optimizer — $0.50 USDC. Proceed?"
2. `POST /agent-revenue-optimizer` with `agent`, `description`, `current_revenue`, `model`.
3. Present: pricing recommendations, monetization strategies, token model options.

---

## Safety Notes

- **Always confirm price before calling.** Every tool charges USDC from the user's Base Account. Show the tool name and USD price and wait for explicit "yes" before POST-ing.
- **One confirmation per call.** Do not bundle multiple tools into a single "yes" — each is a separate charge.
- **POST only — requires harness.** All Blue Agent tools require POST with a JSON body. Consumer Claude/ChatGPT without a harness HTTP tool cannot call them. If no HTTP tool is available, tell the user they need Claude Code, Cursor, or Codex.
- **Results are AI-generated.** Blue Agent responses are LLM synthesis of real signals — not financial advice. Remind the user before acting on token pick, DeFi opportunity, or investment-grade outputs.
- **Token picks are not endorsements.** `/token-pick-signal` and `/token-momentum-scanner` outputs reflect AI narrative analysis. Low-liquidity tokens carry high risk.
- **Wallet analysis requires user consent.** `/wallet-strategy-analyzer` and `/whale-copy-signal` involve wallet addresses — confirm the user wants their address analyzed before calling.

---

## Notes

- USDC on Base: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- All prices are in USD, paid in USDC on Base (chainId `8453`)
- Full tool list and docs: [blueagent.dev/api-docs](https://blueagent.dev/api-docs)
- X/Twitter: [@blueagent_](https://x.com/blueagent_)
