# Custom / Non-Native Plugins

The native plugins shipped with this skill (Morpho, Moonwell, Uniswap, Avantis) have their HTTP APIs **allowlisted in the Base MCP `web_request` tool**. This matters because Claude and ChatGPT restrict which APIs an agent can call directly from their surface — `web_request` is what makes those calls possible. For native plugins, `web_request` works out of the box.

If the user introduces a **custom plugin** or pastes instructions to interact with a protocol that isn't one of the native plugins, its API host is almost certainly **not** in the `web_request` allowlist and the call will be rejected. Do not silently retry against an allowlist-rejected host — pick one of the paths below based on your environment.

## Path 1 — Harness has a direct HTTP tool

If the current environment lets you call HTTP APIs directly (e.g. Claude Code, Codex, Cursor, or any harness where you have a fetch / curl / shell tool), **use that tool to make the call yourself**. Do not route it through `web_request`.

Any HTTP method works here (GET, POST, etc.), assuming the harness's HTTP tool supports it.

## Path 2 — Claude / ChatGPT consumer surfaces

Claude and ChatGPT *can* fetch GET URLs themselves, but for security reasons they will only fetch URLs that the **user has pasted into the chat**. The agent cannot freely construct and fetch arbitrary URLs on its own.

That makes the flow effectively **GET-only**: there's no equivalent escape hatch for POST/PUT/DELETE with custom headers and a body, because the user can't realistically inject those into the chat in a fetchable form.

So for non-native plugins on Claude / ChatGPT consumer surfaces:

- **Only GET-style APIs are viable.** If the protocol's API requires POST or other write methods to retrieve calldata, surface this limitation to the user — explain that their environment can't perform the fetch and that they would need a harness with HTTP tools (e.g. Claude Code) to proceed.
- For GET endpoints:
  1. Construct the full URL with every query parameter encoded inline (address, amount, slippage, chain, etc.).
  2. Show the URL to the user and ask them to paste it back into the chat. Once pasted, you can fetch it yourself — that's the security model these surfaces enforce.
  3. Parse the response and continue the flow (e.g. map returned calldata into the batched-calls tool, then walk through the approval flow — see [approval-mode.md](approval-mode.md) and [batch-calls.md](batch-calls.md)).

## Decision summary

| Situation | What to do |
|-----------|------------|
| Native plugin, any harness | Use `web_request` directly. |
| Non-native plugin, harness has an HTTP tool (Claude Code, Codex, Cursor, …) | Call the API with the harness's HTTP tool. Any method is fine. |
| Non-native plugin, Claude / ChatGPT consumer apps | GET only. Construct the URL, ask the user to paste it into the chat so you're allowed to fetch it, then parse the response. If the API needs POST, tell the user this surface can't support it. |
