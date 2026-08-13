# Payer gas sponsorship (ERC-8168)

Sponsoring gas for 8130 accounts with a payer service — the path to gasless
onboarding (account creation + first transaction with zero user ETH). For
account creation and core concepts, read
[eip8130-accounts.md](eip8130-accounts.md) first.

A **payer** is a service that co-signs `payer_auth` to pay gas (sponsored or
in ERC-20). The hosted vibenet payer lives at
`https://api.vibes.base.org/api/vibenet/account/payer` and supports **both**
ERC-8168 modes:

- `mode: "send"` (default) — payer co-signs and submits (`payer_sendTransaction`)
- `mode: "sign"` — payer co-signs only; you broadcast with `eth_sendRawTransaction`

## Sponsor a first transaction (gasless onboarding)

```ts
import type { Hex } from "viem";
import { createPayerClient, sendSponsoredCalls } from "viem/eip8168";
import { waitForTransactionReceipt } from "viem/eip8130";

const payerClient = createPayerClient({
  url: "https://api.vibes.base.org/api/vibenet/account/payer",
});

// Default mode:"send" — payer co-signs and broadcasts, resolving with an
// OBJECT: `{ transactionHash }`. Destructure it. (The declared return type says
// otherwise — see the note below — so TypeScript needs a cast.)
const { transactionHash: hash } = (await sendSponsoredCalls(client, {
  account,
  payerClient,
  accountChanges: [account.createChange], // deploy rides in the first sponsored tx
  calls: [{ to: account.address, value: 0n, data: "0x" }],
  context: { flow: "transact" }, // budgets free grants per (sender, flow)
})) as unknown as { transactionHash: Hex };
const receipt = await waitForTransactionReceipt(client, { hash });
```

No faucet call and no user ETH is needed anywhere in this flow — the payer's
`payer_auth` makes the protocol debit gas from the payer, not the sender.

For self-submit (e.g. custom RPC / retry control), pass `mode: "sign"` — the
call then resolves with the signed raw transaction, which you broadcast yourself
with `eth_sendRawTransaction`.

**The declared return type is wrong.** `SendSponsoredCallsReturnType` is typed
as a union of hex strings (`SendTransactionReturnType | SignTransactionReturnType`),
but `mode: "send"` resolves with `{ transactionHash }` at runtime —
live-confirmed against the hosted payer. Passing the raw result into
`waitForTransactionReceipt` fails at the RPC layer with
`invalid type: map, expected 32 bytes`, which points nowhere near the cause. The
union also isn't assignable to `Hex`, so narrowing needs `as unknown as`.

## Wire protocol (JSON-RPC over the payer URL)

Under the hood `sendSponsoredCalls` runs the ERC-8168 flow: fetch terms with
`payer_getTerms`, build and sign `sender_auth` with `payer` set and
`payer_auth` empty, then hand off via `payer_sendTransaction` (send mode) or
`payer_signTransaction` (sign mode). `payer_getTerms` +
`payer_sendTransaction` are the required pair every payer implements;
`payer_signTransaction` is optional (advertised in the terms' `methods`).
Rejections come back as JSON-RPC error `-32000` with a
`data: { code, reason }` envelope — branch on the string `code` (e.g.
`BUDGET_EXHAUSTED`, `SENDER_LIMIT_REACHED`, whose context includes a
`validFor` retry hint). Full types: `src/eip8168/types.ts` on
the fork branch.

## Notes

- Subsequent sponsored txs omit `account.createChange` — only the first tx
  carries it.
- **Don't sponsor immediately after a self-paid deploy.** Account config
  propagates ~1 block behind the receipt (the same lag as `eth_getCode` and
  config read-backs), and the payer validates against the lagging state — so a
  sponsored tx sent right after a successful deploy is rejected with
  `EIP-8130 validation failed: actor is not bound`, surfaced as viem's
  `InvalidInputRpcError: Missing or invalid parameters`. Neither message points
  at timing. Retry on `actor is not bound` (a few seconds is enough) or wait for
  the account's code read-back before sponsoring. Live-confirmed: the same call
  fails immediately after deploy and succeeds ~6s later.
- `context.flow` lets the hosted payer budget free grants per
  `(sender, flow)` pair; pick a stable string per product surface
  (e.g. `"onboarding"`, `"transact"`).
- Payer standard: https://eip.tools/eip/8168 (viem module:
  `src/eip8168` on the fork branch).
