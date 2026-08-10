/**
 * Base AI Agent Skills Configuration
 */

export const BASE_SKILLS_CONFIG = {
  ecosystem: {
    name: 'Base AI Agent Skills Collection',
    installer: 'npx skills add base/skills',
    mcpServer: 'mcp.base.org',
    network: 'Base Mainnet (8453)',
  },
  skills: [
    {
      id: 'base_mcp_wallet',
      name: 'Base Model Context Protocol (MCP) Wallet',
      category: 'Wallet & Auth',
      description: 'Provides AI models (Claude, GPT) with wallet capabilities for transaction signing & EVM state reads.',
    },
    {
      id: 'erc20_token_launcher',
      name: 'Base ERC-20 Token Launcher',
      category: 'Tokenomics',
      description: 'Allows AI agents to programmatically deploy and initialize custom ERC-20 tokens on Base.',
    },
    {
      id: 'uniswap_v3_swap',
      name: 'Base Uniswap V3 Swap Router',
      category: 'DeFi',
      description: 'Executes automated token swaps with optimal routing and slippage bounds.',
    },
    {
      id: 'x402_micropayment_settler',
      name: 'X402 Protocol Micropayment Settler',
      category: 'Agent Commerce',
      description: 'Handles HTTP 402 Payment Required challenges via Base USDC micropayments.',
    },
  ],
};
