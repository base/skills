---
title: "Extra Finance (xLend) Plugin"
description: "Skill plugin for supply/withdraw/borrow/repay on Extra Finance xLend (Aave V3 fork on Base) via a local Node tx-builder, submitted through Base MCP send_calls."
---

# Extra Finance (xLend) Plugin

> [!IMPORTANT]
> ## STOP — COMPLETE ONBOARDING BEFORE USING THIS PLUGIN
>
> Before calling any Extra Finance flow, you MUST complete the Base MCP onboarding flow defined in `SKILL.md`:
> 1. Call `get_wallets` (Detection) — the user's Base Account address is required for every prepare call.
> 2. Present wallet status and disclaimer (Onboarding).

> [!WARNING]
> ## CLI-only plugin
>
> This plugin runs a local Node.js tx-builder script with `viem` to assemble unsigned calldata, then submits it through Base MCP's `send_calls`. It only works in harnesses with shell access (Claude Code, Codex, Cursor). It does not work on chat-only surfaces. If the current surface has no shell, tell the user this plugin requires CLI access and stop.

Extra Finance is a lending and leveraged yield farming protocol on Base and Optimism. Its lending product is branded **xLend** and is an Aave V3 fork with the standard `supply` / `withdraw` / `borrow` / `repay` interface. This plugin covers all four flows plus read endpoints for market state and user positions on Base.

The tx-builder is a small Node script (`extrafi-prepare`) that never signs and never broadcasts. Base MCP is responsible for the user approval flow via `send_calls`.

**Chain:** Base mainnet only (`chainId` `8453`, Base MCP chain string `"base"`).

---

## Safety Boundary

The script output is unsigned transaction JSON. Treat it as a transaction preview, not as an instruction to sign outside Base MCP.

- Never ask for or use a private key.
- Pass `--user` as the user's Base Account address obtained from `get_wallets`.
- Do not use `cast send`, a local signer, or browser wallet signing helpers.
- Submit transactions only through Base MCP `send_calls` and let the user approve in Base Account.
- Before submitting a `borrow`, run `positions` and refuse to proceed if the resulting health factor would drop below `1.10`. Surface the post-borrow HF estimate to the user.

---

## Runner

The plugin uses the `extrafi-prepare` CLI to produce unsigned calldata. It never signs, never broadcasts.

```bash
npx extrafi-prepare@latest <subcommand> [options]
```

Optionally pin a more reliable Base RPC instead of the public default:

```bash
export EXTRAFI_RPC_URL="<reliable Base RPC URL>"
```

The default RPC (`https://mainnet.base.org`) is fine for tx-building. For repeated `info`/`positions` reads under load, a paid RPC is more reliable.

On Windows shells (bash/git-bash/PowerShell wrapped in bash), prefer forward slashes when passing paths — backslashes can collapse into escape sequences inside posix-flavored wrappers.

---

## Supported Assets

| Symbol | Decimals |
|---|---|
| USDC   | 6 |
| WETH   | 18 |
| WSTETH | 18 |
| CBETH  | 18 |
| CBBTC  | 8 |

Default asset for every subcommand: **USDC**. Use `--asset <symbol>` to override.

---

## Read endpoints

### `info` — single-reserve snapshot

```bash
npx extrafi-prepare info --user 0xUser --asset USDC
```

Returns JSON with wallet balance, supplied amount (aToken), stable/variable debt, and current supply APY / variable borrow APR for that reserve.

### `positions` — full account view

```bash
npx extrafi-prepare positions --user 0xUser
```

Returns the user's aggregate position across all reserves plus health factor and LTV:

```json
{
  "chain": "base",
  "user": "0x...",
  "summary": {
    "totalCollateralUsd":   "12.34",
    "totalDebtUsd":         "0.00",
    "availableBorrowsUsd":  "9.87",
    "liquidationThreshold": "78.00%",
    "ltv":                  "75.00%",
    "healthFactor":         "∞"
  },
  "reserves": [
    { "symbol": "USDC", "supplied": "5.000123", "stableDebt": "0", "variableDebt": "0", "asCollateral": true }
  ]
}
```

`reserves` only includes assets where the user has non-zero supply or debt. `healthFactor` is `"∞"` when there is no debt.

Always run `positions` before a borrow or a partial withdraw.

---

## Prepare endpoints

All prepare commands emit JSON in Base MCP `send_calls` shape (`{ chain, calls }`).

### `prepare-supply` — deposit into xLend

```bash
npx extrafi-prepare prepare-supply --user 0xUser --amount 50 --asset USDC
```

Builds an **ordered batch of two calls**: `USDC.approve(POOL, amount)` then `Pool.supply(asset, amount, user, 0)`.

### `prepare-withdraw` — pull asset out

```bash
npx extrafi-prepare prepare-withdraw --user 0xUser --amount 50  --asset USDC
npx extrafi-prepare prepare-withdraw --user 0xUser --amount max --asset USDC
```

Single call to `Pool.withdraw(asset, amount, user)`. `--amount max` uses `type(uint256).max`, which Aave V3 interprets as "withdraw the entire aToken balance."

### `prepare-borrow` — open a debt position

```bash
npx extrafi-prepare prepare-borrow --user 0xUser --amount 5 --asset USDC
npx extrafi-prepare prepare-borrow --user 0xUser --amount 0.01 --asset WETH --mode variable
```

Single call to `Pool.borrow(asset, amount, mode, 0, user)`. Default `--mode variable` (interestRateMode `2`). Stable mode (`1`) is accepted but is deprecated in modern Aave V3 — most reserves only support variable.

**The user must have supplied collateral first**, otherwise the call reverts (`COLLATERAL_BALANCE_IS_ZERO`). Always run `positions` first.

### `prepare-repay` — repay debt

```bash
npx extrafi-prepare prepare-repay --user 0xUser --amount 5   --asset USDC
npx extrafi-prepare prepare-repay --user 0xUser --amount max --asset USDC
```

**Ordered batch of two calls**: `Asset.approve(POOL, amount)` then `Pool.repay(asset, amount, mode, user)`. `--amount max` repays the entire current debt of the chosen mode for that asset.

When using `--amount max`, the approve is also for `uint256.max`. This is intentional — Aave V3 reads the exact current debt at call time, and the leftover allowance from a max-approve is not exploitable since the Pool only ever calls `transferFrom(user, ..., currentDebt)`.

---

## Base MCP Conversion

Every prepare subcommand emits JSON already in `send_calls` shape:

```json
{
  "chain": "base",
  "calls": [
    { "to": "0x...", "data": "0x...", "value": "0x0" }
  ]
}
```

Pass it straight through:

```
send_calls({ "chain": "base", "calls": <calls from script output> })
```

Do not re-order calls. For supply and repay, the ERC-20 approve must come before the Pool call.

---

## Orchestration

```
1. get_wallets -> Base Account address
2. (optional) npx extrafi-prepare positions --user <address>
   -> validate collateral, health factor, debt before write
3. npx extrafi-prepare <prepare-*> --user <address> --amount <decimal> --asset <symbol>
4. Parse stdout as JSON. stderr carries diagnostics.
5. send_calls(chain="base", calls=<calls>) -> approval URL + request ID
6. Show the approval URL.
7. get_request_status(requestId) -> confirmed
```

If the script exits nonzero, do not invent replacement parameters. Read the error from stderr, fix the inputs, rerun.

For borrow specifically:

```
positions -> read current HF and availableBorrowsUsd
if requested amount in USD > 0.9 * availableBorrowsUsd: warn the user and require explicit confirmation
prepare-borrow -> calldata
send_calls -> approval URL
```

---

## Example Prompts

```
Show me my Extra Finance xLend USDC position on Base.
```
1. `info --user <address> --asset USDC`
2. Present `balances.supplied`, `balances.wallet`, and `market.supplyApy`.

```
Show me my full Extra Finance account on Base.
```
1. `positions --user <address>`
2. Present `summary` (HF, LTV, totals) and `reserves` (per-asset breakdown).

```
Supply 50 USDC to Extra Finance xLend on Base.
```
1. `info` to confirm wallet balance ≥ 50 USDC.
2. `prepare-supply --user <address> --amount 50 --asset USDC`.
3. `send_calls` with the returned calls. Show approval URL.

```
Withdraw everything I have on Extra Finance USDC.
```
1. `info` to confirm there is a supplied balance.
2. `prepare-withdraw --user <address> --amount max --asset USDC`.

```
Borrow 0.001 ETH against my collateral on Extra Finance.
```
1. `positions` to confirm HF and availableBorrowsUsd.
2. Refuse if the request would push HF below 1.10.
3. `prepare-borrow --user <address> --amount 0.001 --asset WETH --mode variable`.

```
Repay all my USDC debt on Extra Finance.
```
1. `info --asset USDC` to confirm variable/stable debt amounts.
2. `prepare-repay --user <address> --amount max --asset USDC --mode variable`.

---

## Risk Notes

- Supply and withdraw have **no slippage**. Amount in = amount out (modulo accrued interest).
- Aave V3 has paused states, per-reserve caps, and frozen markets. If `supply`/`borrow` reverts, check `getReserveData` (surface from `info`) and reduce the amount or wait.
- `withdraw` can revert if it would breach health factor when the user has open borrows.
- `borrow` reverts if there is no collateral or if the post-borrow HF would be < 1.
- Stable rate borrowing (mode `1`) is deprecated and unavailable on most reserves. Default to `variable`.

---

## Tested Behavior

Tested on 2026-05-27 against Base mainnet.

What worked:
- `info --asset USDC` returned `walletBalance`, `supplied`, market APY/APR, totals.
- `prepare-supply --amount 5 --asset USDC` produced a correct ordered batch (`approve` + `supply`).
- End-to-end: script output passed to Base MCP `send_calls`, approval URL returned, transaction signed and confirmed via Base Account. Reference tx: [`0x8fcbd85e`](https://basescan.org/tx/0x8fcbd85ece6bf02bbb811837a95b71beccb965c588327616171305b612e487e8) (5 USDC supply, block 46548782).

Observed gotchas:
- On Windows / git-bash, `plugins\extra-finance\scripts\extrafi.mjs` collapses `\e`, `\s` into nothing inside Bash. Use forward slashes when invoking from a posix-flavored shell.
- The public RPC `https://mainnet.base.org` works fine for the read endpoints but can rate-limit under repeated `positions` calls. Set `EXTRAFI_RPC_URL` to a paid RPC for production usage.
- USDC has 6 decimals on Base, not 18. The script handles this via the per-reserve `decimals` table — do not override.

---

## Constants

### Pool (Aave V3 fork — xLend on Base)

| Contract | Address |
|---|---|
| Pool                          | `0x09b11746DFD1b5a8325e30943F8B3D5000922E03` |
| PoolDataProvider              | `0x1566DA4640b6a0b32fF309b07b8df6Ade40fd98D` |
| PoolAddressesProvider         | `0x1E35e657d469F134ea9cfE52E28949586f1a9c29` |
| PoolAddressesProviderRegistry | `0x61f94fA13151c197498B174471ECEdb16Bfbf4a5` |

### Reserves on Base

| Token  | Asset | aToken (supply receipt) |
|---|---|---|
| USDC   | `0x833589fcd6edb6e08f4c7c32d4f71b54bda02913` | `0xf17182f6f28Ded63B77A2Bb774c58aDe44612bE4` |
| WETH   | `0x4200000000000000000000000000000000000006` | `0x9Ef15597B0B900bfceE4A77204F72bd20C85d7c8` |
| wstETH | `0xc1cba3fcea344f92d9239c08c0568f6f2f0ee452` | `0x749Fc8D298A41A55AB305164602a185dB29f8F2B` |
| cbETH  | `0x2ae3f1ec7f1f5012cfeab0185bfc7aa3cf0dec22` | `0x2308Fc7785597cC40aB53f302b491294b8d8d8bE` |
| cbBTC  | `0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf` | `0xdf2730830c77780A11248945C342c002DB73A8Be` |

Source: `ExtraFi/contracts-and-pools-info` repo (`xlend-files/deployed-contracts.json` and `xlend-files/reserve-info.json`).

### Function selectors used

| Selector | Function |
|---|---|
| `0x095ea7b3` | `ERC20.approve(address,uint256)` |
| `0x617ba037` | `Pool.supply(address,uint256,address,uint16)` |
| `0x69328dec` | `Pool.withdraw(address,uint256,address)` |
| `0xa415bcad` | `Pool.borrow(address,uint256,uint256,uint16,address)` |
| `0x573ade81` | `Pool.repay(address,uint256,uint256,address)` |
