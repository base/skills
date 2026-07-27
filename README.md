# Base Skills

![Base](logo.webp)

[Agent Skills](https://agentskills.io) for building on [Base](https://base.org). These skills enable AI agents to connect to Base, deploy contracts, integrate wallets, run nodes, and more.

<!-- Badge row 1 - status -->

[![GitHub contributors](https://img.shields.io/github/contributors/base/skills)](https://github.com/base/skills/graphs/contributors)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/w/base/skills)](https://github.com/base/skills/graphs/contributors)
![GitHub repo size](https://img.shields.io/github/repo-size/base/skills)

<!-- Badge row 2 - links and profiles -->

[![Website base.org](https://img.shields.io/website-up-down-green-red/https/base.org.svg)](https://base.org)
[![Blog](https://img.shields.io/badge/blog-up-green)](https://base.mirror.xyz/)
[![Docs](https://img.shields.io/badge/docs-up-green)](https://docs.base.org/)
[![Discord](https://img.shields.io/discord/1067165013397213286?label=discord)](https://base.org/discord)
[![Twitter Base](https://img.shields.io/twitter/follow/Base?style=social)](https://twitter.com/Base)

<!-- Badge row 3 - detailed status -->

[![GitHub pull requests by-label](https://img.shields.io/github/issues-pr-raw/base/skills)](https://github.com/base/skills/pulls)
[![GitHub Issues](https://img.shields.io/github/issues-raw/base/skills.svg)](https://github.com/base/skills/issues)

## Recommended Skills

Consolidated skills that cover the most common use cases. Each uses progressive reference loading — the skill loads a single entry point and pulls in detailed references only when needed.

| Skill | Install | Description |
| ----- | ------- | ----------- |
| [build-on-base](./skills/build-on-base/SKILL.md) | `npx skills add base/skills --skill build-on-base` | Complete Base development playbook: network, contracts, wallet auth, payments, attribution, and migrations. Consolidates all individual skills into one. |
| [base-mcp](./skills/base-mcp/SKILL.md) | `npx skills add base/skills --skill base-mcp` | Base MCP server — gives your AI assistant a wallet via mcp.base.org. Sending, swapping, signing, batched calls, balances, and partner plugins for lending, swaps, and more. |
| [vibenet](./skills/vibenet/SKILL.md) | `npx skills add base/skills --skill vibenet` | Build on [vibenet](https://chain.base.org/vibenet), the Base Vibes devnet for native account abstraction (EIP-8130) with viem: smart accounts, batched calls, session keys and policies, and ERC-8168 payer gas sponsorship. |

## Installation

Install with [Vercel's Skills CLI](https://skills.sh):

```bash
npx skills add base/skills
```

## Usage

Skills are automatically available once installed. The agent will use them when relevant tasks are detected.

**Examples:**

```text
Deploy my contract to Base Sepolia
```

```text
How do I connect to Base mainnet?
```

```text
Add Sign in with Base to my app
```

```text
Convert my existing Farcaster miniapp to a standard app on Base
```

```text
Register my trading bot and add builder code attribution to its transactions
```

```text
Create an EIP-8130 smart account on vibenet and fund it from the faucet
```

```text
Deploy a smart account on vibenet with sponsored gas, so the user needs no ETH
```

```text
Authorize a session key on my 8130 account with a weekly USDC spend limit
```

### Example: gasless onboarding on vibenet

A worked example of what the `vibenet` skill produces — creating an EIP-8130
smart account and deploying it with zero user funds, via an ERC-8168 payer:

```ts
import type { Hex } from "viem";
import { createPublicClient, http } from "viem";
import { generatePrivateKey, privateKeyToAccount } from "viem/accounts";
import {
  allPhasesSucceeded,
  newSmartAccount8130,
  waitForTransactionReceipt8130,
} from "viem/experimental/eip8130";
import { createPayerClient, sendSponsoredCalls } from "viem/experimental/eip8168";

const chain = {
  id: 84538453,
  name: "vibenet",
  nativeCurrency: { name: "Ether", symbol: "ETH", decimals: 18 },
  rpcUrls: { default: { http: ["https://rpc.vibes.base.org"] } },
};
const client = createPublicClient({ chain, transport: http() });

// The address is derived locally — synchronous, no RPC, nothing on-chain yet.
// (The fork types `signer` for P-256 keys, so a K1 account needs a cast.)
const signer = privateKeyToAccount(generatePrivateKey());
const account = newSmartAccount8130({ signer: signer as never });

// There is no deploy step: the account is created by its first transaction.
// The payer covers gas, so this works at a zero balance — no faucet needed.
const payerClient = createPayerClient({
  url: "https://api.vibes.base.org/api/vibenet/account/payer",
});
const { transactionHash: hash } = (await sendSponsoredCalls(client, {
  account,
  payerClient,
  accountChanges: [account.createChange], // only on the first tx
  calls: [{ to: account.address, value: 0n, data: "0x" }],
  context: { flow: "onboarding" },
})) as unknown as { transactionHash: Hex };

const receipt = await waitForTransactionReceipt8130(client, { hash });
if (!allPhasesSucceeded(receipt)) throw new Error("a phase reverted");
```

See the [vibenet skill](./skills/vibenet/SKILL.md) for the install steps (the
8130 tooling ships on a viem fork branch), the account lifecycle, session keys,
and the devnet's sharper edges.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the terms of the included LICENSE file.

---
[Base]: https://base.org
