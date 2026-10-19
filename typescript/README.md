# Exogram TypeScript & Node.js Client SDK (`v0.2.0`)

[![npm](https://img.shields.io/npm/v/@exogram/sdk)](https://www.npmjs.com/package/@exogram/sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official TypeScript & Node.js SDK for **Exogram** — Personal Neural Network (`Work · People · Life`), Encrypted Memory Vault, and Deterministic `0.07ms` Instinct Action Governance.

## Installation

```bash
npm install @exogram/sdk
```

## Quickstart (Zero-Signup Local Mode or Cloud)

```typescript
import { ExogramClient } from '@exogram/sdk';

// Runs in Zero-Signup Local Mode if no apiKey is provided, or Cloud Mode with apiKey
const client = new ExogramClient();

async function main() {
    // 1. Store memory in the Personal Neural Network
    const rec = await client.vault.store('Deploy target is Cloudflare Workers Global Edge', {
        namespace: 'work',
        sphere: 'Work',
        confidence: 0.96
    });

    // 2. Multi-hop associative retrieval (Infinite-Hop Spreading Activation + HippoRAG 2 PPR)
    const context = await client.neuralNetwork.retrieve('What is our deploy target?', {
        spheres: ['Work', 'People', 'Life'],
        maxHops: 4
    });

    // 3. Deterministic 0.07ms State-Hash & Instinct Action Gate
    const judgment = await client.governance.evaluateAction({
        agentId: 'ts-agent',
        actionType: 'deploy_worker',
        parameters: { target: 'cloudflare' },
        stateHash: context.stateHash
    });

    if (judgment.permitted && judgment.executionToken) {
        const receipt = await client.actions.execute(judgment.executionToken);
        console.log(`Committed! Ledger Hash: ${receipt.ledgerHash}`);
    }
}

main();
```

## License

MIT — see [LICENSE](LICENSE) for details.
