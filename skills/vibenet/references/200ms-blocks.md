# 200ms native blocks (Cobalt) on vibenet

Querying, streaming, and timing transactions against vibenet's 200ms canonical
blocks. For network endpoints and install, see the [skill root](../SKILL.md).
**None of this needs the viem fork** — stock `npm install viem` is enough for
everything on this page except the 8130 smart-account send at the end.

## What changed

Cobalt moves Base block production from one block every 2s to **five complete
canonical blocks per second**. Each 200ms block has its own number, hash, state
root, receipts, and unsafe → safe → finalized lifecycle. It **replaces
Flashblocks** (the pre-Cobalt preconfirmation stream); Flashblocks production
stops and the `"pending"` tag has no preconfirmation meaning any more.

| Network | Status |
|---|---|
| vibenet (`84538453`) | **Live** — experimental, "may change, don't base production decisions on it" |
| Base Sepolia / Mainnet | Not active; activation and client versions TBD |

The block header keeps its **seconds** `timestamp`, and so do `eth_call`,
transaction validity windows, and EVM `block.timestamp`. The sub-second part
comes from a **BaseTime** metadata deposit at `tx[1]` of every block:

```
full_ms(block) = 1000 * block.timestamp + millisPart      millisPart ∈ {0, 200, 400, 600, 800}
full_ms(child) = full_ms(parent) + 200                    (no skipped slots)
```

RPC responses expose the full millisecond value as extra **optional** fields
(omitted for pre-Cobalt or pruned history, so always treat them as possibly
missing):

| Where | Field | Live on `rpc.vibes.base.org`? |
|---|---|---|
| `eth_getBlockByNumber` / `eth_getBlockByHash` | `timestampMs` (hex quantity) | yes |
| `eth_subscribe("newHeads")` | `timestampMs` | yes (`wss://rpc.vibes.base.org/ws`) |
| `eth_getTransactionByHash` / `…ByBlock*AndIndex` (mined tx) | `blockTimestamp` + `blockTimestampMs` | yes |
| `eth_getLogs`, `eth_getFilterLogs/Changes`, `eth_subscribe("logs")` | `blockTimestampMs` on each log | yes |
| `eth_getTransactionReceipt` | `blockTimestampMs` on **`receipt.logs[i]` only** — nothing at the receipt top level | yes |
| `eth_getHeaderByNumber/Hash`, `eth_getBlockReceipts` | `timestampMs` per spec | **no** — `rpc method is not whitelisted` (-32601) on the public RPC |

Worked example from the docs: a block at 42.200s has `timestamp: 0x2a`,
`timestampMs: 0xa4d8`.

### The BaseTime deposit (`tx[1]`) and predeploy

| | |
|---|---|
| Position | `tx[1]` in every block, right after the L1-info deposit at `tx[0]`, before user txs |
| Type / from | Deposit `0x7e` from `0xDeaDDEaDDeAdDeAdDEAdDEaddeAddEAdDEAd0001` |
| To | BaseTime predeploy `0x4200000000000000000000000000000000000030` |
| Calldata | `setTimestampMillisPart(uint16)` — selector `0x86bdf394` + 32-byte part |
| Predeploy getters | `timestampMillisPart()` → `uint16` (selector `0x7b2fea99`), `timestampMs()` → `uint256` (selector `0x5745a677`) |
| Implementation | `0xc0D3C0d3C0d3C0D3c0d3C0d3c0D3C0d3c0d30030` behind the proxy |

Because the deposit executes before every user transaction, a contract can read
the current block's millisecond time from the predeploy during execution:

```solidity
interface IBaseTime {
    function timestampMillisPart() external view returns (uint16); // 0 | 200 | 400 | 600 | 800
    function timestampMs() external view returns (uint256);        // 1000 * block.timestamp + part
}
IBaseTime constant BASE_TIME = IBaseTime(0x4200000000000000000000000000000000000030);
// block.timestamp is still whole seconds.
```

## Query a block

Stock viem keeps unknown RPC fields, so `getBlock` returns `timestampMs` — but
as the **raw hex string**, untyped (the `Block` type doesn't know about it).
Convert it yourself and treat it as optional:

```ts
import { createPublicClient, http, hexToBigInt, decodeFunctionData, parseAbi, type Hex } from "viem";

const vibenet = {
  id: 84538453,
  name: "vibenet",
  nativeCurrency: { name: "Ether", symbol: "ETH", decimals: 18 },
  rpcUrls: { default: { http: ["https://rpc.vibes.base.org"], webSocket: ["wss://rpc.vibes.base.org/ws"] } },
  blockTime: 200, // lets viem pick sane defaults, but see "Polling" below
} as const;
const client = createPublicClient({ chain: vibenet, transport: http() });

// Cobalt fields ride along untyped — declare them once.
type CobaltBlock = { timestampMs?: Hex };
type CobaltTx = { blockTimestampMs?: Hex };

const BASE_TIME = "0x4200000000000000000000000000000000000030";
const baseTimeAbi = parseAbi([
  "function timestampMillisPart() view returns (uint16)",
  "function timestampMs() view returns (uint256)",
  "function setTimestampMillisPart(uint16)",
]);

const block = await client.getBlock({ includeTransactions: true }); // latest
const raw = (block as unknown as CobaltBlock).timestampMs;
const timestampMs = raw ? hexToBigInt(raw) : undefined; // undefined = pre-Cobalt/pruned
const millisPart = timestampMs !== undefined ? timestampMs - block.timestamp * 1000n : undefined;

// tx[1] is the BaseTime deposit; decode the part it wrote.
const baseTimeTx = block.transactions[1];
const { args: [partFromTx] } = decodeFunctionData({ abi: baseTimeAbi, data: baseTimeTx.input });

// The predeploy agrees, as long as you pin the same block.
const partFromChain = await client.readContract({
  address: BASE_TIME, abi: baseTimeAbi, functionName: "timestampMillisPart", blockNumber: block.number,
});

console.log({ number: block.number, timestamp: block.timestamp, timestampMs, millisPart, partFromTx, partFromChain });
// e.g. { number: 2845536n, timestamp: 1788960994n, timestampMs: 1788960994200n, millisPart: 200n, partFromTx: 200, partFromChain: 200 }
```

Raw JSON-RPC, if you'd rather `curl`:

```bash
RPC=https://rpc.vibes.base.org
# block → timestamp (s) + timestampMs
curl -s $RPC -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_getBlockByNumber","params":["latest",false]}' \
  | jq '.result | {number, timestamp, timestampMs}'
# logs → blockTimestampMs on every log
curl -s $RPC -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[{"fromBlock":"latest","toBlock":"latest"}]}' \
  | jq '.result[0] | {blockNumber, blockTimestamp, blockTimestampMs}'
# predeploy → current millisecond part
curl -s $RPC -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_call","params":[{"to":"0x4200000000000000000000000000000000000030","data":"0x7b2fea99"},"latest"]}'
```

Anything mined carries the block's ms time too: `getLogs` /
`getTransactionReceipt(...).logs[i].blockTimestampMs` and
`getTransaction(...).blockTimestampMs` (stock viem; the 8130 fork's
`getTransaction` is the exception — see Gotchas).

## Stream blocks

Use the WebSocket endpoint — note the **`/ws` path**; the bare host refuses the
upgrade. Every block arrives (~5/s), each with `timestampMs`:

```ts
import { createPublicClient, webSocket, hexToBigInt } from "viem";

const ws = createPublicClient({ transport: webSocket("wss://rpc.vibes.base.org/ws") });
const unwatch = ws.watchBlocks({
  onBlock: (block) => {
    const ms = hexToBigInt((block as any).timestampMs);
    console.log(block.number, ms, `.${ms % 1000n}`); // 2845550n 1788960997000n .0 → .200 → .400 …
  },
});
```

Live-confirmed: 10 consecutive `watchBlocks` events were contiguous block
numbers exactly 200ms apart in `timestampMs`.

Over **HTTP**, `watchBlocks` polls at the client's `pollingInterval` (see
Polling) and therefore *skips* blocks at 200ms cadence; pass
`emitMissed: true` if you need every block, or use the WebSocket transport.

Raw subscription, if you're not using viem:

```json
{"jsonrpc":"2.0","id":1,"method":"eth_subscribe","params":["newHeads"]}
```

`eth_subscribe("logs", …)` and `eth_subscribe("transactionReceipts")` also
work on `/ws`. `eth_subscribe("newFlashblocks")` still *returns a subscription
id* on vibenet but **never emits** — a silent no-op, not an error.

### Migrating from Flashblocks

| Flashblocks | Cobalt |
|---|---|
| `eth_subscribe("newFlashblocks")` | `eth_subscribe("newHeads")` |
| `eth_subscribe("pendingLogs")` | `eth_subscribe("logs")` |
| `eth_subscribe("newFlashblockTransactions")` | `newHeads`, then fetch each block's txs |
| `eth_getBlockByNumber("pending")`, `eth_getBalance/eth_call/eth_estimateGas/eth_getTransactionCount(…, "pending")`, `eth_getLogs` to `"pending"` | the same call with `"latest"` — canonical 200ms state |

`"pending"` still *answers* on vibenet (it returns the block being built) but it
is not a preconfirmation stream and there is no replacement for one: the
canonical block simply lands 200ms later. `safe` and `finalized` lag the head by
minutes (~1000 and ~2000 blocks when measured), so don't wait on them in demos.

## Polling: make viem keep up

viem's client `pollingInterval` defaults to **4000ms** on a chain object without
`blockTime`, and to `max(blockTime / 2, 500)` — i.e. a **500ms floor** — with
`blockTime: 200`. Every `waitForTransactionReceipt` / `watchBlocks` /
`watchBlockNumber` over HTTP inherits it, so a 200ms chain looks like a 4s (or
0.5s) chain unless you say otherwise. Pass `pollingInterval` explicitly on the
call (or the client) when you're timing anything:

```ts
const receipt = await client.waitForTransactionReceipt({ hash, pollingInterval: 100 });
```

The 8130 fork's `waitForTransactionReceipt` (from `viem/eip8130`) has its own
default of 500ms, independent of the client — same fix, `pollingInterval: 100`.
It also makes **2–3 RPC round-trips per iteration** (receipt, then a
`getTransaction` probe for the tx's expiry, then a block-timestamp read), so
from a browser at ~150ms RTT each iteration costs ~0.5s and a tx that landed in
one 200ms block still reports ~1.4s (live-observed). When the number matters,
poll `getTransactionReceipt` from `viem/eip8130` yourself every 100ms — one
call per iteration — and keep `allPhasesSucceeded(receipt.eip8130)` for the
verdict.

## Send a transaction and see which 200ms block it landed in

### Plain EOA (stock viem)

```ts
import { createPublicClient, createWalletClient, http, hexToBigInt, parseEther, type Hex } from "viem";
import { privateKeyToAccount, generatePrivateKey } from "viem/accounts";
// `vibenet` chain object as above (with webSocket + blockTime: 200)

const account = privateKeyToAccount(generatePrivateKey()); // throwaway devnet key
const client = createPublicClient({ chain: vibenet, transport: http() });
const wallet = createWalletClient({ account, chain: vibenet, transport: http() });

// Fund it (0.1 ETH per drip, 10s cooldown per address and per IP), then poll the balance.
await fetch("https://api.vibes.base.org/api/vibenet/faucet/drip", {
  method: "POST", headers: { "content-type": "application/json" },
  body: JSON.stringify({ address: account.address }),
});
while ((await client.getBalance({ address: account.address })) === 0n) await new Promise((r) => setTimeout(r, 100));

const sentAt = Date.now();
const hash = await wallet.sendTransaction({ to: "0x000000000000000000000000000000000000dEaD", value: parseEther("0.0001") });
const receipt = await client.waitForTransactionReceipt({ hash, pollingInterval: 100 });
const minedAt = Date.now();

const block = await client.getBlock({ blockNumber: receipt.blockNumber });
const blockMs = hexToBigInt((block as unknown as { timestampMs: Hex }).timestampMs);
console.log({
  hash, block: receipt.blockNumber, blockTimestampMs: blockMs, millisPart: blockMs % 1000n,
  receiptAfterBroadcastMs: minedAt - sentAt,
});
```

Measured on 2026-09-09 (three sends, from a client ~150ms RTT from the RPC):

| Metric | Observed |
|---|---|
| Faucet drip → balance visible | 0.4–0.7s |
| `sendTransaction` broadcast → receipt (HTTP, 100ms polling) | 0.50–0.53s |
| Same over the WebSocket client (`newHeads`-driven wait) | 0.44–0.69s |
| Inclusion block's `timestampMs` − broadcast wall-clock | +0.26–0.36s (i.e. the next or second slot) |

Most of the wall-clock in a naive script is *before* broadcast: viem's
`sendTransaction` does chain-id, nonce, gas and fee round-trips first
(~0.7–1.1s at that RTT). Pass `nonce`, `gas`, `maxFeePerGas` and
`maxPriorityFeePerGas` yourself if you want the send to be one round-trip.

### 8130 smart account (viem fork)

Same shape as the create-and-send example in
[eip8130-accounts.md](eip8130-accounts.md), with two 200ms-specific details:
poll fast, and read the millisecond time **from the block**, because the 8130
`getTransaction` doesn't carry it and a `0x79` tx object inside a block body has
no `hash` field to look up.

```ts
import { hexToBigInt, parseEther, type Hex } from "viem";
import { sendTransaction, waitForTransactionReceipt, allPhasesSucceeded } from "viem/eip8130";

const hash = await sendTransaction(client, { account, calls, gas /* from estimateGas, +20% */ });
const receipt = await waitForTransactionReceipt(client, { hash, pollingInterval: 100 });
if (!allPhasesSucceeded(receipt.eip8130)) throw new Error("a phase reverted");

const block = await client.getBlock({ blockNumber: BigInt(receipt.blockNumber) });
const blockMs = hexToBigInt((block as unknown as { timestampMs: Hex }).timestampMs);
console.log(receipt.blockNumber, blockMs, blockMs % 1000n);
```

Measured on 2026-09-09 with a fresh account (deploy + first batch in one tx):

| Metric | Observed |
|---|---|
| `sendTransaction` (prepare + sign + broadcast) | 0.75s |
| Broadcast → 8130 receipt (100ms polling) | 0.47s |
| `eth_getCode` non-empty after the create receipt | first poll, <0.1s (the old "~1 block" lag is now ~200ms at most) |
| Hosted payer accepts a sponsored tx right after the self-paid deploy | first attempt, no `actor is not bound` retry needed |
| `sendTransactionSync` (`eth_sendRawTransactionSync`) | **not allowlisted** on `rpc.vibes.base.org` — use `sendTransaction` + `waitForTransactionReceipt` |

## Gotchas (all live-confirmed on vibenet)

- **`timestampMs` / `blockTimestampMs` arrive as hex strings through viem**, not
  `bigint` like `timestamp`. `hexToBigInt` them before doing arithmetic or
  comparing to `timestamp * 1000n`. They are also absent from viem's types —
  cast, as above.
- **The receipt top level has no ms field.** It's on `receipt.logs[i]`. A tx
  that emits no logs → fetch its block.
- **The 8130 fork's `getTransaction` drops `blockTimestampMs`** (it rebuilds the
  object from the nested `tx` body), and **`0x79` tx objects returned inside a
  block or via `eth_getTransactionByBlockNumberAndIndex` have no `hash` key**.
  Keep the hash `sendTransaction` returned and read the block's `timestampMs`.
- **`eth_getHeaderByNumber/Hash` and `eth_getBlockReceipts` are not allowlisted**
  on the public RPC even though the spec adds `timestampMs` to them. Use
  `eth_getBlockByNumber` and per-tx receipts. `eth_sendRawTransactionSync`
  isn't either, so the fork's `sendTransactionSync` fails with
  `rpc method is not whitelisted` — it is not a 200ms feature you can use here.
- **WebSocket is `wss://rpc.vibes.base.org/ws`.** Without `/ws` (or on
  `ws.vibes.base.org`) the upgrade fails with a non-101 status.
- **Default polling hides the speed-up** — 4000ms without `blockTime`, 500ms
  floor with it. Always pass `pollingInterval` on waits and watches you time.
- **`"pending"` answers but isn't preconfirmation**; `safe`/`finalized` are
  minutes behind the head.
- **Devnet state resets** (block numbers and tx hashes above are from one
  session and will not resolve later). Don't hardcode them in tests.
- Everything on this page is vibenet-only today; Base Sepolia and Mainnet still
  produce 2s blocks without `timestampMs`.

## Reference

- Spec + RPC behaviour: https://docs.base.org/upgrades/cobalt/200ms-blocks
- Flashblocks migration table: https://docs.base.org/upgrades/cobalt/migrate-from-flashblocks
- Vibenet overview: https://docs.base.org/build-on-base/test-on-vibenet
