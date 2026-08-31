/**
 * Base Skills Studio Client Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  loadConfig();
  initFormListeners();
});

function initTabs() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.nav-tab').forEach(t => t.classList.toggle('active', t === tab));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.toggle('active', p.id === `tab-${tab.dataset.tab}`));
    });
  });
}

async function loadConfig() {
  try {
    const res = await fetch('/api/config');
    const data = await res.json();

    const select = document.getElementById('select-skill');
    const grid = document.getElementById('skills-container');

    select.innerHTML = '';
    grid.innerHTML = '';

    data.skills.forEach(s => {
      // Option
      const opt = document.createElement('option');
      opt.value = s.id;
      opt.textContent = `${s.name} (${s.category})`;
      select.appendChild(opt);

      // Card
      const card = document.createElement('div');
      card.className = 'skill-card';
      card.innerHTML = `
        <div class="skill-title">${s.name}</div>
        <div class="skill-cat">${s.category} • ID: ${s.id}</div>
        <div class="text-muted" style="font-size: 0.85rem;">${s.description}</div>
      `;
      grid.appendChild(card);
    });

    updateDefaultPrompt();
    select.addEventListener('change', updateDefaultPrompt);
  } catch (e) {
    console.error(e);
  }
}

function updateDefaultPrompt() {
  const skillId = document.getElementById('select-skill').value;
  const input = document.getElementById('input-prompt');

  if (skillId === 'erc20_token_launcher') {
    input.value = 'Launch AGNT token with 1B supply on Base Mainnet';
  } else if (skillId === 'uniswap_v3_swap') {
    input.value = 'Swap 0.05 ETH for USDC on Uniswap V3';
  } else if (skillId === 'x402_micropayment_settler') {
    input.value = 'Settle X402 payment challenge for $0.03 USDC';
  } else {
    input.value = 'Execute Base Model Context Protocol Action';
  }
}

function initFormListeners() {
  document.getElementById('skill-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-run-skill');
    const outBox = document.getElementById('output-json-box');
    const resultBox = document.getElementById('skill-result-box');

    const skillId = document.getElementById('select-skill').value;
    const agentPrompt = document.getElementById('input-prompt').value;

    btn.disabled = true;
    btn.textContent = '⚡ Executing Base AI Skill...';

    try {
      const res = await fetch('/api/skill/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skillId, agentPrompt }),
      });
      const data = await res.json();

      outBox.textContent = JSON.stringify(data, null, 2);
      resultBox.innerHTML = `
        <div class="card" style="border-color: #0052ff; background: rgba(0, 82, 255, 0.08);">
          <strong style="color: #60a5fa;">⚡ Skill Executed on Base!</strong>
          <div class="mono text-muted mt-1" style="font-size: 0.75rem;">TX Hash: ${data.txHash} • Fee: ${data.gasFeeEth}</div>
        </div>
      `;
    } catch (err) {
      resultBox.innerHTML = `<div class="badge red">Execution error: ${err.message}</div>`;
    } finally {
      btn.disabled = false;
      btn.textContent = '⚡ Execute Skill on Base';
    }
  });
}
