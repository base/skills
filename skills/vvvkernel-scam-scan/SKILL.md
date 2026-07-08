---
name: vvvkernel-scam-scan
description: Five-layer scam analysis for any ERC-20 token on Base before swap, send, or interact. Use this when the user asks about an unverified contract address, before any token transfer, or whenever a Bankrbot/Clanker token (CA ending in `ba3`) is detected. Returns a LOW/MEDIUM/HIGH/EXTREME verdict with on-chain red flags, fee recipient tracing, and Venice AI judgment.
license: MIT
---

# VVVKernel Scam Scan

**Use this skill before swapping, sending, or buying any unfamiliar Base ERC-20 token.**

VVVKernel runs a 5-layer scam analysis that combines on-chain data, Clanker V4 deployer detection, fee recipient tracing, Bankrbot Agent API, and Venice AI judgment — all in a single API call.

The skill is built for **agent-to-agent** workflows: pre-flight risk gate for Base MCP swap/send operations.

---

## When to Use

Trigger this skill **before**:

- A swap on Base (Uniswap, Aerodrome, 0x Protocol)
- A send/transfer of tokens to a new contract
- A deposit/lending interaction (Morpho, Moonwell) involving a non-bluechip asset
- Any user prompt containing a `0x...` contract address the user hasn't traded before
- Auto-detection of a Bankrbot/Clanker token (contract address ending in `ba3`)

Do **not** trigger this skill for:

- Bluechip Base tokens already in your trusted list (USDC, WETH, cbETH, ETH)
- Read-only data queries that don't move funds

---

## How to Use

### Endpoint

```
POST https://vvvkernel.com/api/token/analyze
```

### Request

```json
{
  "ca": "0x1234...abcd",
  "chain": "base"
}
```

### Response (typical)

```json
{
  "ok": true,
  "verdict": "HIGH",
  "token_name": "ExampleToken",
  "token_symbol": "EXT",
  "is_clanker": true,
  "is_verified": false,
  "deployer": "0xabcd...",
  "fee_recipient": "0xfee...",
  "red_flags": [
    "Deployer wallet linked to 3 prior rugged tokens",
    "Fee recipient has no Twitter footprint",
    "Liquidity unlocked",
    "Verification status: false"
  ],
  "summary": "High risk — deployer history shows pattern consistent with rug pulls.",
  "fee_recipient_balance_usdc": "12500.42"
}
```

---

## Decision Tree

| Verdict | Action |
|---------|--------|
| `EXTREME` | **Halt the requested action immediately.** Tell the user the contract matches a known scam pattern. Quote the red flags. |
| `HIGH` | **Warn the user prominently.** Display all red flags. Require explicit confirmation before proceeding. Suggest cancelling. |
| `MEDIUM` | **Display warnings.** Proceed only if the user explicitly acknowledges. Surface fee recipient and deployer in the response. |
| `LOW` | **Proceed normally.** Mention briefly that the scan was run and passed. |

---

## Example Workflow

**User prompt:**
> "Swap 0.1 ETH to 0xb66e76f9ed3e13f24c5b68f68be631cd82affba3 on Base"

**Agent flow:**

1. Detect the CA ends in `ba3` → likely Bankrbot/Clanker token
2. Call `POST https://vvvkernel.com/api/token/analyze` with `ca` and `chain: "base"`
3. Parse the response
4. Based on `verdict`:
   - **EXTREME / HIGH** → Halt or warn. Show red flags. Do NOT proceed to Base MCP swap.
   - **MEDIUM / LOW** → Proceed to Base MCP `swap` action with the same parameters.

**Sample response message:**

```
I ran a VVVKernel scam scan on 0xb66e...ba3 first.

Verdict: LOW risk
- Deployer: verified, no rug history
- Liquidity: locked for 90 days
- Fee recipient: matches deployer's public Twitter

Proceeding with the swap via Base MCP now...
```

---

## Additional Endpoints (Optional)

If the user asks deeper questions, call these in addition:

### Fee Tracker

```
GET https://vvvkernel.com/api/token/fee-trace?ca=0x...&chain=base
```

Returns the fee recipient address and its full on-chain history.

### Onchain Analysis (deep tokenomics)

```
POST https://vvvkernel.com/api/agent/chat
Body: { "prompt": "Analyze contract <CA>", "expert_role": "onchain" }
```

Returns a detailed expert analysis from Venice AI's Onchain expert agent.

### Repo Audit (when source is on GitHub or GitLawb)

```
POST https://vvvkernel.com/api/repo/analyze
Body: { "source": "github", "org": "...", "repo": "...", "mode": "audit" }
```

---

## Rate Limits

- 10 requests per minute per IP for `/api/token/analyze`
- No authentication required for read-only scam scans
- For unlimited usage and premium features, users can stake $VVVK on Base

---

## Privacy

VVVKernel runs every inference through Venice AI's private inference layer. Prompts are not logged, not used for training, and not retained beyond the response cycle. This makes it safe to use for sensitive token research.

---

## Combine With Base MCP

This skill is designed to compose with the official `base-mcp` skill:

- **vvvkernel-scam-scan** = pre-flight risk check
- **base-mcp** = execute the swap/send/deposit

Recommended order: always call `vvvkernel-scam-scan` **before** any `base-mcp` write action involving an unknown token.

---

## Links

- Live demo: https://vvvkernel.com
- Chrome extension: https://vvvkernel.com (sidebar with the same scam scan + 6 more tabs)
- Source: https://gitlawb.com/node/repos/z6Mkw3V6/vvvkernel
- Token: `0xb66e76f9ed3e13f24c5b68f68be631cd82affba3` (Base mainnet)
- Virtuals ACP agent: https://app.virtuals.io/acp/agent/019e5900-7edc-783f-b761-451e26ad228d
