# 🤖 Base AI Agent Skills & MCP Studio

An interactive **AI Agent Skills Sandbox**, **Base MCP Protocol Runner**, and **On-Chain Capability Inspector** for **Base Skills (`base/skills`)**.

---

## 🌟 Key Features

- 🤖 **On-Chain Agentic Capabilities**: Equip AI agents (Claude, GPT, Cursor) with native Base skills to launch ERC-20 tokens, swap on Uniswap V3, and settle X402 micropayments.
- ⚡ **Base MCP Server Protocol**: Native Model Context Protocol interface for wallet actions (`mcp.base.org`).
- 🌐 **Interactive Web Studio**: Live Agent Skills sandbox and execution payload inspector on `http://localhost:3426`.
- ⌨️ **Universal CLI (`base-skills-cli`)**: Terminal utility for listing and executing Base agent skills.

---

## 🚀 Quickstart

```bash
# Launch Base Skills Studio
npm start
# Open http://localhost:3426

# Or run via CLI
node bin/base-skills-cli.js list
node bin/base-skills-cli.js run erc20_token_launcher
```
