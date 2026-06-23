# Testing B20 Token Creation

base-std ships fully-functional Solidity mocks of all three precompiles, so creation scripts are testable with plain `forge test` — no fork, no RPC.

## BaseTest does the wiring

Inherit `BaseTest` from `base-std-test/lib/BaseTest.sol` (requires the `base-std-test/=lib/base-std/test/` remapping). Its `setUp`:

- etches `MockB20Factory`, `MockPolicyRegistry`, `MockActivationRegistry` at the canonical precompile addresses
- activates the `B20_ASSET`, `B20_STABLECOIN`, and `POLICY_REGISTRY` features (on a live chain the Base team controls activation; the mocks just turn it all on)
- provides labeled actors: `admin`, `alice`, `bob`, `attacker`

Always call `super.setUp()` when overriding.

## Structuring script + test

`vm.envAddress` in `run()` makes scripts hard to call from tests. Put the creation logic in a parameterized public function and keep `run()` as a thin env-reading wrapper:

```solidity
contract CreateMyToken is Script {
    function run() external returns (address) {
        return create(vm.envAddress("TOKEN_ADMIN"), vm.envAddress("TOKEN_MINTER"), vm.envAddress("TOKEN_TREASURY"));
    }

    function create(address admin, address minter, address treasury) public returns (address token) {
        // ... encode params + initCalls, call createB20 ...
    }
}
```

Then the test exercises the *exact* code that will run at deploy time. Note: when the test calls `create()` directly (no broadcast), `msg.sender` for `createB20` is the script contract — fine for testing config, but the deterministic address will differ from production. Don't drop `vm.startBroadcast`/`stopBroadcast` from `run()`-path code; under `forge test` without an active broadcast they are inert enough for this pattern, but if you hit prank/broadcast conflicts, move the broadcast calls into `run()` only.

## Example test

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {BaseTest} from "base-std-test/lib/BaseTest.sol";
import {B20Constants} from "base-std/lib/B20Constants.sol";
import {IB20Asset} from "base-std/interfaces/IB20Asset.sol";
import {StdPrecompiles} from "base-std/StdPrecompiles.sol";
import {CreateMyToken} from "../script/CreateMyToken.s.sol";

contract CreateMyTokenTest is BaseTest {
    IB20Asset internal token;
    address internal minter = makeAddr("minter");
    address internal treasury = makeAddr("treasury");

    function setUp() public override {
        super.setUp(); // etches the precompile mocks — without this every call reverts
        token = IB20Asset(new CreateMyToken().create(admin, minter, treasury));
    }

    function test_configuration() public view {
        assertEq(token.name(), "My Token");
        assertEq(token.symbol(), "MYT");
        assertEq(token.decimals(), 18);
        assertTrue(token.hasRole(B20Constants.DEFAULT_ADMIN_ROLE, admin));
        assertTrue(token.hasRole(B20Constants.MINT_ROLE, minter));
        assertEq(token.supplyCap(), 1_000_000e18);
        assertEq(token.balanceOf(treasury), 100_000e18);
        assertTrue(StdPrecompiles.B20_FACTORY.isB20Initialized(address(token)));
    }

    function test_minterCanMint_othersCannot() public {
        vm.prank(minter);
        token.mint(alice, 1e18);
        assertEq(token.balanceOf(alice), 1e18);

        vm.prank(attacker);
        vm.expectRevert(); // AccessControlUnauthorizedAccount
        token.mint(attacker, 1e18);
    }
}
```

## What to assert

Cover everything the user asked for, not just what's convenient:

- **Identity**: `name()`, `symbol()`, `decimals()`, `currency()` (stablecoin), `contractURI()`
- **Roles**: `hasRole(role, holder)` for every grant — and a negative check that `attacker` lacks them
- **Policies**: `policyId(scope)` equals the configured ID for every configured scope
- **Supply**: `supplyCap()`, `totalSupply()`, `balanceOf` for each initial-mint recipient
- **Behavior**: at least one positive and one negative path per feature configured (minter mints / non-minter reverts; blocked sender can't transfer; pauser pauses; etc.)
- **Bootstrap closed**: `factory.isB20Initialized(token)` is true (works against both mock and live backends)

For policy behavior tests, the built-in IDs avoid registry setup: `0` (`ALWAYS_ALLOW`) and `(uint64(IPolicyRegistry.PolicyType.ALLOWLIST) << 56) | 1` (`ALWAYS_BLOCK`) exercise both authorize and forbid paths. For realistic flows, create a policy on the mock registry in the test and add/remove members.

## Fork testing (optional)

The mocks are reference implementations of the live Rust precompiles. To validate against the real thing, base-std's pattern is `LIVE_PRECOMPILES=true` (skips the etch so calls hit the chain's precompiles) plus `--fork-url <base-rpc>`. Only relevant when verifying mock/live parity — day-to-day tests should use the default mock mode.
