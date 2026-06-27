# Accepting B20 Payments (Merchant/App Integration)

This is the *receiving* side of B20 — for an app or merchant collecting payments and matching them
to orders. (For the issuer-side operations — minting, roles, supply cap — see
[post-deploy.md](post-deploy.md).)

## Table of Contents

- [Why Memos Instead of Plain `transfer`](#why-memos-instead-of-plain-transfer)
- [Full Pattern](#full-pattern)
- [Allowance-Based Collection](#allowance-based-collection)
- [Pre-Flight Simulation](#pre-flight-simulation)
- [Indexing at Scale](#indexing-at-scale)

## Why Memos Instead of Plain `transfer`

Standard ERC-20 `transfer`/`transferFrom` give you no way to tie an incoming payment to a specific
order without an off-chain side-channel (e.g. asking the payer to message you separately). B20's
`transferWithMemo`/`transferFromWithMemo` attach a `bytes32` reference directly to the onchain
transfer — read it back from the same transaction that moved the funds.

B20 is a full ERC-20 superset, so existing `transfer`/`balanceOf`/`approve` integrations keep
working unchanged if you don't need memo tracking yet — this is purely additive.

## Full Pattern

Read decimals once, send a memo'd payment, read the memo back from the receipt:

```js
import { parseUnits, stringToHex, hexToString, parseEventLogs } from 'viem';

const TOKEN    = '0xB200...'; // the B20 token you accept
const MERCHANT = '0x...';     // where payments land

const ABI = [
  { type: 'function', name: 'decimals', stateMutability: 'view', inputs: [], outputs: [{ type: 'uint8' }] },
  { type: 'function', name: 'transferWithMemo', stateMutability: 'nonpayable',
    inputs: [{ name: 'to', type: 'address' }, { name: 'amount', type: 'uint256' }, { name: 'memo', type: 'bytes32' }],
    outputs: [{ type: 'bool' }] },
  { type: 'event', name: 'Memo', inputs: [
    { name: 'caller', type: 'address', indexed: true },
    { name: 'memo',   type: 'bytes32', indexed: true },
  ] },
];

const decimals = await publicClient.readContract({ address: TOKEN, abi: ABI, functionName: 'decimals' });

const hash = await walletClient.writeContract({
  address: TOKEN, abi: ABI, functionName: 'transferWithMemo',
  args: [MERCHANT, parseUnits('10', decimals), stringToHex('order-42', { size: 32 })],
});

const receipt = await publicClient.waitForTransactionReceipt({ hash });
const [memo] = parseEventLogs({ abi: ABI, logs: receipt.logs, eventName: 'Memo' });
console.log(hexToString(memo.args.memo, { size: 32 }).replace(/\0+$/, '')); // "order-42"
```

**Always read `decimals()` from the token, never hardcode it** — STABLECOIN is fixed at 6, but
ASSET tokens can be anywhere in `[6, 18]`.

**Strip trailing null padding after `hexToString`** — `stringToHex(orderId, { size: 32 })` pads
the string to fill 32 bytes; `hexToString(..., { size: 32 })` decodes the full padded buffer, so
`.replace(/\0+$/, '')` is needed to get back the clean original string for display/comparison.

## Allowance-Based Collection

For pull-based payments (the merchant initiates, with prior `approve`), use
`transferFromWithMemo` instead — it "emits the same `Memo` event," so the read-back side of your
integration doesn't change:

```js
await walletClient.writeContract({
  address: TOKEN, abi: ABI, functionName: 'transferFromWithMemo',
  args: [payer, MERCHANT, parseUnits('10', decimals), stringToHex('order-42', { size: 32 })],
});
```

## Pre-Flight Simulation

B20 transfers can revert where a plain ERC-20 transfer wouldn't — a regulated issuer's
`TRANSFER_SENDER_POLICY`/`TRANSFER_RECEIVER_POLICY` (see [policy.md](policy.md)) or a paused
`TRANSFER` feature. Simulate with the same arguments before asking the payer to sign, so
`PolicyForbids`/`ContractPaused` surface as a clear error instead of a failed transaction after
gas was already spent:

```js
await publicClient.simulateContract({ address: TOKEN, abi: ABI, functionName: 'transferWithMemo', args: [...] });
```

See [errors.md](errors.md) for the full error catalog and a viem decoding pattern.

## Indexing at Scale

For matching payments to orders across many transactions (rather than reading one receipt right
after sending it), query `Transfer` and `Memo` events directly via the CDP SQL API rather than
running your own indexer:
[docs.cdp.coinbase.com/data/sql-api/b20-events](https://docs.cdp.coinbase.com/data/sql-api/b20-events).
Join `Transfer` and `Memo` rows on `(transactionHash, logIndex − 1)` — `Memo` is always emitted
immediately after the primary event it tags.
