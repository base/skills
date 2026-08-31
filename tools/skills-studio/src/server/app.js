/**
 * Base AI Agent Skills Web Studio Server
 */

import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import { BASE_SKILLS_CONFIG } from '../config.js';
import { defaultSkillsRunner } from '../core/skills-runner.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const WEB_ROOT = path.join(__dirname, '../../web');

const app = express();
const PORT = process.env.PORT || 3426;

app.use(cors());
app.use(express.json());
app.use(express.static(WEB_ROOT));

// 1. Config & Skills Catalogue
app.get('/api/config', (req, res) => {
  res.json({
    ecosystem: BASE_SKILLS_CONFIG.ecosystem,
    skills: BASE_SKILLS_CONFIG.skills,
  });
});

// 2. Execute Skill Call
app.post('/api/skill/execute', (req, res) => {
  try {
    const result = defaultSkillsRunner.executeSkill(req.body);
    res.json(result);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// 3. Execution History
app.get('/api/history', (req, res) => {
  res.json(defaultSkillsRunner.getHistory());
});

if (process.env.NODE_ENV !== 'test') {
  app.listen(PORT, () => {
    console.log(`\n======================================================`);
    console.log(`🤖 Base AI Agent Skills & MCP Studio Running!`);
    console.log(`🌐 Web Dashboard: http://localhost:${PORT}`);
    console.log(`⚡ Skills Registry: base/skills (npx skills add)`);
    console.log(`======================================================\n`);
  });
}

export default app;
