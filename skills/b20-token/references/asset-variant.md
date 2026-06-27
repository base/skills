# ASSET-Variant-Only Features

These three capabilities exist **only** on `B20Variant.ASSET` tokens (variant byte `0x00`) — the
`STABLECOIN` variant doesn't have them.

## Multiplier (Rebase)

A WAD-precision (18-decimal fixed point) multiplier applied to all balance reads. Raw balances are
stored unchanged on-chain; the multiplier scales what callers see.

```solidity
function multiplier() external view returns (uint256);                    // current multiplier
function scaledBalanceOf(address account) external view returns (uint256); // raw balance × multiplier
function toScaledBalance(uint256 raw) external view returns (uint256);
function toRawBalance(uint256 scaled) external view returns (uint256);
function updateMultiplier(uint256 newMultiplier) external; // gated by OPERATOR_ROLE
```

Use case: rebasing tokens (e.g. a yield-bearing wrapper) without rewriting every holder's stored
balance on every rebase — only the multiplier changes.

## Announcements

On-chain disclosure brackets that wrap sensitive operations (batch mints, multiplier updates) with
a public notice period, gated by `OPERATOR_ROLE`:

```solidity
function announce(bytes[] calldata internalCalls, bytes32 id, string calldata description, string calldata uri) external;
```

Behavior:
1. Emits `Announcement` (with `id`, `description`, `uri`).
2. Executes `internalCalls` in order.
3. Emits `EndAnnouncement`.

**`id` must be unique forever** — reusing one is a contract-level mistake, not just bad practice
(treat it like a nonce). Inner call reverts surface wrapped in `InternalCallFailed`, not the raw
inner revert — when debugging an `announce()` failure, the actual cause is one level deeper than
the visible error.

## Batch Mint

```solidity
function batchMint(address[] calldata recipients, uint256[] calldata amounts) external; // gated by MINT_ROLE
```

Mints to many recipients in a single call — `recipients` and `amounts` must be parallel arrays.
Each recipient is still subject to `MINT_RECEIVER_POLICY` individually. **Should be wrapped in
`announce()`** for transparency on large distributions (e.g. an airdrop) — this is a convention,
not an enforced requirement.

```solidity
bytes[] memory mintCall = new bytes[](1);
mintCall[0] = abi.encodeCall(IB20Asset.batchMint, (recipients, amounts));
token.announce(mintCall, keccak256("airdrop-2024-q1"), "Q1 2024 community airdrop", "ipfs://...");
```

## Extra Metadata (Key-Value Store)

A free-form string-keyed metadata store, separate from `name`/`symbol`/`contractURI`:

```solidity
function extraMetadata(string calldata key) external view returns (string memory);
function updateExtraMetadata(string calldata key, string calldata value) external; // gated by METADATA_ROLE
```

Passing an empty `value` removes the entry. Use this for arbitrary project-specific metadata (e.g.
`"category"` → `"gaming"`) that doesn't warrant a dedicated field.

## Building the initCalls Helpers (B20FactoryLib)

```solidity
function encodeBatchMint(address[] memory recipients, uint256[] memory amounts) internal pure returns (bytes memory) {
    return abi.encodeCall(IB20Asset.batchMint, (recipients, amounts));
}

function encodeUpdateMultiplier(uint256 newMultiplier) internal pure returns (bytes memory) {
    return abi.encodeCall(IB20Asset.updateMultiplier, (newMultiplier));
}

function encodeUpdateExtraMetadata(string memory key, string memory value) internal pure returns (bytes memory) {
    return abi.encodeCall(IB20Asset.updateExtraMetadata, (key, value));
}
```

These are normal function-call encodings (not the struct-as-tuple gotcha from
[encoding.md](encoding.md)) — `encodeFunctionData` in viem works the same way if doing this
client-side.
