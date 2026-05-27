---
title: "Blue Agent Plugin"
description: "Skill plugin for running Blue Agent's AI-powered builder tools on Base — market fit analysis, token pick signals, competitive intelligence, investor memos, and more — paid automatically via x402 (USDC on Base)."
---

# Blue Agent Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before calling any Blue Agent tool. Blue Agent tools are called directly via HTTP — there is no separate Blue Agent MCP server. Payment for each tool is handled automatically by Base MCP's x402 payment flow.

[Blue Agent](https://blueagent.dev) is the AI founder console for Base builders. It provides a suite of pay-per-use intelligence tools powered by a 3-agent collab (Blue Agent · Aeon · MiroShark) — covering market analysis, fundraising, token launches, competitive intelligence, and builder scores. Each tool is exposed as an x402 API: pay in USDC on Base, get a structured JSON response.

No additional MCP server is required. Calls go directly to the x402 endpoint; Base MCP's x402 payment capability handles the USDC charge.

**Prerequisite:** `x402.bankr.bot` must be reachable from your harness. All tools require POST requests with a JSON body — they are **not** viable on consumer Claude or ChatGPT surfaces without a harness HTTP tool. If no harness HTTP tool is available, tell the user they need Claude Code, Cursor, or a similar environment.

**Chain:** Base mainnet (chainId `8453`)  
**Payment:** USDC on Base, charged per call via x402

---

## API

Base URL: `https://x402.bankr.bot/0xf31f59e7b8b58555f7871f71973a394c8f1bffe5`

All endpoints accept `POST` with `Content-Type: application/json`. The x402 payment is made automatically by Base MCP before the tool responds. Parameters can also be passed as query strings for GET-style calls where supported.

### Tools

| Tool | Endpoint | Price | Input |
|------|----------|-------|-------|
| Market Fit Validator | `/market-fit` | $0.35 | `description`, `name?`, `stage?` |
| Token Pick Signal | `/token-pick-signal` | $0.20 | `chain?`, `context?` |
| Narrative Position | `/narrative-position` | $0.25 | `topic?` |
| Ecosystem Digest | `/ecosystem-digest` | $0.20 | _(no required fields)_ |
| Builder Deep DD | `/builder-deep-dd` | $1.00 | `target`, `type?`, `context?` |
| Competitor Scan | `/competitor-scan` | $0.75 | `project`, `competitors?`, `description?` |
| Investor Memo | `/investor-memo` | $0.75 | `project`, `description`, `ask?`, `stage?`, `traction?` |
| Token Launch Readiness | `/token-launch-readiness` | $0.50 | `description`, `name?`, `stage?` |
| Stack Recommender | `/stack-recommender` | $0.35 | `description`, `name?` |
| Roadmap Validator | `/roadmap-validator` | $0.50 | `description`, `roadmap?` |
| Pitch Intelligence | `/pitch-intelligence` | $0.35 | `project`, `description?` |

---

## Tool Details

### `POST /market-fit` — $0.35

GO / WAIT / PIVOT verdict for a project idea. Blue Agent expands the brief, Aeon analyzes narrative positioning, MiroShark scores across 4 personas (Analyst, Influencer, Retail, Observer).

**Request body:**
```json
{
  "description": "A decentralized reputation engine for Base builders that scores onchain activity and social credibility",
  "name": "BuilderScore",
  "stage": "idea"
}
```

**Response shape:**
```json
{
  "verdict": "GO",
  "score": 74,
  "summary": "Strong narrative fit with Base ecosystem growth...",
  "dimensions": {
    "market_timing": 18,
    "differentiation": 16,
    "base_fit": 20,
    "execution_risk": 12,
    "community_pull": 8
  },
  "risks": ["<risk>"],
  "next_actions": ["<action>"]
}
```

---

### `POST /token-pick-signal` — $0.20

One actionable token pick with retail consensus. Aeon scans top movers and narrative setups; MiroShark applies retail + analyst personas to reach a consensus pick.

**Request body:**
```json
{
  "chain": "base",
  "context": "looking for asymmetric setups under $10M mcap"
}
```

**Response shape:**
```json
{
  "pick": "TOKEN",
  "address": "0x...",
  "mcap": "$8M",
  "thesis": "...",
  "entry": "current price or venue",
  "target": "...",
  "risk": "HIGH|MEDIUM|LOW",
  "consensus": "BULL|BEAR|NEUTRAL",
  "confidence": 72
}
```

---

### `POST /narrative-position` — $0.25

Current narrative map with position calls: FRONT-RUN / RIDE / FADE / IGNORE. Aeon tracks narrative momentum on CT; Blue Agent synthesizes the position table.

**Request body:**
```json
{
  "topic": "AI agents on Base"
}
```

**Response shape:**
```json
{
  "narratives": [
    {
      "name": "Agent Economy",
      "position": "FRONT-RUN",
      "momentum": "rising",
      "rationale": "..."
    }
  ],
  "summary": "..."
}
```

---

### `POST /ecosystem-digest` — $0.20

Weekly Base ecosystem recap — top launches, trending builders, protocol updates, narrative shifts. No required fields.

**Request body:** `{}` (or omit body)

**Response shape:**
```json
{
  "week": "2026-W21",
  "top_launches": ["..."],
  "trending_builders": ["..."],
  "protocol_updates": ["..."],
  "narrative_shift": "...",
  "summary": "..."
}
```

---

### `POST /builder-deep-dd` — $1.00

Comprehensive due diligence on a builder, agent, or project. Aeon runs deep research x2 (product + background), Blue Agent audits, MiroShark provides analyst perspective.

**Request body:**
```json
{
  "target": "vitalik.eth",
  "type": "builder",
  "context": "focus on Base ecosystem contributions"
}
```

`type` accepts: `"builder"` | `"project"` | `"agent"` (default: `"project"`)

**Response shape:**
```json
{
  "target": "vitalik.eth",
  "score": 91,
  "tier": "Founder",
  "research": "...",
  "strengths": ["..."],
  "risks": ["..."],
  "verdict": "..."
}
```

---

### `POST /investor-memo` — $0.75

Full investor memo: market framing, why this wins, traction, competitive landscape, investment grade (A–D), and VC targets.

**Request body:**
```json
{
  "project": "BuilderScore",
  "description": "Reputation engine for Base builders scoring onchain + social credibility",
  "ask": "$500K",
  "stage": "pre-seed",
  "traction": "120 DAU, 3 protocol integrations"
}
```

**Response shape:**
```json
{
  "investment_grade": "B",
  "memo": "...",
  "key_strengths": ["..."],
  "key_risks": ["..."],
  "comparable": "Gitcoin Passport",
  "analyst_verdict": "...",
  "vc_targets": ["..."]
}
```

---

### `POST /competitor-scan` — $0.75

Competitive intelligence: strengths, weaknesses, differentiation matrix, and strategic recommendations.

**Request body:**
```json
{
  "project": "BuilderScore",
  "description": "Reputation engine for Base builders",
  "competitors": ["Gitcoin Passport", "Talent Protocol", "Layer3"]
}
```

---

### `POST /token-launch-readiness` — $0.50

Pre-launch readiness score + GO/WAIT verdict + prioritized action checklist for a token launch on Base.

**Request body:**
```json
{
  "description": "A reputation token for Base builders rewarding onchain contributions",
  "name": "$BUILD",
  "stage": "pre-launch"
}
```

---

## Orchestration

### x402 payment flow

Blue Agent tools charge per call via x402. The payment is deducted in USDC from the user's Base Account automatically by Base MCP's x402 payment mechanism — no manual payment step is needed. Confirm the tool price with the user before calling.

```text
1. Tell the user the tool name and price ("Market Fit Validator — $0.35")
2. Ask for explicit confirmation before making the paid call
3. POST to the endpoint with the required body (harness HTTP tool)
4. Parse the JSON response
5. Present structured results to the user
```

Do not chain multiple paid calls without per-call user confirmation. Each call charges the user's Base Account.

### Choosing a tool

| User request | Tool |
|---|---|
| "validate my idea", "does this have PMF", "go or no-go" | `/market-fit` |
| "what token should I buy", "find me an asymmetric play" | `/token-pick-signal` |
| "what narratives are running on CT", "what's hot on Base" | `/narrative-position` |
| "give me a weekly recap", "what happened in Base this week" | `/ecosystem-digest` |
| "research this builder / project", "do DD on X" | `/builder-deep-dd` |
| "write me an investor memo", "fundraising narrative" | `/investor-memo` |
| "scan my competitors", "who am I competing against" | `/competitor-scan` |
| "am I ready to launch my token", "token launch checklist" | `/token-launch-readiness` |
| "what tech stack should I use", "recommend a stack" | `/stack-recommender` |
| "validate my roadmap", "is my roadmap realistic" | `/roadmap-validator` |

---

## Example Prompts

**Validate my project idea**
> "Validate my idea: a gig marketplace for Base builders where tasks are posted with USDC escrow and reputation is tracked onchain."

1. Confirm: "I'll run Market Fit Validator ($0.35 USDC from your Base Account). Proceed?"
2. On confirmation: `POST /market-fit` with `description` = the idea text.
3. Present: verdict (GO/WAIT/PIVOT), score out of 100, top risks, next actions.

**Get a token pick**
> "Give me a token pick on Base under $10M mcap."

1. Confirm: "I'll run Token Pick Signal ($0.20 USDC). Proceed?"
2. `POST /token-pick-signal` with `chain: "base"` and `context` from the user.
3. Present: pick, thesis, entry, risk rating, consensus score.

**Research a builder**
> "Do a deep DD on @jessepollak — what has he shipped on Base?"

1. Confirm: "Builder Deep DD costs $1.00 USDC. Proceed?"
2. `POST /builder-deep-dd` with `target: "jessepollak"`, `type: "builder"`.
3. Present: builder score, tier, research summary, strengths, risks.

**Write an investor memo**
> "Write an investor memo for my project: decentralized task marketplace for Base builders. We're raising $500K pre-seed. 3 integrations live."

1. Confirm: "Investor Memo costs $0.75 USDC. Proceed?"
2. `POST /investor-memo` with `project`, `description`, `ask`, `stage`, `traction`.
3. Present: investment grade, memo narrative, VC targets.

**Ecosystem digest**
> "What's happening in the Base ecosystem this week?"

1. Confirm: "Ecosystem Digest costs $0.20 USDC. Proceed?"
2. `POST /ecosystem-digest` with empty body.
3. Present: top launches, trending builders, narrative shift summary.

---

## Safety Notes

- **Always confirm price before calling.** Every tool charges USDC from the user's Base Account. Show the tool name and price and wait for explicit "yes" before POST-ing.
- **One confirmation per call.** Do not bundle multiple tools into a single confirmation — each call is a separate charge.
- **POST only.** All Blue Agent tools require POST with a JSON body. They cannot be called from consumer Claude/ChatGPT surfaces without a harness HTTP tool (Claude Code, Cursor, Codex, etc.). If no HTTP tool is available, tell the user they need a CLI harness.
- **Results are AI-generated.** Blue Agent responses are LLM synthesis of real signals — not financial advice. Remind the user of this before acting on token pick or investment-grade outputs.
- **Token picks are not endorsements.** The `/token-pick-signal` output reflects AI narrative analysis, not investment advice. Low-liquidity tokens carry high risk.

---

## Notes

- USDC on Base: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- All prices are in USD, paid in USDC on Base (chainId `8453`)
- Full tool list and docs: [blueagent.dev/api-docs](https://blueagent.dev/api-docs)
- X/Twitter: [@blocky_agent](https://x.com/blocky_agent)
- Built by [Blocky Studio](https://blocky.studio)
