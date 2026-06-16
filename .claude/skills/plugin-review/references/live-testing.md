# Live Testing Playbook

Optional phase that materially improves a review by checking reality instead of the doc's claims. **Strictly read-only / non-destructive**: never submit an onchain tx, spend funds, launch a token, buy, or sign-and-broadcast.

## API / SDK verification

Goal: confirm the documented endpoints/SDK/contracts actually exist and behave as claimed.

Tools: `curl`, `node`, `npm`/`npx`, `cast` (foundry), Etherscan API, public RPCs.

For each documented endpoint/command/SDK entrypoint:
1. **Call it.** GET/quote/build endpoints are fine to call (they only return data) — do NOT submit returned calldata. Do NOT call endpoints that create/launch/buy even if they return data; probe those with HEAD/OPTIONS or a deliberately-invalid body to observe the error shape.
2. **Record** exact request, HTTP status, and whether the response shape matches the doc.
3. **Verify auth claims.** Probe unauthenticated — a `401` proves the endpoint is real and gated; a `402` proves an x402/paid path. This frequently contradicts the doc (e.g. "no auth" claims that actually 401; auth endpoints that turn out to be public; preview hosts that 500 on valid input).
4. **SDK**: `npm view <pkg> version repository` to confirm it exists; optionally install in a temp dir and run a minimal read-only call. CLIs via npx: `npx -y <pkg> --help`.
5. **Contracts**: confirm documented addresses exist onchain (`cast code <addr> --rpc-url <rpc-url>` or Etherscan) on the claimed chain.
6. **Allowlist**: list hosts the plugin actually contacts; confirm `requires.allowlist` ⊇ that set with no extras.

Append findings as `## Live API / SDK Verification` in the report. Update the verdict if reality changes it.

### Useful public RPCs

- Base: `https://mainnet.base.org`
- Base Sepolia: `https://sepolia.base.org`
- Ethereum: `https://eth.llamarpc.com`
- Arbitrum: `https://arb1.arbitrum.io/rpc`
- Optimism: `https://mainnet.optimism.io`
- Polygon: `https://polygon-rpc.com`

### Safety recap
Read-only/build only. Don't approve, don't broadcast, don't spend. Throwaway eval API keys end up in plaintext in the session — let them lapse after the review.
