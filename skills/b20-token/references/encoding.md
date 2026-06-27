# Encoding B20 Params in JS/TS (viem/wagmi)

If you're building a wallet-signed UI (the user signs with their own wallet — MetaMask, Coinbase
Wallet, WalletConnect — rather than a Foundry script holding a private key), you need to replicate
`B20FactoryLib`'s encoding in TypeScript. This is the single most error-prone part of a client-side
B20 integration.

## Table of Contents

- [The Gotcha](#the-gotcha)
- [Correct viem Encoding](#correct-viem-encoding)
- [`initCalls` Entries Are Normal Function-Call Encoding](#initcalls-entries-are-normal-function-call-encoding)
- [Decoding Custom Errors](#decoding-custom-errors)
- [Builder Code Attribution (ERC-8021)](#builder-code-attribution-erc-8021)

## The Gotcha

`B20FactoryLib.encodeStablecoinCreateParams` (and the ASSET equivalent) does:

```solidity
return abi.encode(
    IB20Factory.B20StablecoinCreateParams({ version: 1, name: name, symbol: symbol, ... })
);
```

This is `abi.encode` of **a single struct argument**. Solidity ABI-encodes a struct as a tuple —
and because it's the *only* top-level argument and that tuple is dynamic (it contains strings),
the encoding is:

```
[offset slot: 0x20]  →  [the tuple's own head/tail encoding]
```

i.e. **one extra 32-byte offset slot precedes the struct's fields.** It is *not* the same as
encoding the fields as a flat parameter list. Encoding it as a flat list silently produces
different (shorter) calldata that the factory will reject — typically as `AbiDecodeFailed` or a
similarly opaque revert, because the bytes "look like" valid ABI data, just shifted by one slot.

## Correct viem Encoding

Use a **single tuple-typed parameter**, not a flat parameter list:

```typescript
import { encodeAbiParameters, parseAbiParameters, type Address, type Hex } from "viem";

export function encodeStablecoinCreateParams(
  name: string,
  symbol: string,
  initialAdmin: Address,
  currency: string,
): Hex {
  return encodeAbiParameters(
    parseAbiParameters("(uint8 version, string name, string symbol, address initialAdmin, string currency)"),
    [{ version: 1, name, symbol, initialAdmin, currency }],
  );
}

export function encodeAssetCreateParams(
  name: string,
  symbol: string,
  initialAdmin: Address,
  decimals: number,
): Hex {
  return encodeAbiParameters(
    parseAbiParameters("(uint8 version, string name, string symbol, address initialAdmin, uint8 decimals)"),
    [{ version: 1, name, symbol, initialAdmin, decimals }],
  );
}
```

The parenthesized type string makes it **one tuple parameter** containing all the fields — matching
`abi.encode(struct)` byte-for-byte. Passing the fields as separate parameters
(`parseAbiParameters("uint8, string, string, address, string")` with 5 separate args) is the bug —
it omits the outer offset slot.

### How to Verify You Got It Right

Compare against a known-good Solidity-generated encoding (e.g. from a successful `base-forge
script --broadcast` run, read back via `base-cast tx <hash>` or a trace). Byte-for-byte match is
the only real test — don't trust that it "looks plausible."

## `initCalls` Entries Are Normal Function-Call Encoding

Unlike the create-params struct, `initCalls` entries (`grantRole`, `updateSupplyCap`, `mint`,
`transferWithMemo`, ...) are encoded the standard way — they're real function calls, not a struct
argument, so no extra wrapping applies:

```typescript
import { encodeFunctionData } from "viem";

export function encodeGrantRole(role: Hex, account: Address): Hex {
  return encodeFunctionData({ abi: b20TokenAbi, functionName: "grantRole", args: [role, account] });
}
```

## Decoding Custom Errors

Add the relevant `error` entries to your ABI so viem can decode revert reasons into names instead
of raw selectors:

```typescript
export const b20TokenAbi = [
  // ...functions...
  { type: "error", name: "AccessControlUnauthorizedAccount", inputs: [{ name: "account", type: "address" }, { name: "neededRole", type: "bytes32" }] },
  { type: "error", name: "SupplyCapExceeded", inputs: [{ name: "cap", type: "uint256" }, { name: "attempted", type: "uint256" }] },
  { type: "error", name: "FeatureNotActivated", inputs: [{ name: "feature", type: "bytes32" }] },
] as const;
```

Then extract the decoded name from a failed `useWriteContract`/`writeContract` error via
`error.walk((e) => e instanceof ContractFunctionRevertedError)` and `revertError.data?.errorName` —
see [errors.md](errors.md) for the full error catalog and friendly-message mapping.

## Builder Code Attribution (ERC-8021)

If you have a Base Builder Code, append it to every transaction so onchain activity is attributed
to it. Both `viem`'s `writeContract`/`sendTransaction` accept a `dataSuffix` field directly
(wagmi passes it through transparently since it spreads extra params into the underlying viem call):

```typescript
writeContract({
  address: B20_FACTORY_ADDRESS,
  abi: b20FactoryAbi,
  functionName: "createB20",
  args: [variant, salt, params, initCalls],
  dataSuffix: BUILDER_CODE_DATA_SUFFIX, // your encoded code from base.dev
});
```

No extra package is required if you already have the pre-encoded suffix — `dataSuffix` is a
first-class viem parameter (`Hex`, appended to calldata, ~16 gas per non-zero byte).
