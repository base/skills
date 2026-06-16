# PR Comment Guidelines

When reviewing a plugin PR, draft the comment to a file first. **Only post when explicitly instructed.**

## Style rules
- **Professional and concise.** Skimmable. Actionable.
- **No emojis.**
- **No compliments / no praise.** Don't tell authors their work is good. Omit "Strengths." Don't include non-actionable "this part is correct" notes (the only exception: a brief "leave X as-is" guard if there's real risk of them breaking a working piece while changing other things — and frame it as guidance, not praise).
- **No testing-context asides.** Never mention how the finding was produced (no "we ran read-only", "no funds moved", etc.). State findings as **facts about the plugin / API / contracts**, e.g. "`POST /x` returns HTTP 500 on all endpoints," "the API requires an object, not a string," "Seaport calldata isn't returned as hex."
- **Cite specifics**: field names, endpoints, file paths, section names, contract behavior. Link shared files (e.g. the tag vocabulary in `references/plugin-spec.md`) when asking for an edit there.

## Structure
Open with one neutral framing sentence (what's needed before merge, no praise). Then group findings:

```markdown
<one-line framing — e.g. "A few changes before merge:" or "There are structural and functional issues to resolve before this can be reviewed for merge.">

**Required**
- <blocking/major items — what's wrong + the concrete fix>

**Minor**
- <minor/nit items>
```

- Use **Required** for blockers/majors, **Minor** for the rest. Call out "blocking" explicitly when an item makes the plugin unusable for the default wallet or unroutable.
- If there are no required items, omit the **Required** section (don't pad).
- Sub-bullet multi-part items (e.g. several request-schema mismatches under one bullet).

## Always include when applicable

- **Contribution scope (Required) — if the PR edits shared/registry files.** Tell them to revert the `SKILL.md` plugins-table row and any `references/plugin-spec.md` edits to the Integration Types "Examples" cell, the "Existing Plugin Conformance" table, or the plugin count — maintainers register plugins when the program is ready. Preserve only a genuinely net-new tag-vocabulary addition. Limit the diff to `plugins/<slug>.md` (+ that tag line). Tailor: list exactly which files/edits to revert for this PR.

## Calibration (don't over-ask)
- Don't recommend `irreversible` on swap plugins (see evaluation-criteria gotcha #2).
- Don't mandate a specific `version` number; at most flag package-mirroring "in case unintended."
- Don't ask for things the MCP client handles (e.g. transport headers like `Mcp-Session-Id` are handled by the client, not the plugin).
- Don't flag a correct chat-only "stop" as a defect.

## Posting (only when instructed)
```bash
gh pr comment <n> --repo base/skills --body-file <comment-file>
```
