#!/usr/bin/env node

/**
 * Base AI Agent Skills CLI
 */

import { BASE_SKILLS_CONFIG } from '../src/config.js';
import { defaultSkillsRunner } from '../src/core/skills-runner.js';

const args = process.argv.slice(2);
const command = args[0] || 'help';

async function main() {
  switch (command.toLowerCase()) {
    case 'list': {
      console.log('\n🤖 Base AI Agent Skills Catalogue:');
      BASE_SKILLS_CONFIG.skills.forEach(s => {
        console.log(`  • [${s.id}] (${s.category})`);
        console.log(`    Name:        ${s.name}`);
        console.log(`    Description: ${s.description}\n`);
      });
      break;
    }

    case 'run': {
      const skillId = args[1] || 'erc20_token_launcher';
      console.log(`\n⚡ Executing Base AI Agent Skill '${skillId}'...`);
      const res = defaultSkillsRunner.executeSkill({ skillId, agentPrompt: 'Launch AGNT token on Base' });
      console.log(`  TX Hash:     ${res.txHash}`);
      console.log(`  Status:      ${res.status}`);
      console.log(`  Gas Cost:    ${res.gasFeeEth}`);
      console.log(`  Output:      ${JSON.stringify(res.agentOutput, null, 2)}\n`);
      break;
    }

    case 'studio': {
      console.log('\n🌐 Launching Base Skills Studio on :3426...');
      await import('../src/server/app.js');
      break;
    }

    default: {
      console.log(`
╔══════════════════════════════════════════════════════════════════╗
║               🤖 BASE AI AGENT SKILLS CLI                        ║
║        On-Chain Capabilities & MCP Tooling for Base L2           ║
╚══════════════════════════════════════════════════════════════════╝

Commands:
  base-skills-cli list                  List all available Base agent skills
  base-skills-cli run [skillId]          Execute an AI agent skill on Base L2
  base-skills-cli studio                 Launch Interactive Web Studio on :3426
      `);
      break;
    }
  }
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
