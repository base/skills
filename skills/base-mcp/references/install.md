# Installing Base MCP

Choose your app below. The whole process takes under two minutes.

---

## Claude Desktop

1. Open Claude Desktop
2. Click the **Claude** menu in the top menu bar → **Settings…**
3. Go to the **Integrations** tab
4. Click **Add integration**
5. Enter a name (e.g. `Base`) and the server URL: `https://mcp.base.org`
6. Click **Add**
7. A browser window opens — sign in to authorize (see [Authorization](#authorization) below)

> If you don't see an Integrations tab, your Claude Desktop version may be older. Update to the latest version from [claude.ai/download](https://claude.ai/download).

---

## ChatGPT (desktop app)

1. Open the ChatGPT app
2. Click your **profile picture** (top-right) → **Settings**
3. Go to the **Connectors** tab
4. Click **Add connector** → **MCP server**
5. Paste the server URL: `https://mcp.base.org`
6. Click **Connect**
7. A browser window opens — sign in to authorize (see [Authorization](#authorization) below)

---

## Claude.ai (web)

1. Go to [claude.ai](https://claude.ai) and sign in
2. Click your **profile picture** (bottom-left) → **Settings**
3. Go to the **Integrations** tab
4. Click **Add integration**
5. Paste the server URL: `https://mcp.base.org`
6. Click **Connect**
7. A browser window opens — sign in to authorize (see [Authorization](#authorization) below)

---

## Claude Code (CLI · VS Code · JetBrains)

Run this in your terminal:

```bash
claude mcp add base-account --transport http https://mcp.base.org
```

Then restart Claude Code and sign in when prompted.

---

## Cursor

Add to `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project):

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

## Authorization

After connecting the server, a browser tab opens to mcp.base.org. Here's what to do:

1. Click **Sign in with Base**
2. If you don't have a Base account yet, you can create one for free — no Coinbase account required
3. Review the permissions the app is requesting and click **Authorize**
4. The browser tab will close and you'll be taken back to your app

That's it — the MCP is now connected.

---

## Did it work?

Ask your AI assistant: **"Show me my wallets."**

If it replies with a wallet address, you're all set. If it says it doesn't have access to a wallet tool, the MCP isn't connected — try the install steps again or check the troubleshooting section below.

---

## Troubleshooting

**The browser tab for sign-in never opened**
→ Try opening `https://mcp.base.org` in your browser directly and signing in there, then re-add the server in your app.

**I see "Integration not found" or "Tool not available"**
→ The server may not have loaded yet. Restart your app and try again.

**The Integrations / Connectors tab doesn't exist**
→ Your app version may be outdated. Update to the latest version and try again.

**web_request fails with a domain error**
→ The website you're trying to reach isn't in the approved list. This is a security feature — see plugin references for supported partner APIs.
