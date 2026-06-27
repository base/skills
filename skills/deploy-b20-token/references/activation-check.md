# Checking B20 Activation Before You Deploy

B20 features are gated by Base's `ActivationRegistry` precompile. A network can have the
`B20_FACTORY` precompile **responding to calls** while the actual ASSET/STABLECOIN feature is
still **not activated** — in that state, `createB20` reverts with `FeatureNotActivated`, even
though read-only calls like `getB20Address` succeed fine.

**Always verify activation before attempting a deploy on an unfamiliar network.** This avoids a
wasted transaction (and the confusing experience of a read call working while the write call
reverts).

Use the bundled script rather than retyping the commands:

```bash
scripts/check-activation.sh https://mainnet.base.org
# ASSET activated:      false
# STABLECOIN activated: false
# (exits 1 — do not proceed with createB20 on this network)
```

Exit code `0` means both variants are activated; `1` means at least one isn't (or the registry
itself isn't reachable). The sections below explain what's happening if you need to debug it
manually instead.

## The Two Things to Check Are Different

| Check | What it tells you |
|-------|---|
| `eth_getCode` on `B20_FACTORY_ADDRESS` | **Nothing useful.** Precompiles are handled natively by the node, not via bytecode — this returns `0x` even when fully live. Don't use this as a liveness signal. |
| `ActivationRegistry.isActivated(feature)` | The actual, authoritative answer. |

## Command

```bash
REG=0x8453000000000000000000000000000000000001  # ActivationRegistry precompile
RPC=https://mainnet.base.org                     # or sepolia.base.org, rpc.vibes.base.org

base-cast call $REG "isActivated(bytes32)(bool)" $(base-cast keccak "base.b20_asset") --rpc-url $RPC
base-cast call $REG "isActivated(bytes32)(bool)" $(base-cast keccak "base.b20_stablecoin") --rpc-url $RPC
```

Both must return `true` for the variant you intend to deploy.

## Reading the Result

| Result | Meaning |
|--------|---|
| `isActivated` returns `true`/`false` cleanly | Registry is live; `false` means genuinely not activated yet — don't deploy. |
| `Error: contract ... does not have any code` on the **registry call itself** | The registry precompile isn't wired up on this network/node at all yet (earlier rollout stage than "not activated"). |
| `createB20` simulated and reverts `FeatureNotActivated` | Confirms the same thing at the factory level — useful as a second, independent check (see below). |

## Optional: Confirm via a Dry-Run Simulation

`base-cast call` on a non-view function performs an `eth_call` simulation without broadcasting —
safe to use as a definitive pre-flight check:

```bash
base-cast call 0xB20f000000000000000000000000000000000000 \
  "createB20(uint8,bytes32,bytes,bytes[])(address)" \
  1 0x0000000000000000000000000000000000000000000000000000000000000099 \
  "$PARAMS" "[]" \
  --rpc-url $RPC
```

If this reverts with selector `0xb9b2a425` (`FeatureNotActivated(bytes32)`), activation is
confirmed off — regardless of what any announcement or third party claims. Verify the selector
yourself rather than trusting prose:

```bash
base-cast sig "FeatureNotActivated(bytes32)"
# 0xb9b2a425
```

## Don't Trust Announcements Over the Chain

Activation timelines get communicated informally (docs, social posts, support bots) and can slip.
Treat any "B20 is live on mainnet" claim as a hypothesis, not a fact, until the registry itself
confirms it. The check above takes one RPC call — there's no reason to build on secondhand
information when the ground truth is a single command away.
