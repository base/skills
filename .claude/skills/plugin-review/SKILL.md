---
name: plugin-review
description: Validate and review Base MCP plugin files against the Plugin Specification. Use when writing a new plugin, preparing a plugin PR for submission, self-checking a plugin before opening a PR, or reviewing someone else's plugin PR. Triggers on requests like "check my plugin against the spec", "validate this plugin file", "review my plugin PR", "does this plugin conform to the spec", "prepare my plugin for submission", "write a plugin for X protocol".
license: Complete terms in LICENSE.txt
---

# Plugin Review

Validate Base MCP plugin files against the current Plugin Specification. Produces a conformance report with actionable findings.

Works for both **authors** (self-check before submitting a PR) and **reviewers** (evaluate an incoming PR).

## Workflow

1. **Fetch the current spec** (it changes — never rely on a stale copy):
   ```bash
   curl -s https://raw.githubusercontent.com/base/skills/master/skills/base-mcp/references/plugin-spec.md
   ```
   Related docs worth reading: `references/custom-plugins.md`, `references/approval-mode.md`, `references/batch-calls.md`, and `SKILL.md` (the root skill). Existing native plugins under `skills/base-mcp/plugins/` are the precedent for conventions.

2. **Read the plugin file** in full. If reviewing a PR:
   ```bash
   gh pr view <n> --repo base/skills --json title,body,number,headRefName,files,additions,deletions
   gh pr diff <n> --repo base/skills
   # raw plugin file (diff may be truncated):
   gh api "repos/base/skills/pulls/<n>/files" --jq '.[] | select(.filename|endswith(".md")) | .raw_url'
   ```

3. **Static conformance evaluation** — assess against every dimension in `references/evaluation-criteria.md` (includes compliance/language checks and high-risk category gates). Write the report using `references/report-template.md`.

4. **(Optional) Live API / SDK verification** — exercise the documented endpoints/SDK/contracts with read-only calls. See `references/live-testing.md`. For perps/prediction-market/gambling plugins, also run the **geoblock verification** (compare frontend vs API access restrictions). Append a `## Live API / SDK Verification` section to the report. This routinely overturns doc claims (fabricated/locked endpoints, broken hosts, wrong response shapes).

5. **Save the report.** If reviewing a PR and asked to comment, draft a PR comment from the report using `references/comment-guidelines.md` and post with: `gh pr comment <n> --repo base/skills --body-file <comment-file>`.

## Multiple PRs

Evaluate PRs in parallel by spinning up one sub-agent per PR (each writes its own report + returns a short verdict summary). Hand each sub-agent: the spec (or its raw URL), the PR number, the evaluation criteria, the report template, and the comment guidelines.

## Critical gotchas

These recur and are easy to get wrong — full detail in `references/evaluation-criteria.md`:

- **Smart-account signatures break naive signing.** The default Base MCP wallet is a smart contract; `sign` returns a variable-length ERC-1271/6492 signature (>200 bytes), not a 65-byte EOA sig. Any plugin that splices a signature into a fixed-width calldata slot, or bakes an off-chain EIP-712 signature into calldata (e.g. Permit2 `buildCallWithPermit2`), is **broken** for that wallet. Correct pattern: onchain allowance grants.
- **`irreversible` risk is NOT for every onchain write.** The spec says "flag when worth emphasizing." Pure swaps use `slippage` (precedent: Uniswap, Aerodrome carry `[slippage]`, not `irreversible`). Reserve `irreversible` for asymmetric/severe cases (perps/liquidation, token launches/rug). Do not demand it on swaps.
- **Don't self-register.** A plugin PR must NOT edit the `SKILL.md` plugins table, the Integration Types "Examples" cell, or the "Existing Plugin Conformance" table — those are maintainer-managed (codified in plugin-spec.md "Contribution Scope"). The only sanctioned shared-file edit is appending a genuinely net-new tag to the vocabulary list. Limit the diff to `plugins/<slug>.md` (+ that tag line).
- **`version` is the plugin-doc version** — not the npm/package version and not a global spec version. The spec mandates no specific starting number.
- **Verify claims, don't trust them.** Auth models, allowlist completeness, response shapes, and contract addresses are frequently wrong in the doc. Probe them (live testing).
- **Reference links** from a plugin file must use `../references/...` (plugin files live in `plugins/`, refs in `references/`).
- **Neutral language is mandatory.** No yield/rate/performance claims, no "you should buy X", no "always deposit here", no defaulting to specific tokens. Steering language is a blocker.
- **Perps, prediction markets, and privacy plugins need legal review** before inclusion as native plugins. Flag this as a pre-merge process gate in the report.
- **API geoblock parity.** If the protocol's frontend geoblocks US IPs (or others), the API must enforce equivalent restrictions. If it doesn't, Base MCP risks being a circumvention tool — flag as a blocker.
