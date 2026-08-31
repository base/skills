# Arcis Protocol Plugin

> [!IMPORTANT]
> ## STOP — COMPLETE ONBOARDING BEFORE USING THIS PLUGIN
>
> Before calling any Arcis endpoint, you MUST complete the Base MCP onboarding flow:
> 1. Call `get_wallets` (Detection)
> 2. Present wallet status and disclaimer (Onboarding)
>
> The user's wallet address — required by every call — is only confirmed during Detection.

Arcis Protocol is financial infrastructure for autonomous AI agents on Base. Yield-bearing vaults (raUSDC), identity-aware credit (ERC-8004), and revenue bonds — accessible through the Agent Treasury Interface (ATI): `deposit()`, `withdraw()`, `balance()`.

**Supported chain:** Base mainnet (`8453` / `0x2105`).

---

## Contract Addresses

| Contract | Address |
|---|---|
| ArcisVault (raUSDC) | `0x00325d9da832b38179ed2f0dabd4062d93e325a7` |
| AgentCredit | `0xdf31800e620f728297340d66acf5a306f07ce7a1` |
| RevenueBondFactory | `0xeb65d8bb08e0ea4a6bb9162d53d1b444f99681ba` |
| IdentityRegistry | `0xaa4da295dd368c0f10128654af76e3f002e20e71` |
| ATIRouter | `0xd0c64f997ca9aa427f8834578bd7f0313f868e83` |
| StrategyAave | `0x43626D6162Ccb12328B989BB228DaD2941F2F12a` |
| StrategyAllocator | `0x7Fd5d7b49694858FCf143E0039e83cDB0196DD7A` |
| USDC | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |

---

## Read Operations

View calls — no transaction needed.

### Vault TVL
```
Function: totalAssets()
Selector: 0x01e1d114
Contract: ArcisVault
Returns: uint256 (USDC amount, 6 decimals)
```

### Agent Balance
```
Function: balance(address agent)
Selector: 0xe3d670d7
Contract: ArcisVault
Returns: uint256 (USDC value of agent's position, 6 decimals)
```

### Exchange Rate
```
Function: exchangeRate()
Selector: 0x3ba0b9a9
Contract: ArcisVault
Returns: uint256 (18 decimals — divide by 1e24 for human-readable rate)
```

### Max Deposit
```
Function: maxDeposit(address agent)
Selector: 0x402d267d
Contract: ArcisVault
Returns: uint256 (max additional USDC the agent can deposit, 6 decimals)
```

### Preview Deposit
```
Function: previewDeposit(uint256 assets)
Selector: 0xef8b30f7
Contract: ArcisVault
Returns: uint256 (raUSDC shares the agent would receive)
```

### Credit Utilization
```
Function: lendingPool() → uint256
Selector: 0x3a85149a
Contract: AgentCredit

Function: totalBorrowed() → uint256
Selector: 0x4c19386c
Contract: AgentCredit
```

---

## Write Operations

### Deposit USDC into Vault

Two calls required (approve + deposit), executed atomically via `send_calls`:

**Step 1 — Approve USDC:**
```
Function: approve(address spender, uint256 amount)
Selector: 0x095ea7b3
Contract: USDC (0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913)
Arguments: spender = ArcisVault address, amount = deposit amount
```

**Step 2 — Deposit:**
```
Function: deposit(uint256 amount)
Selector: 0xb6b55f25
Contract: ArcisVault (0x00325d9da832b38179ed2f0dabd4062d93e325a7)
Arguments: amount = USDC amount (6 decimals, e.g. 100000000 = $100)
```

### Withdraw from Vault
```
Function: withdraw(uint256 shares)
Selector: 0x2e1a7d4d
Contract: ArcisVault
Arguments: shares = raUSDC shares to redeem
```

---

## send_calls Mapping

### Deposit (ordered batch)
```json
{
  "chain": "base",
  "calls": [
    {
      "to": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
      "value": "0x0",
      "data": "0x095ea7b3<vault_address_padded><amount_padded>"
    },
    {
      "to": "0x00325d9da832b38179ed2f0dabd4062d93e325a7",
      "value": "0x0",
      "data": "0xb6b55f25<amount_padded>"
    }
  ]
}
```

### Withdraw
```json
{
  "chain": "base",
  "calls": [
    {
      "to": "0x00325d9da832b38179ed2f0dabd4062d93e325a7",
      "value": "0x0",
      "data": "0x2e1a7d4d<shares_padded>"
    }
  ]
}
```

---

## Orchestration Patterns

### Deposit Flow
```
1. get_wallets → address
2. Read balance(address) → current position
3. Read maxDeposit(address) → remaining capacity
4. Validate: deposit ≤ maxDeposit and user has sufficient USDC
5. Read previewDeposit(amount) → expected shares
6. Present: "Deposit $X USDC → receive Y raUSDC shares"
7. send_calls(chain="base", calls=[approve, deposit])
8. get_request_status → confirmed
```

### Withdraw Flow
```
1. get_wallets → address
2. Read balance(address) → position value
3. Present: "Withdraw Y shares → receive ~$X USDC"
4. send_calls(chain="base", calls=[withdraw])
5. get_request_status → confirmed
```

---

## MCP Server Alternative

For AI agents that use MCP natively:

```json
{
  "mcpServers": {
    "arcis": { "command": "npx", "args": ["@arcisprotocol/mcp"] }
  }
}
```

Remote endpoint: `https://mcp-production-8219.up.railway.app/mcp`

npm: `@arcisprotocol/mcp`

---

## Notes

- USDC uses 6 decimals. $100 = `100000000`.
- Exchange rate uses 18 decimals with virtual offset. Divide by 1e24 for human-readable.
- Early withdrawals (within 24h) incur 0.1% fee (flash loan protection).
- Strategy additions require 24-hour timelock.
- Emergency withdraw works even when paused.

## Links

- Website: [arcis.money](https://arcis.money)
- Dashboard: [arcis.money/dashboard](https://arcis.money/dashboard)
- GitHub: [github.com/Arcis-Protocol](https://github.com/Arcis-Protocol)
- DeFiLlama: [defillama.com/protocol/arcis](https://defillama.com/protocol/arcis-protocol)
- X: [@ArcisProtocol](https://x.com/ArcisProtocol) · [@custos0x](https://x.com/custos0x)
