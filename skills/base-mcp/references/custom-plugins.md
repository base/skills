# Custom / Non-Native Plugins

The native plugins shipped with this skill (Morpho, Moonwell, Uniswap, Avantis) have their HTTP APIs **allowlisted in the Base MCP `web_request` tool**. This matters because Claude and ChatGPT restrict which APIs an agent can call directly from their surface — `web_request` is what makes those calls possible. For native plugins, `web_request` works out of the box.

If the user introduces a **custom plugin** or pastes instructions to interact with a protocol that isn't one of the native plugins, its API host is almost certainly **not** in the `web_request` allowlist and the call will be rejected. Do not silently retry against an allowlist-rejected host — pick one of the paths below based on your environment.

## Path 1 — Harness has a direct HTTP tool

If the current environment lets you call HTTP APIs directly (e.g. Claude Code, Codex, Cursor, or any harness where you have a fetch / curl / shell tool), **use that tool to make the call yourself**. Do not route it through `web_request`.

Any HTTP method works here (GET, POST, etc.), assuming the harness's HTTP tool supports it.

## Path 2 — Harness has no HTTP tool (typical on Claude / ChatGPT consumer surfaces)

When the only way to fetch an external response is to ask the user to do it, you are effectively limited to **GET endpoints**. The user can paste a URL into a browser and copy back the JSON, but they cannot reasonably send a POST/PUT/DELETE with custom headers and a body.

So for non-native plugins on Claude or ChatGPT consumer surfaces:

- **Only GET-style APIs are viable.** If the protocol's API requires POST or other write methods to retrieve calldata, surface this limitation to the user — explain that their environment can't fetch the response and that they would need a harness with HTTP tools (e.g. Claude Code) to proceed.
- For GET endpoints:
  1. Construct the full URL with every query parameter encoded inline (address, amount, slippage, chain, etc.).
  2. Show the URL to the user and ask them to open it in a browser (or run it with `curl`) and paste the response back into the chat.
  3. Parse what they paste and continue the flow (e.g. map returned calldata into the batched-calls tool, then walk through the approval flow — see [approval-mode.md](approval-mode.md) and [batch-calls.md](batch-calls.md)).

## Decision summary

| Situation | What to do |
|-----------|------------|
| Native plugin, any harness | Use `web_request` directly. |
| Non-native plugin, harness has an HTTP tool (Claude Code, Codex, Cursor, …) | Call the API with the harness's HTTP tool. Any method is fine. |
| Non-native plugin, no HTTP tool (Claude / ChatGPT consumer apps) | GET only. Construct the URL, hand it to the user, parse the response they paste back. If the API needs POST, tell the user this surface can't support it. |
