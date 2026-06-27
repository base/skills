# Deploying a B20 Token

## Input Validation

Before constructing shell commands, validate all user-provided values:

- **rpc-url**: Must be a valid HTTPS URL (`^https://[^\s;|&]+$`). Reject non-HTTPS or malformed URLs.
- **account-address**: Must match `^0x[a-fA-F0-9]{40}$`.
- **token-salt**: Free text is fine — it's hashed — but reject shell metacharacters (`;`, `|`, `` ` ``, `$(`) before interpolating into a command.
- **name/symbol/currency**: Reject control characters; `currency` must be 3 uppercase `A`-`Z` letters for STABLECOIN.

Do not pass unvalidated user input into shell commands or directly into Solidity string literals
without considering injection into the generated script file.

## Foundry Script (CLI Path)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script, console} from "forge-std/Script.sol";

import {B20Constants} from "base-std/lib/B20Constants.sol";
import {B20FactoryLib} from "base-std/lib/B20FactoryLib.sol";
import {IB20Factory} from "base-std/interfaces/IB20Factory.sol";
import {StdPrecompiles} from "base-std/StdPrecompiles.sol";

contract CreateToken is Script {
    function run() external returns (address token) {
        address account = vm.envAddress("ACCOUNT_ADDRESS");
        bytes32 salt = keccak256(bytes(vm.envString("TOKEN_SALT")));

        bytes memory params = B20FactoryLib.encodeStablecoinCreateParams("My Token", "MYT", account, "USD");

        bytes[] memory initCalls = new bytes[](2);
        initCalls[0] = B20FactoryLib.encodeGrantRole(B20Constants.MINT_ROLE, account);
        initCalls[1] = B20FactoryLib.encodeUpdateSupplyCap(type(uint128).max); // no cap

        vm.startBroadcast();
        token = StdPrecompiles.B20_FACTORY.createB20(IB20Factory.B20Variant.STABLECOIN, salt, params, initCalls);
        vm.stopBroadcast();

        console.log("B20 token created at:", token);
    }
}
```

For `ASSET`, swap the params encoder and variant:

```solidity
bytes memory params = B20FactoryLib.encodeAssetCreateParams("My Token", "MYT", account, 18); // decimals 6-18
// ...
token = StdPrecompiles.B20_FACTORY.createB20(IB20Factory.B20Variant.ASSET, salt, params, initCalls);
```

Run it:

```bash
export RPC_URL=https://sepolia.base.org
export PRIVATE_KEY=0x...        # funded testnet/mainnet account — never commit this
export ACCOUNT_ADDRESS=0x...
export TOKEN_SALT=my-unique-salt-string

base-forge script script/CreateToken.s.sol --rpc-url $RPC_URL --private-key $PRIVATE_KEY --broadcast
```

> **Agent behavior:** Never write a private key into a tracked file. Use environment variables or
> Foundry's keystore (`cast wallet import`) and confirm `.env` is in `.gitignore` before proceeding.

## Salt Uniqueness

The token's address is deterministic: `address = f(variant, sender, salt)`. Reusing a salt for the
same `(variant, sender)` pair reverts `TokenAlreadyExists(address)` on the second attempt — it
doesn't create a second token at a new address.

- **CLI scripts**: derive the salt from something that changes per run if uniqueness matters (e.g.
  `keccak256(bytes("${symbol}-${block.timestamp}"))`), or let the user supply a fixed salt
  intentionally if they want a *predictable, reproducible* address.
- **Client-side (viem/wagmi)**: generate per-deploy, e.g.
  `keccak256(toBytes(\`${symbol}-${Date.now()}-${Math.random()}\`))`.

You can predict the resulting address before broadcasting with the factory's view function:

```solidity
function getB20Address(B20Variant variant, address sender, bytes32 salt) external view returns (address);
```

This never reverts — use it to confirm a salt is unused before spending gas on the real call.

## Variant Parameter Reference

| Field | ASSET | STABLECOIN |
|-------|-------|------------|
| `decimals` | Caller-supplied, must be in `[6, 18]` (reverts `InvalidDecimals` otherwise) | Fixed at 6, not a param |
| `currency` | n/a | Required, uppercase `A`-`Z` only (reverts `InvalidCurrency` otherwise) |
| Extra capabilities | Balance multiplier, batch mint/clawback, extra metadata | None — simpler role set |

## What `createB20` Actually Does

1. Derives the token's address from `(variant, sender, salt)`.
2. Decodes `params` per the leading version byte (see [encoding.md](encoding.md) for the
   client-side encoding pitfall).
3. Emits `B20Created`.
4. Runs each entry in `initCalls` in order, with factory-originated calls bypassing the new
   token's role gates and transfer-side policy gates for that window only (so `grantRole`,
   `updatePolicy`, and bootstrap transfers work without the factory holding any role itself).
   `MINT_RECEIVER_POLICY` is never bypassed, and pause state is never bypassed — if you want a
   start-paused token, sequence the `pause(...)` call last in `initCalls`.

**`createB20` itself never mints anything** — see [post-deploy.md](post-deploy.md) for how to
actually put supply into circulation.
