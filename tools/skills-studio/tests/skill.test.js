/**
 * Base AI Agent Skills Unit Tests
 */

import { defaultSkillsRunner } from '../src/core/skills-runner.js';

async function runSkillTests() {
  console.log('Testing Base AI Agent Skills Runner...');

  // 1. Execute Token Launcher Skill
  const res = defaultSkillsRunner.executeSkill({
    skillId: 'erc20_token_launcher',
    agentPrompt: 'Deploy AGNT token',
  });

  if (!res.txHash || res.status !== 'EXECUTED_SUCCESSFULLY') {
    throw new Error('Base AI skill execution failed');
  }

  console.log(`✅ Base AI Agent Skill Executed (${res.skillId} @ TX ${res.txHash.slice(0, 14)}...)!`);
}

runSkillTests().catch(e => {
  console.error('❌ Skill Test Failed:', e);
  process.exit(1);
});
