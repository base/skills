---
title: "Quote Sanity Checks"
description: "Skill reference for validating raw token amounts against human-readable values to prevent display errors in chat summaries."
---

# Quote Sanity Checks

Before presenting a swap, lending, or any DeFi quote to the user, or asking the user to approve a transaction, you **MUST** run sanity checks on the token amounts shown in the human-readable summary.

Even if the underlying calldata or the transaction payload sent to the wallet is correct, displaying an incorrect human-readable token amount in the chat summary breaks the user's trust boundary.

---

## Sanity Check Rules

### 1. Match Raw Base Units with Decimals
Always verify the decimal count of the token you are displaying:
- **ETH / WETH / DAI**: 18 decimals
- **USDC / USDT**: 6 decimals
- **WBTC / cbBTC**: 8 decimals

For any other token, query the token's decimal value or use the value specified by the plugin or API response. Never assume 18 decimals for non-ETH/non-standard tokens.

### 2. Math Consistency
Ensure the formatted amount $H$ (human-readable) and the raw amount $R$ (in base units / wei) satisfy:
$$H \approx \frac{R}{10^{\text{decimals}}}$$

**Example of a display bug to avoid:**
- Input: `50,355,726,366,371` wei of ETH.
- Correct conversion: $\frac{50,355,726,366,371}{10^{18}} = 0.000050355726366371$ ETH.
- **Incorrect/Buggy display**: `0.050356` ETH (off by 3 orders of magnitude due to standard float parsing or decimal shifting mistakes).

### 3. Handle Small Value Truncation Safely
- Do **NOT** aggressively round small amounts (e.g. rounding `0.00005` to `0.05` or `0.00`).
- If an amount is very small:
  - Display the full precise value (e.g., `0.00005035 ETH`).
  - Or display the raw value in base units alongside the formatted value to avoid ambiguity: `0.00005035 ETH (50,355,726,366,371 wei)`.
  - Never truncate a non-zero amount to `0.00` in the summary text.

### 4. Floating Point Safety
- JavaScript/TypeScript float arithmetic can introduce rounding errors (e.g. `0.1 + 0.2 !== 0.3`).
- When doing conversions, use BigInt operations or string manipulation rather than native division/multiplication to avoid precision issues.
- Convert raw strings to BigInt first, pad with leading zeros if necessary, and insert the decimal point relative to the token's decimal precision.

---

## Action Plan for Quotes

When generating a quote summary:
1. **Locate the raw amount** and the **token decimals**.
2. **Perform the division** using string positioning or safe BigInt/decimal logic.
3. **Compare** the resulting value against any pre-formatted values returned by the API/plugin.
4. If the pre-formatted value differs from your safe calculation by more than a reasonable formatting/rounding limit:
   - Trust your safe calculation or the raw base unit amount.
   - Display both the raw amount and the formatted amount clearly: `"Amount: 0.00005035 ETH (~50,355,726,366,371 wei)"`.
