---
title: "Base MCP Plugin Specification"
description: "Authoring spec for native Base MCP plugins — frontmatter schema, required body sections, and integration type definitions."
---

# Base MCP Plugin Specification

This file is the source of truth for authoring native Base MCP plugins. It applies to both internally maintained plugins and partner-authored plugins submitted via PR.

---

## Frontmatter Schema

Every plugin file must open with YAML frontmatter. Fields marked **required** must be present; others default as noted.

### Required fields

| Field | Type | Description |
|---|---|---|
| `title` | string | `"<Protocol> Plugin"` |
| `description` | string | One line: what the plugin does + how it routes to Base MCP. |
| `name` | string | Lowercase slug (e.g. `morpho`). Used for cross-links and the SKILL.md table. |
| `version` | string | Plugin doc version, semver (e.g. `0.2.0`). Bump on meaningful changes (a spec-conformance restructure counts). |
| `integration` | enum | See [Integration Types](#integration-types). |
| `chains` | string[] | Base MCP chain strings the plugin targets (e.g. `[base]`, `[base, optimism]`). |

### Capability flags

All optional. Defaults: `shell: never`, `allowlist: []`, `externalMcp: null`, `cliPackage: null`, `auth: none`, `risk: []`.

| Field | Type | Description |
|---|---|---|
| `requires.shell` | `required \| optional \| never` | Whether shell/terminal access is needed. |
| `requires.allowlist` | string[] | Hosts that must be in the Base MCP `web_request` allowlist. |
| `requires.externalMcp` | `{ name, url } \| null` | Separate MCP server the plugin depends on. |
| `requires.cliPackage` | string \| null | npx/uvx invocation string (e.g. `@morpho-org/cli@latest`). |
| `auth` | `none \| api-key \| siwe-jwt \| oauth-on-install` | Auth model used by the plugin's external services. |
| `risk` | string[] | Risk tags that trigger `## Risks & Warnings`: `liquidation`, `slippage`, `low-liquidity`, `pii`, `irreversible`. |

### Example frontmatter

```yaml
---
title: "Moonwell Plugin"
description: "Lending on Moonwell via HTTP API → send_calls on Base and Optimism."
name: moonwell
version: 0.1.0
integration: http-api
chains: [base, optimism]
requires:
  shell: never
  allowlist: [api.moonwell.fi]
  externalMcp: null
  cliPackage: null
auth: none
risk: [liquidation]
---
```

---

## Integration Types

The `integration` field classifies how the plugin reaches Base MCP. Choose the most specific type that applies; use `hybrid` only when a single type can't describe the routing (document the surface-specific paths in `## Surface Routing`).

| Value | What it means | Examples |
|---|---|---|
| `cli-only` | All calls go through a shell CLI. No HTTP API, no external MCP. | Aerodrome |
| `http-api` | Plugin calls an HTTP API (via `web_request` or harness HTTP tool) to read data or build calldata. | Moonwell, Uniswap, Bankr |
| `external-mcp` | Plugin relies on a separate MCP server. The agent reads that MCP's own tool catalog — this plugin file does **not** enumerate its tools. | Virtuals |
| `semantic-base-tool` | Plugin composes Base MCP's higher-level semantic tools (`swap`, `send`) rather than producing raw calldata. | *(future)* |
| `hybrid` | Combines two or more paths with surface-dependent routing. Document the routing matrix in `## Surface Routing`. | Avantis, Morpho |

---

## Required Body Sections

Sections appear in this order. **R** = required in every plugin. **C** = conditional on frontmatter flags. **O** = optional.

| # | Heading | Status | Condition |
|---|---|---|---|
| 1 | `> [!IMPORTANT]` onboarding callout | R | Always — pointer to Base MCP onboarding in SKILL.md. |
| 2 | `## Overview` | R | Always — 1 paragraph: protocol summary, chain(s), routing one-liner. |
| 3 | `## Detection` | C | `integration` is `external-mcp`, or `hybrid` with an MCP path. |
| 4 | `## Installation` | C | `requires.externalMcp` or `requires.cliPackage` is set. |
| 5 | `## Auth` | C | `auth != none`. |
| 6 | `## Surface Routing` | R | Always — table or prose mapping capability × surface to execution path. |
| 7 | `## Endpoints` or `## Commands` | C | `http-api` → use `## Endpoints`. `cli-only` or CLI path of `hybrid` → use `## Commands`. `external-mcp` plugins **omit this section entirely** — the agent reads the MCP's own tool catalog. |
| 8 | `## Orchestration` | R | Always — ordered steps from user intent to Base MCP call. Use `###` sub-headings for sub-flows. |
| 9 | `## Submission` | R | Always — names the target Base MCP tool (`send_calls`, `swap`, `sign`, or `none`) and any mapping or normalization needed to reach it. |
| 10 | `## Example Prompts` | R | Always — 2–4 concrete prompt → numbered steps. |
| 11 | `## Risks & Warnings` | C | `risk` is non-empty. |
| 12 | `## Notes` | O | Constants, token addresses, known gotchas. |

### Canonical heading names

Use these exact names. Synonyms from older plugins must be renamed on the next meaningful edit.

| Correct | Instead of |
|---|---|
| `## Risks & Warnings` | "Safety Rules", "Safety Notes", "Execution Warnings", "Important Notes" |
| `## Orchestration` | "Orchestration Pattern", "Swap Orchestration", "CLI Orchestration" |
| `## Endpoints` | "API Services", "Endpoint reference" |
| `## Commands` | "Morpho CLI Path", "Runner" |
| `## Surface Routing` | "Surface routing", inline routing prose inside `## Overview` |

---

## Existing Plugin Conformance

Current integration classification for the 7 native plugins:

| Plugin | `integration` | `chains` | `shell` | `allowlist` | `externalMcp` | `auth` | `risk` |
|---|---|---|---|---|---|---|---|
| Aerodrome | `cli-only` | `[base]` | `required` | `[]` | `null` | `none` | `[slippage]` |
| Avantis | `hybrid` | `[base]` | `optional` | `[data.avantisfi.com, core.avantisfi.com, api.avantisfi.com]` | `null` | `none` | `[liquidation, slippage, irreversible]` |
| Bankr | `http-api` | `[base]` | `never` | `[api.bankr.bot]` | `null` | `none` | `[low-liquidity, irreversible]` |
| Moonwell | `http-api` | `[base, optimism]` | `never` | `[api.moonwell.fi]` | `null` | `none` | `[liquidation]` |
| Morpho | `hybrid` | `[base]` | `optional` | `[]` | `{ name: morpho, url: https://mcp.morpho.org/ }` | `none` | `[liquidation]` |
| Uniswap | `http-api` | `[base]` | `never` | `[trade-api.gateway.uniswap.org, liquidity.api.uniswap.org]` | `null` | `api-key` | `[slippage]` |
| Virtuals | `external-mcp` | `[]` | `never` | `[]` | `{ name: virtuals, url: https://mcp.acp.virtuals.io/ }` | `siwe-jwt` | `[pii]` |

All seven are at `version: 0.2.0` as of the spec-conformance restructure.

---

## How to Author a Plugin

Follow these steps to write a new plugin file (`skills/base-mcp/plugins/<slug>.md`). The goal is a file an agent can route from at runtime and a partner can reproduce mechanically.

1. **Classify the integration.** Pick the single most specific `integration` value (see [Integration Types](#integration-types)). This choice drives which body sections are required:
   - `cli-only` → `## Commands`, `requires.shell: required`, `requires.cliPackage` set.
   - `http-api` → `## Endpoints`, list `requires.allowlist` hosts.
   - `external-mcp` → `## Detection` + `## Installation`, set `requires.externalMcp`, **omit** `## Endpoints`/`## Commands` (the agent reads the MCP's own tool catalog).
   - `hybrid` → combine the above and document per-surface paths in `## Surface Routing`.
2. **Fill the frontmatter** using the schema above. Every required field must be present; capability flags default as noted. Be honest about `risk` — it's what triggers `## Risks & Warnings` and shapes the agent's caution.
3. **Write the body sections in canonical order** (see [Required Body Sections](#required-body-sections)). Include every **R** section, every **C** section your frontmatter flags imply, and use the exact canonical heading names.
4. **Name the submission tool.** `## Submission` must say which Base MCP tool the flow lands on — `send_calls`, `swap`, `sign`, or `none` — and any calldata mapping / normalization needed to get there.
5. **Show the happy path.** `## Orchestration` walks user intent → Base MCP call as ordered steps. `## Example Prompts` gives 2–4 concrete prompts, each mapped to numbered steps.
6. **Self-review against the checklist below**, then open a PR to `skills/base-mcp/plugins/<slug>.md`.

## Plugin Skeleton Template

Copy this, fill the placeholders, and delete any **C**/**O** sections that don't apply to your integration:

```markdown
---
title: "<Protocol> Plugin"
description: "<one line: what it does + how it routes to Base MCP>"
name: <slug>
version: 0.2.0
integration: cli-only | http-api | external-mcp | semantic-base-tool | hybrid
chains: [base]
requires:
  shell: never
  allowlist: []
  externalMcp: null
  cliPackage: null
auth: none
risk: []
---

# <Protocol> Plugin

> [!IMPORTANT]
> Run Base MCP onboarding first (see SKILL.md). <one-line pointer.>

## Overview
<1 paragraph: protocol summary, chain(s), one-line routing statement.>

<!-- ## Detection — external-mcp or hybrid-with-MCP only: how to tell the MCP/tooling is present. -->
<!-- ## Installation — only if requires.externalMcp or requires.cliPackage is set. -->
<!-- ## Auth — only if auth != none. -->

## Surface Routing
<table or prose mapping capability × surface → execution path (harness HTTP tool, web_request, CLI, external MCP, UI fallback).>

<!-- ## Endpoints — http-api. | ## Commands — cli-only / CLI path of hybrid. external-mcp omits this. -->

## Orchestration
<ordered steps from user intent to the Base MCP call. Use ### sub-headings for sub-flows.>

## Submission
<names the target Base MCP tool: send_calls | swap | sign | none, plus any mapping/normalization.>

## Example Prompts
<2–4 concrete prompts, each → numbered steps.>

<!-- ## Risks & Warnings — only if risk is non-empty. -->

## Notes
<constants, token addresses, known gotchas, deep reference material.>
```

## Authoring Checklist

Before opening a PR, confirm:

- [ ] Frontmatter present with all **required** fields; enum values are valid.
- [ ] `integration` is the most specific value that fits; flags (`shell`, `allowlist`, `externalMcp`, `cliPackage`, `auth`, `risk`) are accurate.
- [ ] `> [!IMPORTANT]` onboarding callout is first.
- [ ] `## Overview`, `## Surface Routing`, `## Orchestration`, `## Submission`, `## Example Prompts` all present (the **R** sections).
- [ ] Conditional sections included where flags demand: `## Detection`/`## Installation` for external MCPs, `## Auth` when `auth != none`, `## Risks & Warnings` when `risk` is non-empty, `## Endpoints` (http-api) or `## Commands` (cli-only / CLI path).
- [ ] Heading names are canonical — no synonyms (see [Canonical heading names](#canonical-heading-names)).
- [ ] `## Submission` names a concrete Base MCP tool.
- [ ] Sections appear in canonical order.
