---
title: "SBOR Plugin"
description: "Checks a lending rate against the SBOR benchmark before borrowing, through SBOR's remote MCP; read-only, submits nothing to Base MCP."
tags: [borrowing, lending, benchmark-rates, ai-agents]
name: sbor
version: 0.1.0
integration: external-mcp
chains: [base]
requires:
  shell: none
  allowlist: []
  externalMcp:
    name: sbor
    transport: http
    url: https://mcp.sbor.xyz/mcp
  cliPackage: null
auth: none
risk: []
---

# SBOR Plugin

> [!IMPORTANT]
> Run Base MCP onboarding first (see SKILL.md). SBOR only reads published data, so it never needs a wallet connection or a signature.

## Overview

SBOR publishes benchmark lending rates, read from lending contract state and fixed once a day. For borrowing on Base, the benchmark that applies is `BTC-COLLATERAL-USDC`: what it costs to borrow USDC against bitcoin wrapped by a custodian (cbBTC, WBTC), from the Morpho Blue markets on Base and Ethereum whose only collateral is that bitcoin. Use it before a borrow built by a lending plugin such as Morpho or Moonwell: compare the offered rate with the benchmark and stop to ask the user when it is well above. The plugin reads through SBOR's remote MCP server and returns text; it builds no calldata and submits nothing.

## Detection

If the SBOR tools `get_rate`, `compare_rate`, `list_markets`, `get_history`, `compare_chains` and `get_methodology` are not exposed, possibly under a harness namespace, the MCP is not installed: see `## Installation`.

## Installation

The server is remote, needs no key and no sign-in, and all six tools are read-only.

- **Claude Code:** `claude mcp add --transport http sbor https://mcp.sbor.xyz/mcp`
- **Cursor and other JSON-config clients:**

```json
{
  "mcpServers": {
    "sbor": { "url": "https://mcp.sbor.xyz/mcp" }
  }
}
```

- **Claude.ai:** Settings → Connectors → Add custom connector, URL `https://mcp.sbor.xyz/mcp`, no sign-in.
- **ChatGPT and other clients with remote connectors:** add `https://mcp.sbor.xyz/mcp` as a custom connector.
- **Any client that runs local servers instead:** `npx -y sbor-mcp@1.2.0`, the same tools and the same answers.

## Surface Routing

| Capability | Harness with MCP support (Claude Code, Cursor, Codex) | Chat-only (Claude.ai, ChatGPT) |
|---|---|---|
| Check an offered rate against a benchmark | SBOR external MCP, `compare_rate` | SBOR as a remote connector. If it is not connected: ask the user to connect it, or show `https://sbor.xyz/api/v1/latest.json` and ask them to paste it back so it can be fetched (GET only, see custom-plugins.md) |
| Read the benchmarks and the markets behind them | SBOR external MCP, `get_rate`, `list_markets`, `compare_chains` | as above |
| Write anything onchain | none: SBOR never writes | none |

## Orchestration

### Check a rate before borrowing

1. Establish the loan: the asset borrowed, the collateral, the chain, and the offered rate as a percentage (4.2 means 4.2%).
2. Choose the benchmark. USDC borrowed against cbBTC or WBTC on Base or Ethereum: `BTC-COLLATERAL-USDC`. Lending on Stacks: `SBOR-USD`, `SBOR-BTC` or `SBOR-STX` for the currency. Never compare a Base loan with a Stacks index.
3. Call `compare_rate` with `rate`, `side: "borrow"` and the chosen `index`.
4. If it returns an error, the benchmark is stale, withheld or not published. Treat that as unknown, not as zero, tell the user, and do not present SBOR as having approved the rate.
5. If the offer is more than 50 basis points above the benchmark, stop and ask the user before building the borrow in the lending plugin. Otherwise report the comparison and hand back to the lending plugin's flow.

### Explain where a rate comes from

1. `list_markets` with `index: "BTC-COLLATERAL-USDC"` for each Morpho market's rate, utilization and depth.
2. `compare_chains` for the same asset classes elsewhere, with SOFR for reference.

## Submission

`none`. SBOR only reads. Any borrow is built and submitted by the lending plugin, for example Morpho through `send_calls`, after the user has seen SBOR's comparison.

## Example Prompts

**"I've been offered 5.5% to borrow USDC against cbBTC on Base. Is that fair?"**
1. Collateral cbBTC, loan USDC, chain Base, so the benchmark is `BTC-COLLATERAL-USDC` (`## Orchestration` step 2).
2. `compare_rate` with `rate: 5.5`, `side: "borrow"`, `index: "BTC-COLLATERAL-USDC"`.
3. Report the gap in basis points, the cheapest matching market it names, and the freshness line. More than 50 basis points above: recommend stopping to ask about the terms, such as fixed or variable, LTV and liquidation.

**"Borrow 10,000 USDC against my cbBTC on Morpho, but check the rate first."**
1. Read the market's current rate through the Morpho plugin.
2. `compare_rate` against `BTC-COLLATERAL-USDC`.
3. Within 50 basis points: continue in the Morpho plugin. Above: stop and ask the user first.

**"What does it cost to borrow USDC against bitcoin right now?"**
1. `get_rate` with `index: "BTC-COLLATERAL-USDC"`.
2. Report the rate, the depth and the freshness line, and say it is a reference, not an index.

## Notes

- SBOR publishes market data, not financial advice. The decision stays with the user.
- Rates are effective APY percentages. The fixing is published once a day; every tool states its age, and `compare_rate` refuses data more than 48 hours old.
- `BTC-COLLATERAL-USDC` is a reference, not an SBOR index. It is published only when every Morpho market it covers was read. The collateral is custodial wrapped bitcoin.
- `SBOR-USD` measures a dollar on Stacks, borrowed against any crypto collateral, not only bitcoin. It is not a benchmark for a Base loan.
- SBOR is independent: no token, and no stake in or payment from any venue it measures. The data is free to use, including commercially, with attribution.
- Registry: `xyz.sbor/sbor`. Methodology: https://sbor.xyz/llms.txt. For agents: https://github.com/sborxyz/sbor/blob/main/AGENTS.md
