# Post-Deploy: Minting, Roles, Supply Cap, Memos

## Deploying Never Mints — This Trips Up Almost Everyone

`createB20` creates the token and runs `initCalls` (typically `grantRole` + `updateSupplyCap`).
**No tokens exist until something calls `mint()` separately.** If a user reports "I deployed with
a 1M supply but my balance is 0," this is almost always the cause — they set a supply *cap*
(ceiling), not an actual mint.

```bash
base-cast send <TOKEN_ADDRESS> "mint(address,uint256)" <RECIPIENT> <AMOUNT_RAW> \
  --rpc-url $RPC_URL --private-key $PRIVATE_KEY
```

`AMOUNT_RAW` is in the token's smallest unit — multiply by `10^decimals` (6 for STABLECOIN, 6–18
for ASSET). E.g. 1000 tokens at 6 decimals = `1000000000`.

This call **requires the sender to hold `MINT_ROLE`** — see below if they don't.

## Role-Based Access Control

| Role | Required for |
|------|---------------|
| `DEFAULT_ADMIN_ROLE` | Granting/revoking other roles. **Held by the deployer automatically** — but does *not* itself permit minting. |
| `MINT_ROLE` | `mint`, `mintWithMemo` |
| `BURN_ROLE` | `burn`, `burnWithMemo` |
| `BURN_BLOCKED_ROLE` | `burnBlocked` (seizing tokens from an address already denied under `TRANSFER_SENDER_POLICY` — cannot target an arbitrary, non-blocked address) |
| `PAUSE_ROLE` / `UNPAUSE_ROLE` | `pause`/`unpause` (granular: TRANSFER/MINT/BURN bits) |

Granting `MINT_ROLE` to yourself (or anyone) after deploy, if it wasn't done in `initCalls`:

```bash
base-cast send <TOKEN_ADDRESS> "grantRole(bytes32,address)" \
  $(base-cast keccak "MINT_ROLE") <ACCOUNT_ADDRESS> \
  --rpc-url $RPC_URL --private-key $PRIVATE_KEY
```

Only the holder of a role's admin role (by default `DEFAULT_ADMIN_ROLE`) can grant/revoke it.

### Becoming Trustless: `renounceLastAdmin()`

Unlike a plain `renounceRole(DEFAULT_ADMIN_ROLE, ...)` — which reverts `LastAdminCannotRenounce`
if called by the sole remaining admin — there's a dedicated function for deliberately giving up
all admin power:

```solidity
function renounceLastAdmin() external; // reverts NotSoleAdmin if other admins still exist
```

This is **irreversible** and puts the token into a permanent zero-admin state: no more role
grants/revokes/admin changes, ever. **Before calling it**, revoke or hand off any role you don't
want frozen in its current state — existing holders of `PAUSE_ROLE`/`BURN_BLOCKED_ROLE`/etc. keep
their powers after renouncement; only the ability to *change* role assignments goes away.

> **Agent behavior:** If a user asks "how do I make my token trustless," explain this tradeoff
> explicitly before suggesting the call — it's a one-way door.

## Supply Cap

```bash
base-cast send <TOKEN_ADDRESS> "updateSupplyCap(uint256)" <CAP_RAW> \
  --rpc-url $RPC_URL --private-key $PRIVATE_KEY
```

- `CAP_RAW` is in the token's smallest unit, same scaling as mint amounts.
- "No cap" sentinel: `type(uint128).max` (`B20Constants.MAX_SUPPLY_CAP`) — not literal infinity,
  but large enough to be unbounded in practice.
- The cap can be changed later by whoever holds the relevant admin role — it is not fixed at deploy
  time unless admin is renounced first.
- Minting beyond the cap reverts `SupplyCapExceeded(cap, attempted)`.

## Transfers With Memo (Payment References)

For tagging a payment to an order/invoice ID, use the memo'd variants instead of plain
`transfer`/`transferFrom`:

```bash
base-cast send <TOKEN_ADDRESS> "transferWithMemo(address,uint256,bytes32)" \
  <RECIPIENT> <AMOUNT_RAW> <MEMO_BYTES32> \
  --rpc-url $RPC_URL --private-key $PRIVATE_KEY
```

`MEMO_BYTES32` is typically a short string padded to 32 bytes (e.g. an order ID). In viem:

```typescript
import { stringToHex } from "viem";
const memo = stringToHex("order-42", { size: 32 }); // throws if the string doesn't fit in 32 bytes
```

This emits `Memo(address indexed caller, bytes32 indexed memo)` immediately after the standard
`Transfer` event — read it back from a receipt:

```typescript
import { parseEventLogs, hexToString } from "viem";
const [memoLog] = parseEventLogs({ abi: b20TokenAbi, logs: receipt.logs, eventName: "Memo" });
const orderId = hexToString(memoLog.args.memo, { size: 32 });
```

### Pre-Flight Simulation

B20 transfers can revert where plain ERC-20 transfers wouldn't — a regulated issuer's
`TRANSFER_SENDER_POLICY`/`TRANSFER_RECEIVER_POLICY` allowlist/blocklist, or a paused TRANSFER
feature. Simulate before asking the user to sign:

```typescript
await publicClient.simulateContract({ address, abi, functionName: "transferWithMemo", args: [...] });
```

This surfaces `PolicyForbids`/`ContractPaused` as a typed error before any signature is requested,
rather than as a failed-transaction surprise after the user already paid gas to attempt it.
