---
title: "CTRL Plugin"
description: "Skill plugin reference for composing recurring on-chain workflows on Base via CTRL — sign once, the keeper executes triggers and actions under pre-authorized vault caps forever."
---

# CTRL Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before calling any CTRL flow. CTRL is a workflow automation surface — the user signs ONE EIP-5792 batch to deploy an audited vault and register spending caps, and the CTRL keeper then executes triggers autonomously under those caps. The activation batch is meant to be passed to Base MCP's `send_calls`; CTRL itself does not require a separate MCP server.

[CTRL](https://ctrl.build) lets users compose **trigger → action → condition → utility** workflows in natural language and deploy them on-chain on Base. Representative prompts the user might give the agent:

- "DCA $50 ETH into USDC every Monday at 14:00 UTC."
- "Snipe new Flaunch token launches with `milady` in the name for 0.005 ETH each, auto-sell at 2x into USDC."
- "Mirror wallet `0x6cc5...c01b` — when they buy anything over $10k, copy with 0.01 ETH of my own."
- "Sell 50% of $PEPE if the price drops 20% in an hour."

Workflows run against an audited V3 vault (`0x5Df25e79efd7f9dc86841b404b3EA6F4b7951DBB` on Base) that enforces `maxPerSwap` and `maxPerDay` caps the user signs ONCE. A keeper fleet polls every ~5 seconds and executes only when the trigger conditions are met and the on-chain caps allow it. After the activation signature, no further user interaction is required.

**Prerequisite:** `ctrl.build` must be on the Base MCP `web_request` allowlist. If requests are rejected, inform the user and fall back to the harness's HTTP/fetch tool if one is available.

**Chain:** Base mainnet (chainId `8453` / `0x2105`).

**Auth:** Public. No API key required. The wallet signature at activation is the sole security boundary — the first wallet to sign the EIP-5792 batch claims the workflow. Drafts that are never activated auto-prune after 30 days. Rate limits (per-IP) bound anonymous abuse: 10 creates per 10 min, 5 activate-prepares per 10 min, 60 reads per minute.

---

## Flow Overview

1. Call `GET /api/mcp/block-catalog` to discover the live list of block ids and the `fields[]` schema each block accepts.
2. Call `POST /api/mcp/workflows` with the assembled `workflow_data` — no auth header required. Returns a `workflowId`.
3. Call `POST /api/mcp/activate/{workflowId}` with the user's wallet in headers + `maxPerSwapEth` / `maxPerDayEth` / `depositEth` in the body. Returns an EIP-5792 `calls[]` batch.
4. Pass `calls` + `chainId` to Base MCP's `send_calls`. The user signs once in Base Account; the vault deploys + the rule registers in a single batch.
5. Optionally call `GET /api/mcp/execution-logs?workflow_id={id}` to surface keeper history back to the user.

---

## API

Base URL: `https://ctrl.build/api/mcp`

### `GET /block-catalog`

Returns the live catalog of every available block. No auth, no query parameters. ~50 KB JSON.

```json
{
  "triggers": [
    {
      "id": "time.interval",
      "label": "Interval Timer",
      "category": "trigger",
      "fields": [
        { "key": "everyMinutes", "type": "number", "label": "Every (minutes)", "default": 1440 }
      ]
    }
    // 8 more triggers
  ],
  "actions": [
    {
      "id": "cypher.swap",
      "label": "Swap",
      "fields": [
        { "key": "tokenIn", "type": "string", "default": "ETH" },
        { "key": "tokenOut", "type": "string" },
        { "key": "amount", "type": "string", "label": "Amount (ETH or token units)" },
        { "key": "slippage", "type": "number", "default": 5 }
        // additional fields for autoSell*, tokenOutMode, etc.
      ]
    }
    // 4 more actions
  ],
  "conditions": [ /* 4 */ ],
  "utilities":  [ /* 5 */ ]
}
```

Field notes:

- `id` — the canonical block identifier. Pass this as `trigger.type` or `chain[].type` in `POST /workflows`.
- `fields[].key` — the EXACT keys you must use in the `config` object you submit. Do not invent fields.
- `fields[].default` — if a field has a default, omitting it is safe; the keeper will substitute the documented value.

### `POST /workflows`

Create a workflow draft. No `Authorization` header required.

```text Request
POST https://ctrl.build/api/mcp/workflows
Content-Type: application/json
```

```json
{
  "name": "DCA ETH → USDC weekly",
  "description": "Buy $50 of ETH every Monday at 14:00 UTC.",
  "workflow_data": {
    "nodes": [
      { "id": "t1", "type": "trigger",  "blockType": "trigger", "blockSubtype": "time.interval", "data": { "everyMinutes": 10080, "alignedTo": "monday-14:00-utc" }, "position": { "x": 0,   "y": 0 } },
      { "id": "a1", "type": "action",   "blockType": "action",  "blockSubtype": "cypher.swap",   "data": { "tokenIn": "ETH", "tokenOut": "USDC", "amount": "0.01", "slippage": 5 },  "position": { "x": 220, "y": 0 } }
    ],
    "edges": [ { "id": "e1", "source": "t1", "target": "a1" } ]
  },
  "chain": "base",
  "network": "mainnet"
}
```

```json Response
{
  "workflow": {
    "id": "8c3a2f57-1f1e-4c84-a51f-2b9b6b8b2c10",
    "name": "DCA ETH → USDC weekly",
    "status": "draft",
    "created_at": "2026-06-03T08:14:21.000Z"
  }
}
```

Response notes:

- `workflow.id` — pass this to `POST /activate/{workflowId}` in the next step.
- `workflow.status` — always `"draft"` until the activation batch is signed on-chain.

### `POST /activate/{workflowId}`

Encode the EIP-5792 batch the user signs to deploy their vault + register the workflow's spending rules.

```text Request
POST https://ctrl.build/api/mcp/activate/{workflowId}
Content-Type: application/json
X-Wallet-Address: 0x...
X-Wallet-Signature: 0x...
```

```json
{
  "maxPerSwapEth": "0.01",
  "maxPerDayEth":  "0.1",
  "depositEth":    "0.05",
  "expiryDays":    365
}
```

```json Response
{
  "calls": [
    { "to": "0x5Df25e79efd7f9dc86841b404b3EA6F4b7951DBB", "data": "0x...", "value": "0x..." },
    { "to": "0x<predicted-vault-address>",                "data": "0x...", "value": "0x0" }
  ],
  "chainId": 8453,
  "vaultAddress": "0x..."
}
```

Response notes:

- `calls` + `chainId` — pass directly to Base MCP's `send_calls` to prompt the user signature.
- The batch is one or two calls depending on whether the user already has a vault:
  - **No vault yet:** `[factory.createVaultAndDeposit{value: depositEth}, vault.createRule(...)]`
  - **Existing vault:** `[vault.createRule(...)]`
- The first wallet to sign the batch claims the workflow on-chain; subsequent activate calls from other wallets return `403`.

### `GET /vault-status?wallet=0x...`

Read on-chain vault state for any wallet. Public — no auth.

```text Example
GET https://ctrl.build/api/mcp/vault-status?wallet=0x21a2207b77D06F56Ff93f9d41288a7c4dA081De3
```

```json
{
  "walletAddress": "0x21a2207b77d06f56ff93f9d41288a7c4da081de3",
  "vaultExists": false,
  "vaultAddress": null,
  "predictedVaultAddress": "0x25e911b05C7E3f61769161c3dAA340f7ed6E2651",
  "balances": {
    "ethWei": "0",
    "ethDecimal": "0",
    "wethWei": "0",
    "wethDecimal": "0"
  },
  "activeRules": [],
  "ready": false,
  "warnings": ["Vault not deployed — ctrl_activate will deploy it in the same EIP-5792 batch as the rule"]
}
```

Field notes:

- `predictedVaultAddress` — the deterministic CREATE2 address the vault will land at after activation. Useful for surfacing "after you sign, your vault will live at 0x..." to the user.
- `ready` — `true` only if the vault is deployed AND has either ETH or WETH funded.
- `warnings` — human-readable strings to surface verbatim before the user signs.

### `GET /execution-logs?workflow_id=...`

Read keeper execution history. Public — anyone with the `workflow_id` can read it (same trust posture as on-chain tx visibility).

```text Example
GET https://ctrl.build/api/mcp/execution-logs?workflow_id=8c3a2f57-1f1e-4c84-a51f-2b9b6b8b2c10
```

```json
{
  "logs": [
    {
      "id": "...",
      "workflow_id": "8c3a2f57-...",
      "trigger_type": "time.interval",
      "status": "success",
      "started_at":   "2026-06-03T14:00:01.000Z",
      "completed_at": "2026-06-03T14:00:04.213Z",
      "transaction_hash": "0x...",
      "gas_used": "182394"
    }
  ]
}
```

`transaction_hash` is a BaseScan-linkable tx. Use it to construct `https://basescan.org/tx/0x...` when reporting results.

---

## Available Blocks

The catalog at `/block-catalog` is the source of truth, but for planning purposes the live set is:

**Triggers (9)** — `time.interval`, `trigger.manual`, `price.above`, `price.below`, `price.change`, `pool.created` (Base launchpads: Clanker, Flaunch, Zora, BANKR), `watch.whale`, `event.transfer`, `event.balance`.

**Actions (5)** — `cypher.swap`, `read.balance`, `notify.telegram`, `notify.discord`, `util.webhook`.

**Conditions (4)** — `cond.price`, `cond.balance`, `cond.allowed_weekdays`, `cond.time_window`.

**Utilities (5)** — `util.delay`, `util.note`, `util.log`, `util.stop`, `util.snapshot`.

When the user expresses an exit strategy ("sell at 2x", "stop loss at -20%"), wire the auto-sell config directly onto the `cypher.swap` action:

```json
"data": {
  "tokenIn": "ETH",
  "tokenOut": "{{trigger.tokenAddress}}",
  "tokenOutMode": "dynamic",
  "amount": "0.005",
  "slippage": 15,
  "autoSellEnabled": true,
  "autoSellMode": "multiple",
  "autoSellMultiplier": 2,
  "autoSellPercent": 100,
  "autoSellReceiveToken": "USDC"
}
```

`{{trigger.tokenAddress}}` is a templating directive — the keeper substitutes the actual address from the trigger event at fire time. Use it whenever the action targets the token that triggered the workflow.

---

## Safety

CTRL implements a **vault-direct model** — the agent never holds keys, and the on-chain caps are the unbypassable security boundary.

- **On-chain caps.** Every rule the user signs carries an immutable `maxPerSwap` and `maxPerDay`. The vault contract enforces them; no off-chain check can be circumvented.
- **Kill switches.** `vault.pauseVault()` halts all execution; `vault.revokeRule(ruleId)` kills a single workflow. Both are one-tx, user-callable any time. Surface them to the user when they ask "how do I stop this?".
- **Built-in safety primitives.** The `pool.created` trigger has a `safetyEnabled` flag that runs GoPlus honeypot + tax + score checks before any swap fires. Honeypots and high-tax tokens are auto-rejected without a swap or execution log entry.
- **Keeper bounded.** The keeper fleet can only call vault methods the user pre-authorized. Compromising a keeper wallet costs at most one tick's per-swap cap, not the vault.

When activating, surface the caps to the user verbatim: *"You are about to sign a vault with a max of 0.01 ETH per swap and 0.1 ETH per day. Hit cancel if those are wrong."* The user signs the caps, not just "approval."

---

## Worked Example: DCA $50 ETH → USDC every Monday 14:00 UTC

```text
1. GET https://ctrl.build/api/mcp/block-catalog
   → confirm `time.interval` has fields { everyMinutes, alignedTo }
   → confirm `cypher.swap` has fields { tokenIn, tokenOut, amount, slippage }

2. POST https://ctrl.build/api/mcp/workflows
   {
     "name": "DCA ETH → USDC weekly",
     "workflow_data": {
       "nodes": [
         { "id":"t1", "type":"trigger", "blockType":"trigger", "blockSubtype":"time.interval",
           "data": { "everyMinutes": 10080, "alignedTo": "monday-14:00-utc" },
           "position": { "x": 0, "y": 0 } },
         { "id":"a1", "type":"action", "blockType":"action", "blockSubtype":"cypher.swap",
           "data": { "tokenIn":"ETH", "tokenOut":"USDC", "amount":"0.01", "slippage":5 },
           "position": { "x": 220, "y": 0 } }
       ],
       "edges": [ { "id":"e1", "source":"t1", "target":"a1" } ]
     },
     "chain": "base",
     "network": "mainnet"
   }
   → response { workflow: { id: "<uuid>", status: "draft" } }

3. POST https://ctrl.build/api/mcp/activate/<uuid>
   Headers: X-Wallet-Address: <user wallet>, X-Wallet-Signature: <sig>
   Body: { "maxPerSwapEth": "0.01", "maxPerDayEth": "0.1", "depositEth": "0.05", "expiryDays": 365 }
   → response { calls: [...], chainId: 8453, vaultAddress: "0x..." }

4. Pass `calls` + `chainId` to Base MCP's send_calls.
   → user signs in Base Account → vault deploys + rule registers → keeper armed.

5. Tell the user: "DCA armed. Next swap: Monday 14:00 UTC. View at https://ctrl.build/dashboard/automations."
```

---

## Resources

- App: <https://ctrl.build>
- Docs: <https://ctrl.build/docs>
- MCP hub: <https://ctrl.build/mcp>
- Verified contracts on BaseScan:
  - V13 Vault Factory — <https://basescan.org/address/0x5Df25e79efd7f9dc86841b404b3EA6F4b7951DBB>
  - Vault Implementation — <https://basescan.org/address/0x48d16fe4d11499E6714840e101943F0f2FDacB5a>
  - TimelockBeacon — <https://basescan.org/address/0x5760A6D62743860F27843fA314E22166dBEF7d73>
