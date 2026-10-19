# Exogram Python Client SDK (`v0.2.0`)

[![PyPI](https://img.shields.io/pypi/v/exogram)](https://pypi.org/project/exogram/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Official Python SDK for **Exogram** — Personal Neural Network (`Work · People · Life`), Encrypted Memory Vault, and Deterministic `0.07ms` Instinct Action Governance.

Runs out-of-the-box in **Zero-Signup Local SQLite WAL Mode** (`~/.exogram/vault.db`) when no API key is set, or connects to **Exogram Cloud** (`https://exogram.ai` / `https://api.exogram.ai`) when `EXOGRAM_API_KEY` is provided.

## Installation

```bash
pip install exogram
```

## 60-Second Quickstart (Zero-Signup Local SQLite WAL or Cloud)

```python
from exogram import ExogramClient

# Automatically initializes local SQLite WAL (~/.exogram/vault.db) if no API key is set,
# or routes to Exogram Cloud when api_key="exo_live_..." or EXOGRAM_API_KEY is set.
client = ExogramClient()

# 1. Store memory claims across Work, People, and Life spheres
record = client.vault.store(
    "Deploy target is Cloudflare Workers Global Edge via OpenNext",
    namespace="work",
    sphere="Work",
    confidence=0.96,
    temporal_horizon="durable_trait",
)
print(f"Stored {record.id} | State Hash: {record.state_hash}")

# 2. Traverse multi-hop associative connections (Infinite-Hop Spreading Activation + HippoRAG 2 PPR)
context = client.neural_network.retrieve(
    query="How do we deploy to our global edge?",
    spheres=["Work", "People", "Life"],
    max_hops=4,
)
print(f"PPR Converged: {context.ppr_converged} | Claims: {len(context.claims)}")

# 3. Deterministic 0.07ms State-Hash & Instinct Pre-Mutation Action Gate
judgment = client.governance.evaluate_action(
    agent_id="release-sentinel",
    action_type="deploy_worker",
    parameters={"target": "cloudflare", "branch": "main"},
    state_hash=context.state_hash,
)

if judgment.permitted:
    receipt = client.actions.execute(judgment.execution_token)
    print(f"Committed! Ledger Hash: {receipt.ledger_hash}")
```

## License

MIT — see [LICENSE](LICENSE) for details.
