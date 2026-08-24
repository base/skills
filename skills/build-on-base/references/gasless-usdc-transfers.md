---
title: "Gasless USDC Transfers (EIP-3009)"
description: "Skill reference for implementing gasless USDC transfers on Base with transferWithAuthorization — signing, relaying, validation, and smart-wallet caveats."
---

# Gasless USDC Transfers (EIP-3009)

USDC on Base implements **EIP-3009** (`transferWithAuthorization`): the token holder signs an EIP-712 authorization offchain, and any third party (a "relayer") can submit it onchain, paying the gas. The USDC contract verifies the signature itself — the relayer needs no approval and can never alter the transfer.

Use this pattern when users hold USDC but no ETH (common onboarding case), or when your product sponsors gas for payments.

## The authorization envelope

Six parameters, all locked by the user's signature:

| Field | Type | Notes |
|-------|------|-------|
| `from` | address | Token holder. Must be an **EOA** — see smart-wallet caveat below. |
| `to` | address | Recipient. Signed — the relayer cannot redirect. |
| `value` | uint256 | Amount in base units (USDC has 6 decimals). |
| `validAfter` | uint256 | Unix time; use `0` unless scheduling. |
| `validBefore` | uint256 | Unix time expiry. **Keep short** (minutes–1h). |
| `nonce` | bytes32 | Random 32 bytes. The contract enforces one use per `(from, nonce)`. |

## EIP-712 domain — exact values matter

```ts
const domain = {
  name: 'USD Coin',       // MUST match the token contract's name()
  version: '2',
  chainId: 8453,           // 84532 for Base Sepolia
  verifyingContract: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913', // USDC on Base
};
```

Common pitfall: the `name` field must equal the deployed contract's `name()` exactly. Do not assume all Circle stablecoins share it — **EURC on Base returns `"EURC"`**, not "EUR Coin". If the domain name is wrong, signatures fail with a generic "invalid signature" revert that gives no hint the domain was the problem.

Token addresses:

| Token | Network | Address |
|-------|---------|---------|
| USDC | Base (8453) | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |
| USDC | Base Sepolia (84532) | `0x036CbD53842c5426634e7929541eC2318f3dCF7e` |

## Relayer-side validation checklist

The signature protects the transfer parameters, but the relayer should still validate before spending gas:

1. **Cap `validBefore`** — reject authorizations valid longer than ~1 hour. A signed authorization is a bearer instrument until it expires or is used.
2. **Check `from` is an EOA** (`getCode(from) === '0x'`) and fail with a clear message otherwise (see below).
3. **Parse amounts as `BigInt`** and reject non-positive values; never coerce silently.
4. **Rate-limit** the relay endpoint — every submission costs the relayer gas, and a griefing client can drain the gas budget with valid-but-pointless transfers.
5. **Surface revert reasons** (`authorization is used`, `authorization is expired`) to the caller instead of a generic 500 — these are the two most common failures and both are user-actionable.

## Smart-wallet caveat (the most common integration failure)

EIP-3009 requires an ECDSA signature that `ecrecover`s to `from`. **Smart-contract wallets (Base Account, Safe, any ERC-4337 account) cannot produce one** — their `signTypedData` returns an ERC-1271/ERC-6492 signature that the USDC contract's EIP-3009 path will reject.

- Detect contract accounts up front with `getCode` and route them to a different gasless mechanism — batched calls (EIP-5792) with a paymaster is the standard alternative on Base.
- Audit **every** `signTypedData` call site when adding smart-wallet support; the same limitation applies to EIP-2612 `permit`.
- Do not let the failure surface as a revert at submission time — by then the user has already signed and waited.

## Reference implementation

A runnable end-to-end demo (Next.js + viem: signing UI, relay endpoint with the validation checklist above) is available in the Base demos repository under `apps/gasless-usdc-payments/`.
