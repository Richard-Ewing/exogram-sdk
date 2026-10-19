import os
import sqlite3
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from exogram import (
    ActionJudgment,
    AsyncExogram,
    AsyncExogramClient,
    ExecutionReceipt,
    Exogram,
    ExogramClient,
    MemoryRecord,
    NeuralContextPacket,
)


def test_exports_and_aliases():
    assert ExogramClient is Exogram
    assert AsyncExogramClient is AsyncExogram


def test_zero_signup_local_sqlite_wal_mode(tmp_path: Path):
    db_file = tmp_path / "test_vault.db"
    with patch.dict(os.environ, clear=True):
        client = ExogramClient(db_path=str(db_file))
        assert client.local_mode is True
        assert db_file.exists()

        # Verify SQLite WAL pragma is active on the database file
        conn = sqlite3.connect(str(db_file))
        try:
            mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
            assert mode.lower() == "wal"
        finally:
            conn.close()


def test_subclients_vault_neural_governance_actions(tmp_path: Path):
    db_file = tmp_path / "subclients_vault.db"
    client = ExogramClient(local_mode=True, db_path=str(db_file))

    # 1. Vault store & scalar conflict supersession
    rec1 = client.vault.store(
        "Deploy target is Cloudflare Workers in us-east",
        namespace="work",
        sphere="Work",
        confidence=0.96,
        temporal_horizon="durable_trait",
    )
    assert isinstance(rec1, MemoryRecord)
    assert rec1.id.startswith("mem_")
    assert rec1.state_hash.startswith("sha256:")

    # Store associative 2nd-hop memory connecting Cloudflare Workers -> OpenNext adapter -> Production Pipeline
    rec2 = client.vault.store(
        "Cloudflare Workers uses OpenNext adapter for Production Pipeline rollout",
        namespace="work",
        sphere="Work",
        confidence=0.94,
    )
    assert rec2.state_hash != rec1.state_hash

    # Scalar conflict supersession on same subject+predicate prefix
    rec3 = client.vault.store(
        "Deploy target is Cloudflare Workers Global Edge",
        namespace="work",
        sphere="Work",
        confidence=0.98,
    )
    assert rec3.conflicts_superseded >= 1

    # 2. Vault search
    search_hits = client.vault.search("Cloudflare Workers", namespace="work", spheres=["Work"], top_k=5)
    assert len(search_hits) >= 2
    assert any("Global Edge" in m.content for m in search_hits)
    assert not any("in us-east" in m.content for m in search_hits)

    # 3. Personal Neural Network multi-hop retrieval (HippoRAG 2 PPR + Spreading Activation)
    packet = client.neural_network.retrieve(
        query="What adapter powers our Production Pipeline?",
        spheres=["Work", "People", "Life"],
        max_hops=4,
    )
    assert isinstance(packet, NeuralContextPacket)
    assert packet.ppr_converged is True
    assert packet.state_hash.startswith("sha256:")
    assert len(packet.claims) >= 1
    assert len(packet.entities) >= 1

    # 4. Deterministic 0.07ms Governance evaluate_action & Actions execute
    judgment = client.governance.evaluate_action(
        agent_id="release-sentinel",
        action_type="deploy_production_worker",
        parameters={"target": "cloudflare", "env": "production"},
        state_hash=packet.state_hash,
    )
    assert isinstance(judgment, ActionJudgment)
    assert judgment.permitted is True
    assert judgment.execution_token is not None
    assert judgment.execution_token.startswith("exo_tok_")
    assert judgment.latency_ms == 0.07

    receipt = client.actions.execute(judgment.execution_token)
    assert isinstance(receipt, ExecutionReceipt)
    assert receipt.committed is True
    assert receipt.execution_token == judgment.execution_token
    assert receipt.ledger_hash.startswith("sha256:")


def test_governance_blocks_stale_hash_and_destructive_sql(tmp_path: Path):
    db_file = tmp_path / "guard_vault.db"
    client = Exogram(local_mode=True, db_path=str(db_file))

    stale_judgment = client.governance.evaluate_action(
        agent_id="rogue-agent",
        action_type="mutate_config",
        parameters={"key": "val"},
        state_hash="STALE_STATE_HASH",
    )
    assert stale_judgment.permitted is False
    assert stale_judgment.execution_token is None
    assert "STATE_HASH_DRIFT" in stale_judgment.reason

    destructive_judgment = client.governance.evaluate_action(
        agent_id="rogue-agent",
        action_type="sql_exec",
        parameters={"query": "DROP TABLE memories;"},
    )
    assert destructive_judgment.permitted is False
    assert "BLOCKED_BY_INSTINCT" in destructive_judgment.reason


@patch("exogram.client.httpx.Client.post")
def test_remote_evaluate_allowed(mock_post, tmp_path: Path):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"token": "eval-tok-123"}

    client = Exogram(api_key="exo_live_test_token", api_url="https://test.api", db_path=str(tmp_path / "r1.db"))
    res = client.evaluate("db_write", payload={"key": "val"})

    assert res.allowed is True
    assert res.token == "eval-tok-123"
    assert res.status == "ALLOWED"


@patch("exogram.client.httpx.Client.post")
def test_remote_evaluate_blocked(mock_post, tmp_path: Path):
    mock_post.return_value.status_code = 403
    mock_post.return_value.text = "Forbidden by policy"

    client = Exogram(token="exo_live_test_token", api_url="https://test.api", db_path=str(tmp_path / "r2.db"))
    res = client.evaluate("db_write")

    assert res.allowed is False
    assert res.status == "BLOCKED"
    assert "Forbidden" in (res.policy_violation or "")


@patch("exogram.client.httpx.Client.post")
def test_remote_commit_store_and_search(mock_post, tmp_path: Path):
    mock_post.return_value.status_code = 200
    mock_post.return_value.text = "OK"
    mock_post.return_value.json.return_value = {
        "memory_id": "mem-456",
        "conflicts_detected": 0,
        "results": [{"content": "Fact 1", "score": 0.92}],
    }

    client = Exogram(token="exo_live_test_token", api_url="https://test.api", db_path=str(tmp_path / "r3.db"))

    commit_res = client.commit("eval-tok-123", "success")
    assert commit_res.committed is True
    assert commit_res.status == "COMMITTED"

    store_res = client.store_record("Fact content")
    assert store_res.stored is True
    assert store_res.memory_id == "mem-456"

    alias_store_res = client.store("Fact content alias")
    assert alias_store_res.stored is True

    search_res = client.search_records("query")
    assert search_res.total_found == 1
    assert search_res.results[0].content == "Fact 1"

    alias_search_res = client.search("query")
    assert alias_search_res.total_found == 1


@patch("exogram.client.httpx.Client.post")
def test_governed_decorator(mock_post, tmp_path: Path):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"token": "eval-tok-123"}
    mock_post.return_value.text = "OK"

    client = Exogram(token="exo_live_test_token", api_url="https://test.api", db_path=str(tmp_path / "r4.db"))

    @client.governed(action_type="custom_action")
    def my_function(x: int, y: int) -> int:
        return x + y

    result = my_function(2, 3)
    assert result == 5
    assert mock_post.call_count == 2


@pytest.mark.asyncio
@patch("exogram.client.httpx.AsyncClient.post")
async def test_async_evaluate(mock_post, tmp_path: Path):
    mock_resp = httpx.Response(200, json={"token": "async-tok-123"})
    mock_post.return_value = mock_resp

    async_client = AsyncExogramClient(api_key="exo_live_test_token", db_path=str(tmp_path / "r5.db"))
    res = await async_client.evaluate("async_action")

    assert res.allowed is True
    assert res.token == "async-tok-123"
