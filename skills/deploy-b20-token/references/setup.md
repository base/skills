# B20 Setup

## Why Vanilla Foundry Doesn't Work

B20 contracts (`B20_FACTORY`, `ACTIVATION_REGISTRY`, `POLICY_REGISTRY`) are **precompiles** — they
have no deployed bytecode (`eth_getCode` returns `0x` for them even when fully live), and standard
`forge`/`cast`/`anvil` don't know how to simulate calls against them. Calling one with vanilla
Foundry aborts with:

```
Error: call to non-contract address
```

Base ships a patched Foundry build (`base-forge`, `base-cast`, `base-anvil`) that registers the
precompiles into the local EVM for simulation. Use these binaries for every B20 operation —
never the vanilla ones.

## Install

```bash
base-foundryup
```

Verify:

```bash
base-forge --version
```

## Project Setup

```bash
base-forge init my-b20-project
cd my-b20-project
base-forge install base/base-std --no-git
```

`foundry.toml`:

```toml
[profile.default]
src = "src"
out = "out"
libs = ["lib"]
base = true
remappings = [
    "base-std/=lib/base-std/src/",
    "base-std-test/=lib/base-std/test/",
]
```

`base = true` is what registers the precompiles for local simulation via `base-anvil` / script dry-runs.

## Library Surface

`base-std` exposes:

| Import | Purpose |
|--------|---------|
| `StdPrecompiles.sol` | Fixed addresses: `B20_FACTORY`, `ACTIVATION_REGISTRY`, `POLICY_REGISTRY` |
| `interfaces/IB20Factory.sol` | `createB20`, `getB20Address`, `B20Variant` enum, create-params structs |
| `interfaces/IB20.sol` | Full token interface — `mint`, `transferWithMemo`, roles, pause, permit |
| `interfaces/IActivationRegistry.sol` | `isActivated(bytes32)`, `checkActivated(bytes32)` |
| `lib/B20FactoryLib.sol` | Pure encoder helpers for `createB20` params and `initCalls` |
| `lib/B20Constants.sol` | Role hashes (`MINT_ROLE`, `BURN_ROLE`, ...), decimals bounds, `MAX_SUPPLY_CAP` |

Precompile addresses (stable across networks):

```solidity
address constant B20_FACTORY_ADDRESS = 0xB20f000000000000000000000000000000000000;
address constant ACTIVATION_REGISTRY_ADDRESS = 0x8453000000000000000000000000000000000001;
address constant POLICY_REGISTRY_ADDRESS = 0x8453000000000000000000000000000000000002;
```

## Networks

| Network | Chain ID | RPC |
|---------|----------|-----|
| Base Mainnet | 8453 | `https://mainnet.base.org` |
| Base Sepolia | 84532 | `https://sepolia.base.org` |
| Vibenet | 84538453 | `https://rpc.vibes.base.org` |
| Local | 31337 | `base-anvil` |

Always check activation before targeting a network — see
[activation-check.md](activation-check.md).
