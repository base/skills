# B20 Common Errors

All of these are custom Solidity errors, not generic reverts — decode them rather than showing the
user a raw selector. In viem, add the error ABI entries to your contract's ABI so
`ContractFunctionRevertedError.data?.errorName` resolves to a name instead of staying opaque.

| Error | Signature | Cause | Fix |
|-------|-----------|-------|-----|
| `FeatureNotActivated` | `FeatureNotActivated(bytes32)` | The B20 variant isn't activated on this network yet | Check activation first — [activation-check.md](activation-check.md). Not your code's fault; wait or switch network. |
| `TokenAlreadyExists` | `TokenAlreadyExists(address)` | Reused a `salt` for the same `(variant, sender)` pair | Use a fresh, unique salt per deploy |
| `AccessControlUnauthorizedAccount` | `AccessControlUnauthorizedAccount(address,bytes32)` | Caller lacks the role required for this function (e.g. no `MINT_ROLE` for `mint`) | Grant the role first (requires the role's admin, default `DEFAULT_ADMIN_ROLE`) |
| `LastAdminCannotRenounce` | `LastAdminCannotRenounce()` | Called `renounceRole(DEFAULT_ADMIN_ROLE, ...)` as the sole remaining admin | Use `renounceLastAdmin()` instead if intentionally going admin-less |
| `NotSoleAdmin` | `NotSoleAdmin()` | Called `renounceLastAdmin()` while other admins still exist | Revoke other admins first, or accept they'll retain admin |
| `InvalidDecimals` | `InvalidDecimals(uint8)` | ASSET `decimals` outside `[6, 18]` | Pick a value in range |
| `InvalidCurrency` | `InvalidCurrency(string)` | STABLECOIN `currency` contains a non-`A`-`Z` byte | Uppercase ASCII letters only, no symbols/numbers |
| `MissingRequiredField` | `MissingRequiredField(string)` | A required string field (e.g. `currency`) was empty | Supply a non-empty value |
| `SupplyCapExceeded` | `SupplyCapExceeded(uint256,uint256)` | Mint would push `totalSupply` past the cap | Raise the cap (if you hold the role) or mint less |
| `InvalidSupplyCap` | `InvalidSupplyCap(uint256,uint256)` | Proposed cap is below current supply | Cap must be ≥ current `totalSupply` |
| `InsufficientBalance` | `InsufficientBalance(address,uint256,uint256)` | Sender doesn't have enough balance for a transfer/burn | Check `balanceOf` before sending |
| `InsufficientAllowance` | `InsufficientAllowance(address,uint256,uint256)` | `transferFrom` exceeds the approved allowance | `approve` more first |
| `InvalidReceiver` / `InvalidSender` | `InvalidReceiver(address)` / `InvalidSender(address)` | Usually a zero-address misuse | Validate addresses client-side before sending |
| `ContractPaused` | `ContractPaused(uint8)` | The relevant feature bit (TRANSFER/MINT/BURN) is currently paused | Wait for `unpause`, or this is intentional issuer behavior |
| `PolicyForbids` | `PolicyForbids(bytes32,uint64)` | A `PolicyRegistry` allowlist/blocklist denied this transfer/mint | Not a bug — the issuer's compliance policy is blocking this address/action |
| `AccountNotBlocked` | `AccountNotBlocked(address)` | Called `burnBlocked` on an address that isn't currently denied under `TRANSFER_SENDER_POLICY` | `burnBlocked` only seizes from already-blocked accounts, not arbitrary ones |
| `PolicyNotFound` | `PolicyNotFound(uint64)` | Referenced a policy ID that doesn't exist where existence was required | Create the policy first, or use `ALWAYS_ALLOW`/`ALWAYS_BLOCK` |
| `UnsupportedPolicyType` | `UnsupportedPolicyType(bytes32)` | Called `updatePolicy` with a `scope` that isn't one of the four recognized constants | Use `TRANSFER_SENDER_POLICY`/`TRANSFER_RECEIVER_POLICY`/`TRANSFER_EXECUTOR_POLICY`/`MINT_RECEIVER_POLICY` |
| `InternalCallFailed` | `InternalCallFailed(uint256)` | One of the `internalCalls` inside `announce()` reverted (ASSET only) | The real cause is one level deeper — inspect the wrapped inner call, not just this error |
| `ExpiredSignature` | `ExpiredSignature(uint256)` | `permit()` called after its `deadline` | Get a fresh signature with a later deadline |
| `InvalidSigner` | `InvalidSigner(address,address)` | `permit()` recovered a signer that doesn't match the claimed owner | Usually a stale `name()` in the signed domain after `updateName` rotated it — re-fetch `name()` before signing |
| `AbiDecodeFailed` / opaque revert on `createB20` | — | Client-side params encoding is wrong (most often the JS/TS single-tuple gotcha) | See [encoding.md](encoding.md) |

## TypeScript Error-Formatting Pattern

```typescript
import { BaseError, ContractFunctionRevertedError } from "viem";

const ERROR_MESSAGES: Record<string, string> = {
  FeatureNotActivated: "B20 isn't activated on this network yet.",
  AccessControlUnauthorizedAccount: "This address doesn't have the required role.",
  SupplyCapExceeded: "That amount would exceed the token's supply cap.",
  PolicyForbids: "A policy rule on this token is blocking this transaction.",
  // ...add the rest from the table above as needed
};

export function formatB20Error(error: unknown): string {
  if (error instanceof BaseError) {
    const revertError = error.walk((e) => e instanceof ContractFunctionRevertedError);
    if (revertError instanceof ContractFunctionRevertedError) {
      const name = revertError.data?.errorName;
      if (name && ERROR_MESSAGES[name]) return ERROR_MESSAGES[name];
    }
    return error.shortMessage;
  }
  return error instanceof Error ? error.message : "Something went wrong.";
}
```

This only resolves `errorName` if the error is declared in the ABI you pass to `writeContract`/
`simulateContract` — add the ones you expect to hit, not just the function signatures.
