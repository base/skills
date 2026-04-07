---
name: benchmarking-on-op-stack
description: Teaches disciplined benchmarking methodology for Base and OP Stack chains. Covers apples-to-apples comparisons, warmup vs measured runs, latency/throughput/gas/receipt/log benchmarking, public vs private RPC caveats, rate limiting, contract read vs write benchmarking, local/testnet/mainnet considerations, and reproducibility. Use when measuring RPC performance, comparing RPC providers, profiling contract reads/writes, or setting up reproducible benchmarks. Covers phrases like "benchmark on Base", "benchmark RPC latency", "measure transaction latency on Base Sepolia", "gas profiling on Base", "compare RPC providers", "reproducible benchmarks", "benchmark contract reads", "benchmark contract writes", "load test Base", "TPS on Base", "OP Stack performance", or "profile Base RPC".
---

# Benchmarking on OP Stack

Use this skill when a developer needs to measure, compare, or reason about the performance of applications, contracts, or RPC infrastructure on Base or other OP Stack chains. It is an educational and onboarding resource — it does not provide pre-baked performance guarantees.

## Overview

Reliable benchmarking on Base requires controlling for variables that are easy to overlook: cold-cache effects, provider rate limits, sequencer inclusion variance, paymaster overhead, and environment differences between local dev, testnet, and mainnet.

This skill teaches a methodology for getting reproducible, defensible measurements — and for recognizing when reported numbers are likely misleading.

**When to use this skill:**
- Setting up a benchmark suite for a contract or app on Base
- Comparing RPC providers or endpoint configurations
- Profiling gas costs of contract reads or writes
- Evaluating TPS or throughput claims on OP Stack chains
- Auditing whether performance improvements actually helped

**When not to use this skill:**
- When the goal is to stress-test or load-test third-party infrastructure without disclosure
- When specific performance SLAs are needed — this skill teaches measurement methodology, not guarantees

## Benchmarking Principles

### Warmup Runs vs Measured Runs

Always discard the first run(s) when benchmarking RPC calls or contract operations.

**Why:** The first call after a process start or a period of inactivity triggers connection establishment, TLS handshakes, cache priming, and provider-side throttling resets. These are one-time costs that distort average-case measurements.

**Recommended practice:**
- Run ≥ 3 warmup iterations before capturing measurements
- Report the mean of ≥ 5 subsequent measured iterations
- Drop the highest and lowest results, then report the mean of the remaining runs (trimmed mean)

### Apples-to-Apples Comparisons

Never compare measurements taken under different conditions without documenting the delta. Common comparison failures:

| Comparison pitfall | Result |
|-------------------|--------|
| Local anvil vs Sepolia vs Mainnet | Chain state, gas prices, and sequencer behavior differ |
| Public RPC vs private/dedicated RPC | Rate limits and geographic latency are not comparable |
| Cold-cache vs warm-cache | Measurably different latency |
| Single measurement vs statistical aggregate | Outlier-dominated |
| Batched requests vs individual requests | Different concurrency profiles |
| Different contract state sizes | Read costs can diverge significantly |

### Reproducibility Checklist

Before publishing or acting on benchmark results, verify:
- [ ] Tool version and commit hash recorded
- [ ] RPC endpoint URL and provider name documented
- [ ] Network conditions noted (geographic proximity to provider, concurrent load)
- [ ] Warmup run count stated
- [ ] Number of measured iterations stated
- [ ] Result spread (min, max, stddev) reported alongside the mean
- [ ] Environment tier identified (local / testnet / mainnet)
- [ ] Time of day and peak/off-peak context noted (mainnet sequencer load varies)

## What to Measure

Benchmarking OP Stack systems involves four distinct measurement domains. Conflating them produces numbers that look precise but are misleading.

### 1. RPC Latency Benchmark

Measures the round-trip time for a single RPC request with no chain state mutation.

**What to capture:**
- Time-to-first-byte (TTFB)
- Full round-trip end-to-end time
- Error rate (timeout, 429, 5xx)

**Do not assume:**
- Latency from one geographic region reflects global average latency
- A single request's latency represents sustained throughput
- All RPC providers cache the same way — some cache aggressively, some not at all

**Command example (GNU/Linux):**
```bash
# Measure latency over 20 calls, discarding first 3 as warmup
for i in $(seq 1 20); do
  start=$(date +%s%N)
  cast call <CONTRACT> "readSomething()(uint256)" --rpc-url https://sepolia.base.org
  end=$(date +%s%N)
  echo "$(( (end - start) / 1000000 ))"
done \
  | tail -n +4 \
  | awk '{sum+=$1; n++} END {print "mean_ms=" sum/n}'
```
> **Note:** `date +%s%N` (nanosecond timing) is GNU-specific. On macOS or BSD, use `python3 -c 'import time; print(int(time.time()*1e9))'` or a dedicated benchmarking tool instead.

### 2. Transaction Lifecycle Benchmark

Measures the full time from `cast send` invocation to receipt inclusion — not just RPC call latency.

**What to capture:**
- Broadcast time (how fast the RPC accepts the transaction — `cast send` returns immediately after this)
- Inclusion time (time from broadcast to block inclusion — requires polling receipts)
- Confirmation time (time from inclusion to finality, if measuring finality)
- Gas used vs gas limit

**Key distinction:** `cast send --json` returns as soon as the transaction is broadcast — it does not wait for the transaction to be included in a block. Measuring only the broadcast time understates actual transaction latency. Poll the receipt to get the true inclusion time.

**Command example:**
```bash
# Send a transaction and poll for its inclusion block
tx_hash=$(cast send <CONTRACT> "writeSomething()" \
  --rpc-url https://sepolia.base.org \
  --private-key "$KEY" --json | jq -r '.transactionHash')

# Poll until the transaction is mined
cast receipt "$tx_hash" --rpc-url https://sepolia.base.org --json \
  | jq '{blockNumber, gasUsed, status}'
```

### 3. Historical Event / Log Query Benchmark

Measures how fast events or historical state can be retrieved.

**What to capture:**
- `cast logs` query time for recent blocks
- `cast logs --from-block X --to-block Y` for historical ranges
- Archive node vs non-archive node behavior (some queries require full archive state)
- Topic filtering performance (not all topics are indexed equally by all providers)

**Caveats:**
- Log queries across large block ranges on non-archive nodes can be slow
- Some providers rate-limit historical queries differently from recent ones
- Providers that do not index the event's first topic fall back to full scanning, which is significantly slower
- Batch requests (`eth_getLogs` with large ranges) and streaming/polling requests have different performance profiles — do not mix them in the same benchmark

**Command example:**
```bash
# Benchmark a log query across a block range
start=$(date +%s%N)
cast logs --from-block 1000000 --to-block 1050000 \
  <CONTRACT> "Transfer(address,address,uint256)" \
  --rpc-url https://sepolia.base.org
end=$(date +%s%N)
echo "query_time_ms=$(( (end - start) / 1000000 ))"
```

### 4. Smart Contract Execution / Gas Benchmark

Measures gas consumed by contract reads or writes.

**What to capture:**
- Gas used for `eth_call` (read-only)
- Gas used for `eth_sendRawTransaction` (writes)
- Difference between gas estimation and actual gas used
- Paymaster gas overhead if using Base Account or ERC-4337

**Important:** On OP Stack chains including Base, the L1 gas mechanic means gas estimation includes L1 data rollup costs that vary with transaction calldata size — a write with large calldata will have a meaningfully higher gas estimate than the same write on Ethereum L1. Do not treat estimated gas as a tight bound on actual gas. For Base Account (ERC-4337) users, estimates include bundler and paymaster overhead and can run 20–40% higher than for a plain EOA.

**Command example:**
```bash
# Estimate gas for a write
cast estimate <CONTRACT> "writeSomething(uint256)" 42 \
  --rpc-url https://sepolia.base.org

# Send and retrieve actual gas used from the receipt
cast receipt \
  $(cast send <CONTRACT> "writeSomething(uint256)" 42 \
    --rpc-url https://sepolia.base.org --private-key "$KEY" --json \
    | jq -r '.transactionHash') \
  --rpc-url https://sepolia.base.org --json | jq '.gasUsed'
```

## Recommended Benchmark Scenarios

### Scenario A: RPC Provider Comparison

Compare two or more RPC providers for read-call latency and sustained throughput.

1. Send warmup traffic to both endpoints
2. Run ≥ 10 measured iterations per provider
3. Record mean, stddev, min, max
4. Ensure geographic proximity is comparable — if Provider A is in us-east-1 and Provider B is in eu-central-1, run a third test from a neutral location or note the geographic delta explicitly in your report
5. Run at similar times of day (mainnet sequencer load varies)

**Geographic proximity is a first-order variable, not a footnote.** If you are comparing providers to decide which to use in production, benchmark from a machine in the same region your application will serve. Results from a laptop in San Francisco are not valid inputs for a decision that applies to users in Frankfurt.

### Scenario B: Contract Read Optimization

Profile gas and latency for read operations before and after a code change.

1. Establish a baseline with the unmodified contract
2. Run ≥ 5 trim-mean iterations for gas and latency
3. Apply the code change
4. Repeat measurements under identical conditions
5. Attribute any improvement to the code change, not environment differences

### Scenario C: Write Transaction Throughput

Measure transactions-per-second (TPS) achievable for a given workload.

1. Use a funded account on the target network
2. Send N transactions without waiting for confirmation (pool them using `--json` and separate accounts/nonces)
3. Query receipts to determine actual inclusion rate
4. Calculate: `included_tps = confirmed_tx_count / inclusion_window_seconds`

**Caution:** Batching transactions this way may saturate the RPC's transaction pool and trigger 429s or nonce reuse errors. Use separate nonces if sending from multiple accounts.

### Scenario D: RPC Rate Limit Characterization

Determine when a public RPC endpoint starts rate-limiting your traffic.

1. Send a baseline stream of 1 req/s and record success rate
2. Gradually increase request rate (10 req/s, 50 req/s, 100 req/s)
3. Record the request rate at which error rate rises above 0%
4. Report the approximate rate limit ceiling — this is the ceiling, not the target

**Do not use this to "find the max" for production use.** Use a dedicated RPC endpoint for sustained high-throughput workloads.

## Environment Tiers

### Local Dev Chain (Anvil)

**What it is:** A local Ethereum node emulated by Foundry (Anvil), with a genesis dump matching Base Sepolia or Mainnet configuration.

**Use for:** Fast iteration during development, before deploying to testnet.

**Limitations:**
- No sequencer — transactions are mined locally by the dev node
- No paymaster or bundler overhead
- No real chain state — state pre-funded accounts only
- Gas dynamics differ from production (no L1 rollup cost component)
- Rate limiting behavior does not match real RPC providers

**Benchmark validity:** Local results are useful for relative comparisons (e.g., "this optimization reduces gas by X% relative to baseline") but are not comparable to testnet or mainnet results.

### Base Sepolia

**What it is:** Base's testnet, backed by a full OP Stack devnet or testnet stack.

**Use for:** Integration testing, contract deployment, and performance validation that involves real sequencer behavior.

**Caveats:**
- State is much smaller than mainnet — read queries hit a different cache profile
- Sequencer behavior under load may not match mainnet
- Faucet ETH is limited — plan iteration counts before starting
- Some RPC providers do not serve Base Sepolia traffic the same way they serve mainnet

### Base Mainnet

**What it is:** Base's production network, operated by Coinbase.

**Use for:** Final validation of contract performance, production RPC configuration decisions.

**Caveats:**
- Real value is at risk — never benchmark with real funds without proper safeguards
- Sequencer inclusion time varies with network demand (typically 1–4 seconds, can be longer during peak)
- Public RPC rate limits apply — see Rate Limiting below
- Geographic latency to the sequencer affects transaction inclusion time
- L1 gas (calldata posting costs) is a permanent component of gas on Base and differs from Ethereum L1

### Other OP Stack Chains

Many OP Stack chains (OP Mainnet, Mode, Zora, etc.) share the same execution client stack and sequencer architecture as Base, but implementations and configurations differ.

**What to know when benchmarking across OP Stack chains:**
- Do not assume identical performance characteristics across chains
- Some chains use shared sequencers or blob infrastructure — results may not generalize
- Archive node availability varies by chain — some queries that work on Base may fail or be very slow on other OP Stack chains
- EIP-1559 gas parameters are chain-specific
- Chains with smaller state may have faster cold-read performance for recent blocks — this does not mean they are faster in absolute terms for all queries

## Rate Limiting

Public Base RPC endpoints (`sepolia.base.org`, `mainnet.base.org`) are shared infrastructure with rate limits enforced per IP and per API key (if used). Rate limiting distorts benchmark results in two ways:

1. **Once rate-limited, all subsequent measurements are artificially high-latency** (requests queue or return 429s)
2. **Rate limit resets are one-time events** — a measurement taken immediately after a reset looks anomalously fast

**Signs you are being rate-limited:**
- Latency jumps from ~50ms to >1000ms mid-benchmark
- 429 errors appear mid-run
- `cast call` succeeds but `cast send` starts returning nonce errors

**Mitigations:**
- Use your own dedicated RPC endpoint for serious benchmarks
- If using public endpoints, instrument for 429s and discard rate-limited measurements
- Add `sleep` intervals between requests when benchmarking public endpoints (e.g., 100ms between calls)
- Prefer short benchmark runs against public RPCs — long sustained runs will hit limits

**Rule:** Never use a public RPC for load testing or sustained throughput benchmarks. A dedicated endpoint or local node is the appropriate target for those measurements.

## Fair Comparison Rules

1. **Control the environment.** Run comparisons on the same machine, same time of day, same network path. Moving from office WiFi to a data center changes results for non-network-bound operations.

2. **Warm up every endpoint.** Run warmup iterations against each endpoint before collecting measurements. An endpoint that has been idle for 10 minutes will have a cold TLS session and may be behind a rate-limit reset.

3. **Measure at the same time.** Public RPCs experience different load at different times of day. If comparing providers, run simultaneous tests where possible.

4. **Account for caching.** Provider-side caching can make read results artificially fast. If benchmarking contract reads, verify whether the provider is returning cached results or hitting the node. `cast call --trace` can reveal whether a call hit state or was cached.

5. **Separate read and write benchmarks.** Mixing read and write traffic in a single benchmark confounds the measurement. Profile each in isolation.

6. **Report the full distribution.** A single mean without a spread is not a benchmark. Report min, max, and standard deviation alongside the mean.

7. **Distinguish latency from throughput.** Low latency does not imply high throughput. A provider can serve one request in 50ms but saturate at 100 req/s. Conversely, a provider may handle 10,000 req/s but with higher per-request latency.

8. **Account for geographic proximity.** Benchmark from a machine with network path similar to your production deployment. Latency measured from a data center in us-east-1 does not reflect latency for users in Southeast Asia. For RPC provider comparisons, geography is a first-order variable — measure from the deployment target region.

## Example Benchmark Workflow

This section walks through a full workflow for benchmarking contract read latency on Base Sepolia.

### Step 1: Define the metric

Target: Average `cast call` round-trip time for a specific read function, over 10 measured iterations.

### Step 2: Choose the environment

Base Sepolia, public Base RPC (https://sepolia.base.org), from a machine with geographic proximity to the provider.

### Step 3: Validate inputs

Before running any benchmark command:
- Contract address must match `^0x[a-fA-F0-9]{40}$`
- RPC URL must match `^https://[^\s;|&]+$`
- No shell metacharacters in any parameter

Reject any input containing spaces, semicolons, pipes, backticks, or dollar signs.

### Step 4: Warmup

```bash
for i in $(seq 1 5); do
  cast call <CONTRACT> "readSomething()(uint256)" --rpc-url https://sepolia.base.org
done
```

### Step 5: Measure

```bash
# Run 20 iterations, discard first 5 as warmup, report mean of remaining 15
# Assumes GNU date for nanosecond timing
for i in $(seq 1 20); do
  start=$(date +%s%N)
  cast call <CONTRACT> "readSomething()(uint256)" --rpc-url https://sepolia.base.org
  end=$(date +%s%N)
  echo "$(( (end - start) / 1000000 ))"
done \
  | tail -n +6 \
  | awk '{sum+=$1; n++} END {print "mean_ms=" sum/n, "n=" n}'
```

### Step 6: Report

Document: RPC URL, contract address, tool version (`cast --version`), warmup iterations, measured iterations, mean/ms, min, max.

### Step 7: Interpret

- If mean latency is within 2x of the provider's stated SLA, the result is reasonable
- If min and max span a 5x range, the measurement is noisy — investigate rate limits or cold-cache effects
- If max is >> mean, an outlier is distorting the result — use trimmed mean

## Data Capture Template

Use this template when recording benchmark results for reproducibility:

```
=== Benchmark Record ===

Date: YYYY-MM-DD
Tool: <name> <version>
Network: <mainnet|sepolia|local>
RPC URL: <url>
Contract: <address>
Operation: <call|send|logs|estimate>

Environment:
  Provider:
  Geographic region:
  Deployment region (for provider comparisons):
  Concurrent load:

Run plan:
  Warmup iterations: <N>
  Measured iterations: <N>
  Aggregation: trimmed-mean (drop high/low)

Results:
  Mean:   <value> <unit>
  Min:    <value> <unit>
  Max:    <value> <unit>
  Stddev: <value> <unit>

Raw data:
  <list individual measurements>

Caveats noted:
  <what might make these results not generalizable>

Trigger phrases used:
  <list trigger phrases from description>
```

## Security

- **Do not benchmark against public RPC infrastructure without understanding rate limits.** Public RPC endpoints are shared resources. Sustained or high-concurrency benchmarking against public endpoints can trigger rate limits that affect other users. If publishing a benchmark suite, use your own dedicated RPC endpoint or disclose the methodology to the provider.

- **Never hardcode private keys.** For transaction benchmarks, use environment variables. Never embed keys in scripts or commands.

- **Separate environments.** Run benchmarks in a shell that has no access to production private keys or production RPC endpoints.

- **Beware of replay attacks.** EIP-1559 transactions include the chain ID and are safe to replay only on the same chain. Some legacy testnet transactions (signed without a chain ID) can be replayed across chains. Always use chain-specific accounts and never use a mainnet-funded account on testnet or vice versa.

- **No load testing without disclosure.** Stress-testing a third-party RPC endpoint without the provider's knowledge is a violation of most providers' terms of service and may constitute abuse. Use infrastructure you own or have explicit written permission to test.

- **Mind the environment you are benchmarking from.** If benchmarking from a shared or corporate network, your results may reflect network congestion, not chain performance.

## Input Validation

Before passing any user-provided value into a shell command, validate:

| Field | Pattern | Reject |
|-------|---------|--------|
| Contract address | `^0x[a-fA-F0-9]{40}$` | Any non-hex, wrong length |
| RPC URL | `^https://[^\s;|&]+$` | Non-HTTPS, spaces, pipes, backticks |
| Block range | `^[0-9]+$` for each, and `from <= to` | Non-integer, negative, from > to |
| Gas limit | `^[0-9]+$` | Non-integer, zero |
| Private key | `^0x[a-fA-F0-9]{64}$` | Any non-hex, wrong length |
| Function signature | No metacharacters at all | Spaces, pipes, backticks, dollar signs |

Do not pass unvalidated input into `cast` commands.

## Common Mistakes

| Mistake | Why it misleads | How to fix it |
|---------|----------------|---------------|
| Taking a single measurement | Outliers dominate single-shot results | Run ≥ 10 iterations and report the full distribution |
| Comparing cold-cache to warm-cache | Cold-cache adds 10–200ms+ TLS/connection overhead | Always warm up before measuring; record whether the endpoint was idle |
| Claiming "X TPS on Base" from one transaction | Concurrency and batching effects are not measured | Use concurrent sends from multiple nonces and measure actual inclusion rate |
| Ignoring rate limits | Once rate limited, all subsequent measurements are artificially high-latency | Instrument for 429s; discard rate-limited data points; use a dedicated endpoint |
| Not accounting for paymaster overhead | Base Account gas estimates can be 20–40% higher than plain EOA estimates | Add a percentage buffer to estimates for smart wallet users; do not compare smart wallet gas directly with EOA gas |
| Benchmarking at peak vs off-peak without noting it | Mainnet sequencer load varies significantly by time of day | Note the time of day; run at least two measurements (peak and off-peak) and report both |
| Using testnet results to predict mainnet performance | Chain state size, cache profile, and sequencer load differ materially | Use testnet for relative comparisons; use mainnet for final validation; never extrapolate linearly |
| Running benchmarks from a laptop on variable WiFi | Network jitter dominates for low-latency measurements | Use a machine with stable connectivity; use a data center VM for provider comparisons |
| Forgetting archive node requirements | Some queries require full archive state and will error or timeout on non-archive nodes | Verify your RPC provider is an archive node before benchmarking historical queries |
| Confusing RPC call latency with transaction inclusion time | `cast send` returns immediately after broadcast, not after inclusion | Poll the receipt to measure actual inclusion; do not use broadcast time as a proxy for latency |
| Using public RPC for sustained throughput benchmarks | Public RPCs will rate-limit, making results non-representative of actual capacity | Use a dedicated RPC endpoint; if using a public endpoint, keep request rate low and brief |
| Not warming up after a pause | Idle connections cool down and introduce cold-start overhead unrelated to the system under test | If more than ~2 minutes have passed since the last request, run 1–2 warmup calls before measuring |

## Interpretation Guidance

### Good signs a benchmark result is credible:
- The methodology section explains the environment, warmup count, and aggregation method
- Min, max, and stddev are reported alongside the mean
- A clear distinction is drawn between the measurement environment and the claimed generalization
- Results are compared to a controlled baseline, not to an absolute threshold
- The report explicitly calls out what the benchmark does not prove
- Geographic proximity to the RPC provider is documented

### Warning signs a benchmark result is misleading:
- Single measurement reported as "typical performance"
- "X TPS" without describing the batching and concurrency setup
- Testnet results labeled as equivalent to mainnet results
- No mention of warmup runs
- A specific ms/tx number claimed without a spread or context
- No distinction between read and write benchmarking
- Rate limiting not considered as a possible explanation for anomalous results
- No geographic context for RPC provider comparisons

### What to do when results look suspicious:
1. Increase iteration count to ≥ 20 measured runs
2. Run the same benchmark against a different RPC provider
3. Compare results from at least two different times of day
4. Check whether the provider has hit a rate limit mid-benchmark
5. Verify the contract state has not changed between runs (for read benchmarks)
6. Confirm the machine's network path to the provider has not changed
