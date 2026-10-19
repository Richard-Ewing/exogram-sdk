import json
import os
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from mcp_server_exogram.server import (
    evaluate_instinct_action_gate,
    exogram_commit_action,
    exogram_evaluate_action,
    exogram_search_records,
    exogram_store_record,
    get_headers,
    is_local_mode,
    render_live_widget,
    search_memory_vault,
    traverse_neural_graph,
    update_memory_vault,
)


def test_zero_signup_local_mode_when_no_token_set(tmp_path: Path):
    db_file = tmp_path / "mcp_local.db"
    with patch.dict(os.environ, {"EXOGRAM_DB_PATH": str(db_file)}, clear=True):
        assert is_local_mode() is True
        headers = get_headers(strict=False)
        assert "Bearer" in headers["Authorization"]

        # 1. update_memory_vault
        store_json = update_memory_vault(
            content="Exogram uses SQLite WAL for zero-signup local mode",
            namespace="work",
            sphere="Work",
            confidence=0.97,
            temporal_horizon="durable_trait",
        )
        store_data = json.loads(store_json)
        assert store_data["status"] == "STORED"
        assert store_data["record"]["state_hash"].startswith("sha256:")

        # 2. search_memory_vault
        search_json = search_memory_vault("SQLite WAL", namespace="work", spheres="Work")
        search_data = json.loads(search_json)
        assert search_data["total_found"] >= 1

        # 3. traverse_neural_graph
        graph_json = traverse_neural_graph("SQLite WAL", spheres="Work,People,Life", max_hops=4)
        graph_data = json.loads(graph_json)
        assert graph_data["ppr_converged"] is True
        assert len(graph_data["entities"]) >= 1

        # 4. evaluate_instinct_action_gate
        gate_json = evaluate_instinct_action_gate(
            agent_id="cursor-agent",
            action_type="git_push",
            parameters='{"branch": "main"}',
            state_hash=graph_data["state_hash"],
        )
        gate_data = json.loads(gate_json)
        assert gate_data["permitted"] is True
        assert gate_data["latency_ms"] == 0.07

        # 5. render_live_widget
        tile_json = render_live_widget(
            tile_type="checklist",
            title="Release Checklist",
            data_json='{"items": ["Run pytest", "Push to main"]}',
        )
        tile_data = json.loads(tile_json)
        assert tile_data["valid"] is True
        assert tile_data["tile"]["tile_type"] == "checklist"


def test_get_headers_success():
    with patch.dict(os.environ, {"EXOGRAM_API_KEY": "test-token", "EXOGRAM_API_URL": "https://test.api"}):
        headers = get_headers()
        assert headers["Authorization"] == "Bearer test-token"
        assert headers["Content-Type"] == "application/json"


@patch("mcp_server_exogram.server.httpx.Client.post")
def test_evaluate_action_success(mock_post):
    with patch.dict(os.environ, {"EXOGRAM_BEARER_TOKEN": "test-token", "EXOGRAM_API_URL": "https://test.api"}):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"token": "test-eval-token"}

        result = exogram_evaluate_action("test_action", "default", "agent-1", '{"key": "value"}')
        assert "STATUS: ALLOWED. Execution Token Issued: test-eval-token" in result


@patch("mcp_server_exogram.server.httpx.Client.post")
def test_evaluate_action_403(mock_post):
    with patch.dict(os.environ, {"EXOGRAM_BEARER_TOKEN": "test-token", "EXOGRAM_API_URL": "https://test.api"}):
        mock_post.return_value.status_code = 403
        mock_post.return_value.text = "Forbidden action"

        result = exogram_evaluate_action("test_action", "default", "agent-1", '{"key": "value"}')
        assert "STATUS: BLOCKED. Policy violation: Forbidden action" in result


@patch("mcp_server_exogram.server.httpx.Client.post")
def test_evaluate_action_network_error(mock_post):
    with patch.dict(os.environ, {"EXOGRAM_BEARER_TOKEN": "test-token", "EXOGRAM_API_URL": "https://test.api"}):
        mock_post.side_effect = httpx.RequestError("Network error")

        result = exogram_evaluate_action("test_action", "default", "agent-1", "{}")
        assert "STATUS: NETWORK FAILURE" in result


@patch("mcp_server_exogram.server.httpx.Client.post")
def test_commit_action_success(mock_post):
    with patch.dict(os.environ, {"EXOGRAM_BEARER_TOKEN": "test-token", "EXOGRAM_API_URL": "https://test.api"}):
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "OK"

        result = exogram_commit_action("test-eval-token", "success")
        assert "STATUS: COMMITTED" in result
        assert "OK" in result


@patch("mcp_server_exogram.server.httpx.Client.post")
def test_commit_action_error(mock_post):
    with patch.dict(os.environ, {"EXOGRAM_BEARER_TOKEN": "test-token", "EXOGRAM_API_URL": "https://test.api"}):
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = "Internal Error"

        result = exogram_commit_action("test-eval-token", "failure")
        assert "STATUS: COMMIT ERROR. Code 500" in result


@patch("mcp_server_exogram.server.httpx.Client.post")
def test_store_record_success(mock_post):
    with patch.dict(os.environ, {"EXOGRAM_BEARER_TOKEN": "test-token", "EXOGRAM_API_URL": "https://test.api"}):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"memory_id": "mem-123", "conflicts_detected": 1}

        result = exogram_store_record("User likes test")
        assert "STATUS: STORED. Record ID: mem-123 | 1 conflict(s) detected" in result


@patch("mcp_server_exogram.server.httpx.Client.post")
def test_store_record_429(mock_post):
    with patch.dict(os.environ, {"EXOGRAM_BEARER_TOKEN": "test-token", "EXOGRAM_API_URL": "https://test.api"}):
        mock_post.return_value.status_code = 429
        mock_post.return_value.text = "Too many requests"

        result = exogram_store_record("User likes test")
        assert "STATUS: RATE LIMITED. Too many requests" in result


@patch("mcp_server_exogram.server.httpx.Client.post")
def test_search_records_success(mock_post):
    with patch.dict(os.environ, {"EXOGRAM_BEARER_TOKEN": "test-token", "EXOGRAM_API_URL": "https://test.api"}):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "results": [
                {"content": "Match 1", "score": 0.95},
                {"content": "Match 2", "score": 0.85},
            ]
        }

        result = exogram_search_records("test query")
        assert "Found 2 matching records:" in result
        assert "[0.95] Match 1" in result
        assert "[0.85] Match 2" in result


@patch("mcp_server_exogram.server.httpx.Client.post")
def test_search_records_empty(mock_post):
    with patch.dict(os.environ, {"EXOGRAM_BEARER_TOKEN": "test-token", "EXOGRAM_API_URL": "https://test.api"}):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"results": []}

        result = exogram_search_records("test query")
        assert "No matching records found." in result
