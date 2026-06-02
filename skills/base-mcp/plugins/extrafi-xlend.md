---
title: "Extra Finance xLend Plugin"
description: "Skill plugin reference for lending on Extra Finance xLend using extrafi-prepare CLI."
---

# Extra Finance xLend Plugin

> [!IMPORTANT]
> Complete the short Base MCP onboarding flow defined in `SKILL.md` before calling any Extra Finance xLend command. Fetch the user's wallet address only when a flow actually needs it, such as position reads or write preparation.

Extra Finance xLend is an Aave V3-forked lending market on Base. Use the Extra Finance preparation CLI (`npx extrafi-prepare`) to query protocol state, check rates/positions, and prepare unsigned transaction batches, then execute them via `send_calls`.

No additional MCP server required — everything goes through `npx extrafi-prepare` + `send_calls`.

**Supported chains:** Base (8453).

---

## Orchestration Pattern

```
get_wallets -> user address
extrafi-prepare read command -> query market rates/positions
extrafi-prepare prepare command -> PreparedOperation JSON
review summary, simulationOk, outcome, warnings, transactions
send_calls(chain="base", calls from transactions[]) -> approval URL + request ID
user approves
get_request_status(request ID) -> confirmed
```

`extrafi-prepare` commands simulate by default. Check `simulationOk` before presenting an approval link. If `simulationOk` is `false`, inspect and report the revert reason instead of submitting the batch.

---

## Read Commands (use run_command)

Query the protocol state and user positions using the following read commands:

```bash
# Read protocol market rates and APYs
npx extrafi-prepare rates

# Read single reserve details (USDC, WETH, wstETH, cbETH, cbBTC)
npx extrafi-prepare single-reserve --asset USDC

# Read user positions, health factor, and collateral details
npx extrafi-prepare positions --from <address>
```

Market reads return active reserves, collateral factors, borrow/supply APYs, and total TVL.

---

## Prepare Commands (use run_command → send_calls)

Verbs: `supply`, `withdraw`, `borrow`, `repay`.

```bash
# Prepare a supply operation
npx extrafi-prepare supply --asset USDC --amount 100 --from <address>

# Prepare a withdrawal operation
npx extrafi-prepare withdraw --asset USDC --amount 50 --from <address>

# Prepare a borrow operation
npx extrafi-prepare borrow --asset USDC --amount 25 --from <address>

# Prepare a repay operation
npx extrafi-prepare repay --asset USDC --amount 25 --from <address>
```

### Key parameters

| Field | Notes |
|-------|-------|
| `--asset` | Symbol: `USDC`, `WETH`, `wstETH`, `cbETH`, `cbBTC` |
| `--amount` | Human-readable string, e.g. `100` |
| `--from` | User's wallet address (from `get_wallets`) |

### Response → send_calls mapping

`extrafi-prepare` outputs a JSON payload with a `transactions` array:

```json
{
  "simulationOk": true,
  "transactions": [
    { "step": "approve", "to": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "data": "0x095d1a5b...", "value": "0x0" },
    { "step": "supply",  "to": "0x...", "data": "0x6156e79f...", "value": "0x0" }
  ]
}
```

Map these transactions directly to Base MCP's `send_calls` command:

```json
{
  "chain": "base",
  "calls": [
    {
      "to": "<transaction.to>",
      "value": "<transaction.value or 0x0>",
      "data": "<transaction.data>"
    }
  ]
}
```

---

## Example Flows

### Supply 100 USDC on Base xLend

```
1. get_wallets → address
2. Run: npx extrafi-prepare supply --asset USDC --amount 100 --from <address>
3. Check JSON: simulationOk is true
4. send_calls(chain="base", calls from transactions[])
5. User approves → get_request_status(requestId)
```

### Borrow USDC against collateral

```
1. get_wallets → address
2. Run: npx extrafi-prepare positions --from <address> → verify health factor > 1.5
3. Run: npx extrafi-prepare borrow --asset USDC --amount 50 --from <address>
4. Check JSON: simulationOk is true
5. send_calls(chain="base", calls from transactions[])
6. User approves → get_request_status(requestId)
```

### Check positions and health factor

```
1. get_wallets → address
2. Run: npx extrafi-prepare positions --from <address>
3. Show supply balances, borrow balances, and health factor
```

---

## Protocol Notes

- **Collateral Enablement** — Supplying assets automatically sets them as collateral unless the reserve's loan-to-value (LTV) is 0.
- **Liquidation Threshold** — The max borrow capacity is determined by the weighted average collateral factor of supplied assets.
- **WETH/ETH** — Native ETH is supported; the runner handles wrapping/unwrapping internally.

### Health factor guide

| Value | Status |
|-------|--------|
| `> 1.5` | Healthy |
| `1.1 – 1.5` | Caution |
| `< 1.1` | Liquidation risk |
| `null / 0` | No active borrows |
