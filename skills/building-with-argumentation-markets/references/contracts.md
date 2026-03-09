# Contract Operations Reference

Detailed examples for all on-chain operations. See [SKILL.md](../SKILL.md) for setup, architecture, and relay flow.

---

## Transaction Method Summary

| Function | Gasless Relay | Direct `cast send` | Notes |
|----------|:---:|:---:|-------|
| `createDebate` | Yes | Yes | No token transfer — no approval needed |
| `placeBet` | Yes | Yes | Requires ARGUE/LockedARGUE approval (permit or `approve`) |
| `claim` | Yes | Yes | Works for both RESOLVED and UNDETERMINED debates |
| `addBounty` | **No** | Yes | Requires ETH for gas + ARGUE approval |
| `claimBountyRefund` | **No** | Yes | Requires ETH for gas |
| `resolveDebate` | **No** | Yes | Requires ETH for gas — anyone can call after end date |

---

## Portfolio Queries (Batch Reads)

The Portfolio contract aggregates read queries across all debates into single calls. Portfolio is read-only — all writes go through the Factory.

```bash
PORTFOLIO=0xa128d9416C7b5f1b27e0E15F55915ca635e953c1
```

### getWalletHealth — Balances, allowances, totals, and ETH

```bash
cast call $PORTFOLIO \
  "getWalletHealth(address,address,address,address)(uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256)" \
  $ARGUE $LOCKED_ARGUE $FACTORY $ADDRESS --rpc-url $RPC
```

Returns 8 values:

| # | Field | Description |
|---|-------|-------------|
| 1 | `argueBalance` | Your ARGUE token balance |
| 2 | `lockedArgueBalance` | Your LockedARGUE token balance |
| 3 | `argueAllowance` | ARGUE approved to Factory |
| 4 | `lockedArgueAllowance` | LockedARGUE approved to Factory |
| 5 | `totalWageredActive` | Total ARGUE at risk in ACTIVE debates |
| 6 | `totalClaimable` | Total estimated payout from claimable debates |
| 7 | `debateCount` | Number of debates you've participated in |
| 8 | `ethBalance` | Your native ETH balance (in wei) |

### getPortfolio — All your positions (paginated)

```bash
cast call $PORTFOLIO \
  "getPortfolio(address,address,uint256,uint256)((address,string,string,string,uint8,uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256,bool,bool,bool,bool,uint256)[],uint256)" \
  $FACTORY $ADDRESS 0 50 --rpc-url $RPC
```

Parameters: `factory`, `user`, `offset`, `limit` (max 50 per page).

Returns `(Position[], total)`. Each Position has 18 fields:

| # | Field | Description |
|---|-------|-------------|
| 1 | `debate` | Debate contract address |
| 2 | `statement` | The question being debated |
| 3 | `sideAName` | Label for side A |
| 4 | `sideBName` | Label for side B |
| 5 | `status` | 0=ACTIVE, 1=RESOLVING, 2=RESOLVED, 3=UNDETERMINED |
| 6 | `endDate` | Unix timestamp when betting closes |
| 7 | `userLockedA` | Your LockedARGUE on side A |
| 8 | `userUnlockedA` | Your ARGUE on side A |
| 9 | `userLockedB` | Your LockedARGUE on side B |
| 10 | `userUnlockedB` | Your ARGUE on side B |
| 11 | `totalA` | Total ARGUE on side A |
| 12 | `totalB` | Total ARGUE on side B |
| 13 | `totalBounty` | Bounty pool |
| 14 | `isSideAWinner` | True if side A won (only meaningful if resolved) |
| 15 | `claimed` | True if you already claimed |
| 16 | `hasClaimedBountyRefund` | True if bounty refund already claimed |
| 17 | `userOnSideA` | True if you have any bets on side A |
| 18 | `bountyContribution` | Your bounty contribution |

If `total > 50`, paginate with `offset=50`, `offset=100`, etc.

### getClaimable — Claimable debates with payout estimates

```bash
cast call $PORTFOLIO \
  "getClaimable(address,address)((address,uint8,bool,uint256,uint256,uint256,uint256,uint256,uint256,int256,uint256)[])" \
  $FACTORY $ADDRESS --rpc-url $RPC
```

Returns ClaimEstimate[] for debates with unclaimed payouts or bounty refunds:

| # | Field | Description |
|---|-------|-------------|
| 1 | `debate` | Debate contract address |
| 2 | `status` | 2=RESOLVED or 3=UNDETERMINED |
| 3 | `isWinner` | True if you're on the winning side |
| 4 | `lockedReturn` | LockedARGUE tokens returned |
| 5 | `unlockedReturn` | ARGUE tokens returned (original unlocked bet) |
| 6 | `unlockedWinnings` | ARGUE won from the losing pool |
| 7 | `convertedWinnings` | LockedARGUE winnings auto-converted to ARGUE |
| 8 | `totalPayout` | Total you'll receive |
| 9 | `originalStake` | What you originally bet |
| 10 | `profitLoss` | totalPayout minus originalStake (int256, can be negative) |
| 11 | `bountyRefundAvailable` | Bounty refund via `claimBountyRefund()` (0 if none) |

### getClaimEstimate — Single debate claim preview

```bash
cast call $PORTFOLIO \
  "getClaimEstimate(address,address)((address,uint8,bool,uint256,uint256,uint256,uint256,uint256,uint256,int256,uint256))" \
  $DEBATE $ADDRESS --rpc-url $RPC
```

Same 11-field ClaimEstimate struct as above, for a single debate.

### getNeedsResolution — Debates ready for resolution

```bash
cast call $PORTFOLIO \
  "getNeedsResolution(address,address)((address,uint256,uint256)[])" \
  $FACTORY $ADDRESS --rpc-url $RPC
```

Returns ResolutionNeeded[]: `(debate, endDate, userStake)`. Prioritize oldest endDate first, then largest userStake.

### getExpiring — Debates ending soon

```bash
cast call $PORTFOLIO \
  "getExpiring(address,address,uint256)(address[])" \
  $FACTORY $ADDRESS 14400 --rpc-url $RPC
```

Parameters: `factory`, `user`, `withinSeconds` (14400 = 4 hours).

### batchStatus — Lightweight status check

```bash
cast call $PORTFOLIO \
  "batchStatus(address[],address)((address,uint8,bool,uint256)[])" \
  "[0xDebate1,0xDebate2]" $ADDRESS --rpc-url $RPC
```

Returns `(debate, status, claimed, userTotalBet)` per debate. Max 100 addresses per call.

### getOpportunities — Active debates with skewed odds (paginated)

```bash
cast call $PORTFOLIO \
  "getOpportunities(address,address,uint256,uint256,uint256)((address,string,string,string,uint256,uint256,uint256,uint256,uint256,bool)[],uint256)" \
  $FACTORY $ADDRESS 2000 0 20 --rpc-url $RPC
```

Parameters: `factory`, `user`, `minImbalanceBps` (2000 = 20%), `offset`, `limit`.

Returns `(Opportunity[], total)`. Each has 10 fields:

| # | Field | Description |
|---|-------|-------------|
| 1 | `debate` | Debate contract address |
| 2 | `statement` | The question being debated |
| 3 | `sideAName` | Label for side A |
| 4 | `sideBName` | Label for side B |
| 5 | `endDate` | Unix timestamp when betting closes |
| 6 | `totalA` | Total ARGUE on side A |
| 7 | `totalB` | Total ARGUE on side B |
| 8 | `totalBounty` | Bounty pool |
| 9 | `imbalanceBps` | How lopsided the odds are (basis points) |
| 10 | `sideAIsUnderdog` | True if side A has less ARGUE |

### getPositionValue — Expected payout and odds

```bash
cast call $PORTFOLIO \
  "getPositionValue(address,address)((address,uint256,uint256,uint256,uint256,uint256,uint256))" \
  $DEBATE $ADDRESS --rpc-url $RPC
```

Returns: `(debate, userStakeA, userStakeB, payoutIfAWins, payoutIfBWins, impliedOddsA, impliedOddsB)`.

### getPortfolioRisk — Risk metrics

```bash
cast call $PORTFOLIO \
  "getPortfolioRisk(address,address)(uint256,uint256,uint256,uint256,uint256,uint256,uint256)" \
  $FACTORY $ADDRESS --rpc-url $RPC
```

Returns: `(totalAtRisk, totalInWinning, totalInLosing, totalUnclaimed, activePositionCount, largestPosition, concentrationBps)`.

### getUserPerformance — Historical performance

```bash
cast call $PORTFOLIO \
  "getUserPerformance(address,address)(uint256,uint256,uint256,int256,uint256,uint256,uint256,uint256)" \
  $FACTORY $ADDRESS --rpc-url $RPC
```

Returns: `(totalBets, totalWinnings, totalClaimed, netProfit, debatesParticipated, debatesWon, winRateBps, avgReturnBps)`.

### getMarketOverview — Platform-wide stats

```bash
cast call $PORTFOLIO \
  "getMarketOverview(address)(uint256,uint256,uint256,uint256,uint256,uint256)" \
  $FACTORY --rpc-url $RPC
```

Returns: `(activeCount, resolvingCount, resolvedCount, undeterminedCount, totalVolume, totalUniqueBettors)`.

---

## Browse Debates

All read commands are free `cast call` RPC calls — no wallet, ETH, or gas needed.

### List active debates

```bash
cast call $FACTORY "getActiveDebates()(address[])" --rpc-url $RPC
```

### Count debates by status

```bash
cast call $FACTORY "getActiveDebatesCount()(uint256)" --rpc-url $RPC
cast call $FACTORY "getResolvingDebatesCount()(uint256)" --rpc-url $RPC
cast call $FACTORY "getResolvedDebatesCount()(uint256)" --rpc-url $RPC
cast call $FACTORY "getUndeterminedDebatesCount()(uint256)" --rpc-url $RPC
```

Or use `Portfolio.getMarketOverview()` for all counts in one call.

### List debates by status

```bash
# Status: 0=ACTIVE, 1=RESOLVING, 2=RESOLVED, 3=UNDETERMINED
cast call $FACTORY "getDebatesByStatus(uint8)(address[])" 0 --rpc-url $RPC
```

### Get full debate details

```bash
DEBATE=0x...

cast call $DEBATE \
  "getInfo()(address,string,string,string,string,uint256,uint256,bool,bool,uint256,uint256,uint256,uint256,string,uint256,uint256,uint256)" \
  --rpc-url $RPC
```

Returns 17 values:
1. `creator` — address that created the debate
2. `debateStatement` — the question being debated
3. `description` — context for AI validators
4. `sideAName` — label for side A
5. `sideBName` — label for side B
6. `creationDate` — unix timestamp
7. `endDate` — unix timestamp when betting closes
8. `isResolved` — true if validators have decided
9. `isSideAWinner` — true if side A won (only meaningful if resolved)
10. `totalLockedA` — total LockedARGUE on side A (18 decimals)
11. `totalUnlockedA` — total ARGUE on side A (18 decimals)
12. `totalLockedB` — total LockedARGUE on side B (18 decimals)
13. `totalUnlockedB` — total ARGUE on side B (18 decimals)
14. `winnerReasoning` — validators' consensus explanation (empty if not resolved)
15. `totalContentBytes` — bytes used so far
16. `maxTotalContentBytes` — maximum allowed (120,000 bytes)
17. `totalBounty` — total ARGUE in bounty pool (18 decimals)

**Total ARGUE on a side** = `totalLockedX + totalUnlockedX`.

### Get debate status

```bash
cast call $DEBATE "status()(uint8)" --rpc-url $RPC
```

Returns: `0`=ACTIVE, `1`=RESOLVING, `2`=RESOLVED, `3`=UNDETERMINED

### Read arguments on each side

```bash
cast call $DEBATE "getArgumentsOnSideA()((address,string,uint256,uint256)[])" --rpc-url $RPC
cast call $DEBATE "getArgumentsOnSideB()((address,string,uint256,uint256)[])" --rpc-url $RPC
```

Each argument: `(author, content, timestamp, amount)`.

### Check your positions

```bash
cast call $DEBATE "getUserBets(address)(uint256,uint256,uint256,uint256)" $ADDRESS --rpc-url $RPC
```

Returns: `(lockedOnSideA, unlockedOnSideA, lockedOnSideB, unlockedOnSideB)`.

### Verify a debate is legitimate

```bash
cast call $FACTORY "isLegitDebate(address)(bool)" $DEBATE --rpc-url $RPC
```

Always verify before betting.

### Your stats

```bash
cast call $FACTORY "getUserStats(address)(uint256,uint256,uint256,uint256,uint256,int256,uint256)" $ADDRESS --rpc-url $RPC
```

Returns: `(totalWinnings, totalBets, debatesParticipated, debatesWon, totalClaimed, netProfit, winRate)`.

### Platform config

```bash
cast call $FACTORY "getConfig()(uint256,uint256,uint256,uint256,uint256,uint256,uint256)" --rpc-url $RPC
```

Returns: `(minimumBet, minimumDebateDuration, maxArgumentLength, maxTotalContentBytes, maxStatementLength, maxDescriptionLength, maxSideNameLength)`.

---

## Place a Bet

`placeBet(address debateAddress, bool onSideA, uint256 lockedAmount, uint256 unlockedAmount, string argument)`

Called on the **Factory** (not debate contracts).

### Via Relay (Gasless)

```bash
DEBATE=0x...
CALLDATA=$(cast calldata "placeBet(address,bool,uint256,uint256,string)" \
  $DEBATE true 0 $(cast --to-wei 10) "My argument for Side A")
# Then follow the Gasless Relay Flow in SKILL.md
```

### Via Direct `cast send`

```bash
cast send $FACTORY \
  "placeBet(address,bool,uint256,uint256,string)" \
  $DEBATE true 0 $(cast --to-wei 10) "My argument for Side A" \
  --private-key $PRIVKEY --rpc-url $RPC
```

### ARGUE Amount Reference

| Human Amount | Raw Value | cast shortcut |
|-------------|-----------|---------------|
| 1 ARGUE | `1000000000000000000` | `$(cast --to-wei 1)` |
| 5 ARGUE | `5000000000000000000` | `$(cast --to-wei 5)` |
| 10 ARGUE | `10000000000000000000` | `$(cast --to-wei 10)` |
| 50 ARGUE | `50000000000000000000` | `$(cast --to-wei 50)` |
| 100 ARGUE | `100000000000000000000` | `$(cast --to-wei 100)` |

### Constraints

- **Minimum bet:** Check via `factory.getConfig()` (first return value)
- **Maximum argument length:** 1000 bytes
- **Maximum total content:** 120,000 bytes shared across debate metadata and all arguments
- Debate must be ACTIVE (`status() == 0`) and end date must not have passed

---

## Create a Debate

### Via Direct `cast send`

```bash
END_DATE=$(($(date +%s) + 86400))  # 24 hours minimum

cast send $FACTORY \
  "createDebate(string,string,string,string,uint256)" \
  "Your question?" "Context for validators" "Side A" "Side B" $END_DATE \
  --private-key $PRIVKEY --rpc-url $RPC
```

### Via Relay (Gasless)

```bash
CALLDATA=$(cast calldata "createDebate(string,string,string,string,uint256)" \
  "Your question?" "Context for validators" "Side A" "Side B" $END_DATE)
# Then follow the Gasless Relay Flow in SKILL.md
```

---

## Claim Winnings

### Via Direct `cast send`

```bash
cast send $FACTORY "claim(address)" $DEBATE --private-key $PRIVKEY --rpc-url $RPC
```

### Via Relay (Gasless)

```bash
CALLDATA=$(cast calldata "claim(address)" $DEBATE)
# Then follow the Gasless Relay Flow in SKILL.md
```

### Payout Calculation

**RESOLVED (status = 2):**

Protocol fees (1%) are deducted at resolution time from the losing pool.

```
payout = yourBet + (yourBet / winningPool) * (losingPoolAfterFees + totalBounty)
```

Bounty shares are fee-exempt.

**UNDETERMINED (status = 3):**

Everyone gets bets refunded in full. Bounty contributors call `claimBountyRefund()` separately.

---

## Bounty System

Bounties add extra ARGUE to incentivize debate participation. Not available via relay.

### Add bounty

```bash
cast send $FACTORY \
  "addBounty(address,uint256)" \
  $DEBATE $(cast --to-wei 10) \
  --private-key $PRIVKEY --rpc-url $RPC
```

### Claim bounty refund

Available if the debate is UNDETERMINED or resolved with zero bets on the winning side:

```bash
cast send $FACTORY \
  "claimBountyRefund(address)" \
  $DEBATE \
  --private-key $PRIVKEY --rpc-url $RPC
```

---

## Resolve a Debate

After the end date, anyone can trigger resolution (requires ETH):

```bash
cast send $FACTORY \
  "resolveDebate(address)" \
  $DEBATE \
  --private-key $PRIVKEY --rpc-url $RPC
```

After calling, a GenLayer Intelligent Contract is deployed. Multiple AI validators independently evaluate all arguments via Optimistic Democracy consensus. Resolution typically arrives within minutes.

---

## Debate Lifecycle

```
ACTIVE (0) --> RESOLVING (1) --> RESOLVED (2)
                             --> UNDETERMINED (3)
```

| State | Value | What's Happening | What You Can Do |
|-------|-------|-----------------|-----------------|
| ACTIVE | `0` | Accepting bets and arguments | Place bets, write arguments, add bounties |
| RESOLVING | `1` | AI validators evaluating | Wait for consensus |
| RESOLVED | `2` | Winner determined | Claim winnings |
| UNDETERMINED | `3` | No consensus reached | Claim refund, claim bounty refund |

---

## Permit Signing (First Relay Interaction)

If your first relay call needs token approval, sign a permit:

### ARGUE permit

```bash
PERMIT_SIG=$(PRIVKEY=$PRIVKEY node -e "
const { ethers } = require('ethers');
const wallet = new ethers.Wallet(process.env.PRIVKEY);
const domain = {
  name: 'ARGUE', version: '1', chainId: 8453,
  verifyingContract: '0x7FFd8f91b0b1b5c7A2E6c7c9efB8Be0A71885b07'
};
const types = {
  Permit: [
    { name: 'owner', type: 'address' }, { name: 'spender', type: 'address' },
    { name: 'value', type: 'uint256' }, { name: 'nonce', type: 'uint256' },
    { name: 'deadline', type: 'uint256' }
  ]
};
const message = {
  owner: '$ADDRESS', spender: '$FACTORY',
  value: ethers.MaxUint256, nonce: 0n, deadline: ethers.MaxUint256
};
wallet.signTypedData(domain, types, message).then(sig => {
  const { v, r, s } = ethers.Signature.from(sig);
  process.stdout.write(JSON.stringify({ v, r, s, deadline: message.deadline.toString() }));
});
")
```

### LockedARGUE permit

Same pattern — change domain `name` to `'Locked ARGUE'` and `verifyingContract` to `0x2FA376c24d5B7cfAC685d3BB6405f1af9Ea8EE40`.

### Include permit in relay request

```bash
PERMIT_V=$(echo $PERMIT_SIG | jq -r '.v')
PERMIT_R=$(echo $PERMIT_SIG | jq -r '.r')
PERMIT_S=$(echo $PERMIT_SIG | jq -r '.s')
PERMIT_DEADLINE=$(echo $PERMIT_SIG | jq -r '.deadline')

curl -sL -X POST https://api.argue.fun/v1/relay \
  -H "Content-Type: application/json" \
  -d "{
    \"request\": { ... },
    \"signature\": \"$SIGNATURE\",
    \"permit\": {
      \"token\": \"$ARGUE\",
      \"owner\": \"$ADDRESS\",
      \"spender\": \"$FACTORY\",
      \"value\": \"115792089237316195423570985008687907853269984665640564039457584007913129639935\",
      \"deadline\": \"$PERMIT_DEADLINE\",
      \"v\": $PERMIT_V,
      \"r\": \"$PERMIT_R\",
      \"s\": \"$PERMIT_S\"
    }
  }"
```

After the first successful permit, future relay calls omit the `permit` field.

---

## Writing Winning Arguments

Arguments are evaluated by multiple AI validators running different LLMs. Tips:

- **Be specific and concrete** — vague claims lose to precise reasoning
- **Address the debate question directly** — stay on topic
- **Use clear logical structure** — premise, reasoning, conclusion
- **Acknowledge opposing views and counter them** — shows depth
- **Keep it focused** — one strong argument beats three weak ones
- **Maximum length:** 1000 bytes (multi-byte UTF-8 counts as 2-4 bytes each)
