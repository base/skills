---
title: "Quote Display Sanity Checks"
description: "Skill reference for verifying human-readable token amounts before showing a quote or requesting approval."
---

# Quote Display Sanity Checks

Before presenting a swap / DeFi quote, or asking the user to approve a transaction, verify that any human-readable token amount shown in the chat summary was actually derived from the raw amount using the token's correct `decimals`. Do not eyeball, mentally shift a decimal point, or reuse a value computed earlier in the conversation without recomputing it.

## The problem this addresses

Even when the underlying calldata and the Base Account approval screen are correct, the agent's chat summary is still part of the user's trust boundary. If the displayed human-readable amount doesn't match the raw amount, a user reading the summary before opening the approval link may misunderstand what they are about to approve.

## Format function

Use this conversion whenever a raw token amount (in the token's smallest unit, e.g. wei) needs to be shown to the user:

```
function formatTokenAmount(rawAmountWei, decimals):
    # rawAmountWei: integer amount in the token's smallest unit (e.g. wei for ETH)
    # decimals: the token's decimals value (18 for ETH, 6 for USDC, etc.)
    return rawAmountWei / (10 ** decimals)
```

`decimals` must come from token metadata or the MCP response for that specific token — never assume it, and never assume it matches another token's decimals in the same quote (e.g. USDC has 6 decimals, ETH has 18).

## Worked example (matches the reported issue)

- Raw output amount: `50355726366371` wei
- Token: ETH, decimals: `18`
- Human-readable: `50355726366371 / 10^18 = 0.000050355726366371 ETH`

An agent summary that instead displays `0.050356 ETH` is off by roughly three orders of magnitude and must not be shown to the user.

## Checklist before showing a quote or approval summary

1. Identify the raw amount and the token's `decimals` for every amount you're about to display (input and output).
2. Apply `formatTokenAmount(rawAmountWei, decimals)` explicitly — do not shortcut this.
3. Sanity-check by reversing the calculation: `humanReadableValue * 10^decimals` should equal the original raw amount.
4. Only after this check passes, present the quote or approval request summary to the user.
5. If you cannot confirm the token's `decimals`, say so and ask, or fetch it — do not guess.

## Common mistakes

- Off-by-one-order-of-magnitude errors from misremembering or guessing a token's `decimals`.
- Manually reformatting a raw wei string (e.g. inserting a decimal point by eye) instead of doing the actual division.
- Reusing a partially-computed or earlier-in-conversation value instead of recomputing from the raw amount for the final summary.
- Applying one token's `decimals` to a different token's raw amount in a multi-token quote (e.g. using USDC's 6 decimals when formatting the ETH output amount).
