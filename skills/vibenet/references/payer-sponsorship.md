# Payer gas sponsorship (ERC-8168)

Sponsoring gas for 8130 accounts with a payer service — the path to gasless
onboarding (account creation + first transaction with zero user ETH). For
account creation and core concepts, read
[eip8130-accounts.md](eip8130-accounts.md) first.

A **payer** is a service that co-signs `payer_auth` to pay gas (sponsored or
in ERC-20). The hosted vibenet payer lives at
`https://vibes.base.org/api/vibenet/account/payer` and supports **both**
ERC-8168 modes:

- `mode: "send"` (default) — payer co-signs and submits (`payer_sendTransaction`)
- `mode: "sign"` — payer co-signs only; you broadcast with `eth_sendRawTransaction`

## Sponsor a first transaction (gasless onboarding)

```ts
import { createPayerClient, sendSponsoredCalls } from "viem/experimental/eip8168";
import { waitForTransactionReceipt8130 } from "viem/experimental/eip8130";

const payerClient = createPayerClient({
  url: "https://vibes.base.org/api/vibenet/account/payer",
});

// Default mode:"send" — payer co-signs and broadcasts. Returns the tx HASH
// directly (SendTransactionReturnType) — do NOT destructure { transactionHash }.
const hash = await sendSponsoredCalls(client, {
  account,
  payerClient,
  accountChanges: [account.createChange], // deploy rides in the first sponsored tx
  calls: [{ to: account.address, value: 0n, data: "0x" }],
  context: { flow: "transact" }, // budgets free grants per (sender, flow)
});
const receipt = await waitForTransactionReceipt8130(client, { hash });
```

No faucet call and no user ETH is needed anywhere in this flow — the payer's
`payer_auth` makes the protocol debit gas from the payer, not the sender.

For self-submit (e.g. custom RPC / retry control), pass `mode: "sign"` — the
call then resolves with the signed raw transaction
(`SignTransactionReturnType`), which you broadcast yourself with
`eth_sendRawTransaction`. Both modes return a plain hex string, not an
object: the tx hash in `send` mode, the signed tx in `sign` mode.

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
`validFor` retry hint). Full types: `src/experimental/eip8168/types.ts` on
the fork branch.

## Notes

- Subsequent sponsored txs omit `account.createChange` — only the first tx
  carries it.
- `context.flow` lets the hosted payer budget free grants per
  `(sender, flow)` pair; pick a stable string per product surface
  (e.g. `"onboarding"`, `"transact"`).
- Payer standard: https://eip.tools/eip/8168 (viem module:
  `src/experimental/eip8168` on the fork branch).
