# Evaluation Criteria

Assess each plugin against these dimensions. The spec (`skills/base-mcp/references/plugin-spec.md`) is the source of truth — fetch the current version; it changes. Cite evidence (line/section) for every finding.

## Table of contents
- File location & naming
- Frontmatter
- Integration type
- Required body sections
- Submission
- Surface Routing
- Allowlist
- Security
- Content quality
- Compliance & language
- Geoblocking (high-risk categories)
- Disclaimers
- High-risk category gate
- Cross-cutting gotchas (read these)
- Severity rubric

## File location & naming
- Plugin file is at `skills/base-mcp/plugins/<slug>.md`.
- `<slug>` matches frontmatter `name`.

## Frontmatter
Required fields present: `title`, `description`, `tags`, `name`, `version`, `integration`, `chains`.
- **Enums valid**: `integration` ∈ {cli-only, http-api, external-mcp, semantic-base-tool, hybrid}; `requires.shell` ∈ {required, optional, none}; `auth` ∈ {none, api-key, siwe-jwt, oauth-on-install}; `risk` tags ∈ {liquidation, slippage, low-liquidity, pii, irreversible}.
- **`chains` ⊆ supported set**: arbitrum, avalanche, base, base-sepolia, bsc, ethereum, optimism, polygon. `[]` is valid if no onchain tx routes through Base MCP. (Re-check the live `chain` param on Base MCP tools — the set can change.)
- **`tags`**: 3–5 lowercase, hyphenated capability/category keywords (not the protocol name). Reuse existing vocabulary; flag net-new tags (and confirm they're appended to the vocabulary list — the one sanctioned shared-file edit).
- **Capability flags** (`requires.shell/allowlist/externalMcp/cliPackage`, `auth`, `risk`) accurate and derived from real behavior, not copied from another plugin.
- **`version`** is the plugin-doc version (semver). NOT the package/npm version, NOT a spec version. No mandated starting value.

## Integration type
Most specific value per the spec's ordered questions (first match wins): cli-only → http-api → external-mcp → semantic-base-tool → hybrid. If wrong, state the correct value and why.

## Required body sections
R = always required; C = conditional on flags.
- R: `> [!IMPORTANT]` onboarding callout (first), `## Overview`, `## Surface Routing`, `## Orchestration`, `## Submission`, `## Example Prompts`.
- C: `## Detection` + `## Installation` (external-mcp, or hybrid with MCP path, or `cliPackage` set); `## Auth` (auth ≠ none); `## Endpoints` (http-api) or `## Commands` (cli-only / CLI path of hybrid); `## Risks & Warnings` (risk non-empty). external-mcp omits Endpoints/Commands.
- **Canonical heading names** — no synonyms (e.g. "Safety Notes"/"Execution Warnings" → `## Risks & Warnings`; "API" → `## Endpoints`; inline send_calls blocks → `## Submission`).
- **Canonical order** as listed above; no broken internal `#anchor` links after renames.

## Submission
Names a concrete Base MCP tool — `send_calls`, `swap`, `sign`, or `none` — and shows the **exact mapping** from the endpoint/command/MCP output into that tool's input (`{to, value, data}` normalization, chain-string mapping, approvals-before-action batch order). For `none`, state why.

## Surface Routing
A capability × surface table (read vs write × harness vs chat-only) mapping to an execution path (harness HTTP tool / `web_request` / CLI / external MCP / UI-paste fallback). **Must state the shell-less / chat-only behavior** — an explicit fallback or an explicit "stop." (A correct chat-only "stop when the host isn't on the `web_request` allowlist" is good, not a defect.)

## Allowlist
`requires.allowlist` lists **every** external host the plugin fetches over HTTP, and no extras. This is the SSRF / `web_request` boundary. `[]` is only correct for cli-only / external-mcp plugins making no direct HTTP calls. Cross-check against the hosts actually referenced in the body (and, in live testing, actually contacted).

## Security
- Untrusted partner output: external APIs can return malicious calldata. Is `to`/target validated before submit? Are amounts/min-outs checked?
- SSRF: does it take user-supplied URLs to fetch server-side?
- Auth/API-key handling: keys never logged/echoed; secret mechanisms preferred over chat paste.
- PII / irreversible: are the risk tags honest and complete (without over-tagging — see gotchas)?

## Content quality
Orchestration is realistic and actionable; example prompts are concrete (a read, a primary write, an edge/fallback); no copy-paste leftovers from another plugin; response shapes match reality.

## Compliance & language
Plugin copy must use **neutral, non-promotional language**. Flag as a **blocker** if the plugin text contains any of:
- Yield, rate, or performance claims ("earn 12% APY", "best returns")
- Directional recommendations ("you should buy X", "always deposit here", "recommended strategy")
- Default trade parameters that steer toward specific tokens or positions
- Actions that route outside of Base without clear user intent (e.g. a plugin silently bridging to another chain or defaulting to a non-Base chain)

The plugin must describe what the protocol *does*, not advocate for using it. Orchestration should present options neutrally, not prescribe a preferred action.

## Geoblocking (high-risk categories)
Applies to plugins in **perps, prediction markets, and gambling** categories. If the protocol's frontend geoblocks US IPs (or other jurisdictions), the underlying API must enforce equivalent restrictions. Check this during live testing (see `references/live-testing.md`). If the API serves US IPs while the frontend blocks them, Base MCP risks being deemed a circumvention tool — flag as a **blocker**.

## Disclaimers
The plugin's `> [!IMPORTANT]` onboarding callout (first element in the body) should include appropriate disclaimers about the plugin's third-party nature and any relevant risk context. For high-risk categories (perps, prediction markets, privacy), disclaimers should be more prominent. The plugin's `## Installation` section (if present) should also reference these disclaimers.

## High-risk category gate
Plugins in the following categories require **explicit legal review** before inclusion as a native plugin: **perps/perpetual futures, prediction markets, and privacy-focused protocols**. Flag this in the report if the plugin falls into one of these categories — it is not a defect in the plugin itself, but a pre-merge process gate.

## Cross-cutting gotchas (the high-value, easy-to-miss ones)

1. **Smart-account signatures (ERC-1271/6492) are variable-length (>200 bytes), not 65-byte EOA sigs.** The default Base MCP account is a smart contract wallet. Any plugin that:
   - string-replaces a fixed 65-byte signature placeholder inside calldata, or
   - bakes an off-chain EIP-712 signature into calldata (e.g. Permit2 `buildCallWithPermit2`)
   is **broken** for the default wallet (works only for EOAs). Correct pattern: grant the allowance onchain in the `send_calls` batch (e.g. ERC20 `approve` → Permit2 `approve` → router call). Treat this as a blocker, not a nit.

2. **`irreversible` risk is "flag when worth emphasizing," not every write.** Spec precedent: pure swap/DEX plugins (Uniswap, Aerodrome) carry `[slippage]` only. `irreversible` belongs on asymmetric/severe cases — perps/liquidation (Avantis), token launches/rug (Bankr). A swap is economically recoverable (swap back); its salient risk is `slippage`. Do NOT recommend adding `irreversible` to a swap plugin.

3. **Contribution scope / self-registration.** Partners must NOT edit: the `SKILL.md` plugins table (registry), the Integration Types "Examples" cell, or the "Existing Plugin Conformance" table/count. These are maintainer-managed and bumping them causes merge conflicts between concurrent PRs and self-asserts "native" status. The ONLY sanctioned shared-file edit is appending a genuinely net-new tag to the vocabulary list in plugin-spec.md. (Codified in plugin-spec.md "Contribution Scope".) Self-registration edits must be reverted before merge.

4. **`version` semantics.** Plugin-doc version, independent of upstream package version. Mirroring the package version is acceptable but worth flagging in case unintended. The spec mandates no specific starting number — do not assert "must be 0.2.0."

5. **Allowlist provisioning is operator-controlled.** A plugin declaring `requires.allowlist` does not mean those hosts are live-allowlisted; that's a maintainer step (ideally bound to plugin acceptance). The plugin must fail safe on chat-only surfaces when not allowlisted (stop, don't improvise). Don't fault the plugin for this stop.

6. **Reference links** use `../references/...` from plugin files (plugins live in `plugins/`, refs in `references/`). Bare `references/...` resolves to a non-existent `plugins/references/` path.

7. **REST "build" endpoints may return decoded structs, not hex calldata.** If so, the curl→`send_calls` path needs an ABI-encode step the plugin must document (or restrict to a CLI path that encodes internally).

8. **Delist readiness.** Native plugins can be disabled quickly if the underlying API goes rogue, turns malicious, or starts returning harmful calldata. Although users review every transaction via approval mode, inclusion as a native plugin creates an expectation that things work as intended. The plugin itself doesn't need to implement a kill-switch, but reviewers should note if the plugin's architecture makes fast delisting difficult (e.g. hardcoded into core routing with no clean boundary).

9. **Review scope is bounded.** Base review is limited to spec conformance, basic QA, and live testing as documented in this skill. The review does not constitute co-authorship or curation of the plugin's underlying protocol. This boundary is intentional — it allows the plugin program to scale without accumulating unbounded liability.

## Severity rubric
- **blocker** — breaks the documented flow, security hole, makes the plugin unroutable (missing required frontmatter, broken submission for the default wallet, dead/locked API, false auth claim), promotional/steering language, or API circumvents frontend geoblocking in a regulated category.
- **major** — wrong integration type, missing required section, inaccurate allowlist, mis-declared auth, missing disclaimers for high-risk category.
- **minor** — doc/response-shape drift, non-canonical headings, missing optional risk nuance.
- **nit** — wording, formatting, version cosmetics.
