# Evaluation Report Template

Write to a file like `PR-<n>-<slug>.md` (for PR reviews) or `<slug>-review.md` (for self-checks). This is the thorough, evidence-based artifact. Be precise; quote the plugin where it matters.

```markdown
# <slug> — Plugin Spec Evaluation

**Plugin:** `<slug>.md` · **Evaluated against:** current Base MCP Plugin Specification · **Date:** <YYYY-MM-DD>

## Verdict
<One of: ✅ Conforms / 🟡 Approve with minor changes / 🔴 Request changes.> <1–2 sentence rationale reflecting both static and (if run) live findings.>

## Conformance Checklist
| Requirement | Status | Notes |
|---|---|---|
| File location `plugins/<slug>.md` | ✅/🔴 | |
| Frontmatter required fields | | title/description/tags/name/version/integration/chains |
| Enum validity | | integration/shell/auth/risk |
| chains ⊆ supported set | | |
| tags (vocabulary, net-new flagged) | | |
| integration most-specific | | |
| `> [!IMPORTANT]` callout first | | |
| `## Overview` | | |
| `## Surface Routing` (+ chat-only behavior) | | |
| `## Orchestration` | | |
| `## Submission` (names tool + mapping) | | |
| `## Example Prompts` | | |
| Conditional sections (Detection/Installation/Auth/Endpoints/Commands/Risks) | | per flags |
| Canonical headings | | |
| Canonical order / anchors intact | | |
| allowlist accuracy | | |
| Neutral language (no yield claims, no steering) | | |
| Geoblock parity (if perps/prediction/gambling) | | frontend vs API |
| Disclaimers in onboarding callout | | |
| High-risk category gate (perps/prediction/privacy) | | legal review needed? |
| Contribution scope (no self-registration) | | SKILL.md / Examples / Conformance table |

## Detailed Findings
<Numbered. Each: severity (blocker/major/minor/nit) — what's wrong — spec ref — concrete fix.>

## Live API / SDK Verification
<Only if run. Table: Endpoint/Command | Tested how | Result ✅/⚠️/❌ | Evidence. + prose noting any contradiction between live behavior and the doc's claims. Update Verdict if live findings change it, noting the change explicitly.>

## Security & Safety Notes
<Specific concerns: untrusted calldata, SSRF, auth/key handling, PII, irreversibility, risk-tag honesty.>

## Recommended Changes
<Concise, prioritized bullets.>
```

## Notes
- Verdict legend: ✅ conforms · 🟡 approve with changes · 🔴 request changes.
- If a plugin predates a spec restructure, still evaluate against the **current** spec and note staleness.
