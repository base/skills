# Installing Base MCP

Server URL: `https://mcp.base.org`

---

## Claude Code (CLI · VS Code extension · JetBrains extension)

All three use the same Claude Code MCP configuration. Run in any terminal (including the integrated terminal inside VS Code or JetBrains):

```bash
claude mcp add base-account --transport http https://mcp.base.org
```

Or add manually to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "base-account": {
      "type": "http",
      "url": "https://mcp.base.org"
    }
  }
}
```

No restart needed — the server is available in the next Claude Code session.

---

## Claude Desktop

**macOS** config file: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows** config file: `%APPDATA%\Claude\claude_desktop_config.json`

Add or merge the `mcpServers` key:

```json
{
  "mcpServers": {
    "base-account": { "url": "https://mcp.base.org" }
  }
}
```

Restart Claude Desktop after saving. The server appears in the tool menu on next launch.

---

## Claude.ai (web)

1. Open **Settings** (top-right avatar → Settings)
2. Go to **Integrations**
3. Click **Add MCP server**
4. Enter the server URL: `https://mcp.base.org`
5. Click **Connect**

The OAuth flow opens automatically in a new tab.

---

## Cursor

Add to `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project-scoped):

```json
{
  "mcpServers": {
    "base-account": {
      "type": "http",
      "url": "https://mcp.base.org"
    }
  }
}
```

Restart Cursor after saving.

---

## Any other MCP-compatible client

Use the HTTP transport with server URL `https://mcp.base.org`. Consult your client's MCP documentation for the exact config format — the server URL is the only required field.

---

## OAuth Authorization

After adding the server, your client opens an OAuth flow:

1. A browser tab opens to `mcp.base.org`
2. Sign in with your Base Account — no Coinbase account required
3. Authorize the requested permissions
4. Return to your AI client — the MCP is now connected

---

## Verifying the connection

Call `get_wallets`. A successful response lists your Base Account address and any agent wallets. An error or "tool not found" means the MCP is not connected — retry the install steps above.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Tool not found / MCP not connected | Check config file syntax (valid JSON), ensure URL is `https://mcp.base.org`, restart client |
| OAuth window doesn't open | Open `https://mcp.base.org` manually in a browser and complete sign-in |
| `web_request` rejects a domain | The hostname is not in the MCP's allowlist — see plugin references for supported partner APIs |
| `get_wallets` returns no wallets | OAuth wasn't completed — re-run the auth flow |
