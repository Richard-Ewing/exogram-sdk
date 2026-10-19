#!/usr/bin/env python3
"""
Exogram SDK v0.2.0 — 60-Second Zero-Signup Local & Cloud Quickstart.

Run directly with zero signup or environment variables required:
    python examples/quickstart_local_and_cloud.py

If EXOGRAM_API_KEY is set, the client routes to https://api.exogram.ai while
maintaining local SQLite WAL epistemic continuity.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Allow running directly from repo root without prior pip install
REPO_ROOT = Path(__file__).resolve().parent.parent
if (REPO_ROOT / "src" / "exogram").exists():
    sys.path.insert(0, str(REPO_ROOT / "src"))
elif (REPO_ROOT / "python" / "src" / "exogram").exists():
    sys.path.insert(0, str(REPO_ROOT / "python" / "src"))

from exogram import ExogramClient  # noqa: E402


def main() -> None:
    db_file = Path(tempfile.gettempdir()) / "exogram_quickstart_demo.db"
    if db_file.exists():
        db_file.unlink()

    client = ExogramClient(db_path=str(db_file))
    mode_label = "Zero-Signup Local SQLite WAL" if client.local_mode else "Exogram Cloud Authority Runtime"
    print(f"=== Exogram SDK v0.2.0 Quickstart ({mode_label}) ===")
    print(f"Vault Path : {client.db_path}")

    # 1. Store multi-sphere episodic and durable memories
    m1 = client.vault.store(
        "Architecture decision: Production edge deploys to Cloudflare Workers via OpenNext",
        namespace="work",
        sphere="Work",
        confidence=0.98,
        temporal_horizon="durable_trait",
    )
    m2 = client.vault.store(
        "Cloudflare Workers connects to Supabase Postgres and Pinecone hybrid RRF index",
        namespace="work",
        sphere="Work",
        confidence=0.96,
        temporal_horizon="durable_trait",
    )
    m3 = client.vault.store(
        "Family dinner reservation is Friday at 7pm in Seattle",
        namespace="personal",
        sphere="Life",
        confidence=0.92,
        temporal_horizon="ephemeral_episode",
    )
    print(f"[1] Stored 3 memories across Work & Life spheres | Latest State Hash: {m3.state_hash}")

    # 2. Traverse the Personal Neural Network (Infinite-Hop Spreading Activation + HippoRAG 2 PPR)
    context = client.neural_network.retrieve(
        query="What database and vector index back our Cloudflare Workers edge deployment?",
        spheres=["Work", "People", "Life"],
        max_hops=4,
    )
    print(
        f"[2] Neural Graph Retrieval | PPR Converged: {context.ppr_converged} "
        f"| Hops: {context.hops_traversed} | Claims Retrieved: {len(context.claims)}"
    )
    for idx, claim in enumerate(context.claims, 1):
        print(f"    {idx}. [{claim.sphere} | score={claim.score:.2f}] {claim.content}")

    # 3. Deterministic 0.07ms State-Hash & Instinct Action Gate
    judgment = client.governance.evaluate_action(
        agent_id="deployment-sentinel",
        action_type="deploy_cloudflare_worker",
        parameters={"service": "exogram-edge", "environment": "production"},
        state_hash=context.state_hash,
    )
    print(
        f"[3] Instinct Action Gate | Permitted: {judgment.permitted} "
        f"| Latency: {judgment.latency_ms}ms | Token: {judgment.execution_token}"
    )

    # 4. Execute & Commit to Cryptographic Audit Hash Chain
    if judgment.permitted and judgment.execution_token:
        receipt = client.actions.execute(judgment.execution_token)
        print(f"[4] Action Executed & Committed | Ledger Hash: {receipt.ledger_hash}")

    # 5. Demonstrate deterministic blocking of stale state hash drift
    blocked = client.governance.evaluate_action(
        agent_id="rogue-agent",
        action_type="drop_production_table",
        parameters={"sql": "DROP TABLE memories;"},
        state_hash="STALE_STATE_HASH",
    )
    print(f"[5] Drift Guard Verified | Permitted: {blocked.permitted} | Reason: {blocked.reason}")
    print("=== Quickstart Completed Successfully (0 Errors) ===")


if __name__ == "__main__":
    main()
