# Metadata Updates and ERC-2612 Permit

## Contract URI (ERC-7572)

```solidity
function contractURI() external view returns (string memory);
function updateContractURI(string calldata newUri) external; // gated by METADATA_ROLE
```

Off-chain JSON metadata (logo, description, socials), following the
[ERC-7572](https://eips.ethereum.org/EIPS/eip-7572) convention that wallets/explorers already know
to look for.

## Name and Symbol Updates

Both gated by `METADATA_ROLE`:

```solidity
function updateName(string calldata newName) external;     // emits NameUpdated + EIP712DomainChanged
function updateSymbol(string calldata newSymbol) external;  // emits SymbolUpdated only
```

**`updateName` rotates the EIP-712 domain separator** (because `name` is part of the domain — see
below) and emits `EIP712DomainChanged` (ERC-5267) in addition to `NameUpdated`. `updateSymbol`
does not affect the domain at all — `symbol` isn't part of the EIP-712 domain.

> **Agent behavior:** If a user renames a token that has outstanding `permit` signatures pending
> (signed but not yet submitted), warn them those signatures become invalid — the domain separator
> they signed against no longer matches.

## ERC-2612 Permit (Gasless Approvals)

B20 implements the full ERC-2612 surface:

```solidity
function nonces(address owner) external view returns (uint256);          // current permit nonce
function permit(address owner, address spender, uint256 value, uint256 deadline, uint8 v, bytes32 r, bytes32 s) external;
function DOMAIN_SEPARATOR() external view returns (bytes32);
function eip712Domain() external view returns (uint8 fields, string memory name, string memory version, uint256 chainId, address verifyingContract, bytes32 salt, uint256[] memory extensions); // ERC-5267
```

EIP-712 domain shape: `(name, version, chainId, verifyingContract)` — `version` is fixed at the
literal string `"1"` (not configurable, not the token's own versioning).

### Key Constraints

- **ECDSA signatures only** — `permit` does **not** accept ERC-1271 contract signatures. A smart
  contract wallet (e.g. a Safe) cannot use `permit` directly; it must call `approve` normally.
- `nonces(owner)` increments by exactly 1 on each successful `permit` — replay-safe.
- Expired (`deadline < block.timestamp`) reverts `ExpiredSignature(deadline)`.
- Signer mismatch reverts `InvalidSigner(recovered, claimed)`.

### Client-Side Signing (viem)

```typescript
const domain = {
  name: await tokenContract.read.name(),
  version: "1",
  chainId,
  verifyingContract: tokenAddress,
} as const;

const types = {
  Permit: [
    { name: "owner", type: "address" },
    { name: "spender", type: "address" },
    { name: "value", type: "uint256" },
    { name: "nonce", type: "uint256" },
    { name: "deadline", type: "uint256" },
  ],
} as const;

const signature = await walletClient.signTypedData({
  account,
  domain,
  types,
  primaryType: "Permit",
  message: { owner, spender, value, nonce, deadline },
});
```

Re-fetch `name()` (not a hardcoded string) if there's any chance `updateName` has been called —
using a stale name produces a domain mismatch and `InvalidSigner`.
