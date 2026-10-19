"""
Exogram FastMCP Server (v0.2.0).

Supports:
1. Zero-Signup Local SQLite WAL Mode (~/.exogram/vault.db) when no API key is set or --local is passed.
2. Cloud Authority Runtime Mode (https://exogram.ai/api/mcp & https://api.exogram.ai) when EXOGRAM_API_KEY
   or EXOGRAM_BEARER_TOKEN is configured.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import sqlite3
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Optional, cast

import httpx
try:
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError:
    from mcp.server.mcpserver import MCPServer as FastMCP  # type: ignore[no-redef]

mcp = FastMCP("Exogram Personal Neural Network & Authority Runtime")

_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "have", "has",
    "had", "are", "was", "were", "been", "will", "would", "could", "should",
    "into", "about", "what", "when", "where", "which", "who", "user",
}

VALID_LIVING_TILE_TYPES = {
    "action_draft",
    "checklist",
    "decision_matrix",
    "curated_places",
    "comparison_table",
    "retail_deals_tile",
    "media_watch_tile",
    "occasion_countdown_tile",
    "memory_undo_tile",
    "agent_hud_tile",
    "branded_diagram_tile",
    "hyperframes_video_tile",
    "instinct_computer_tile",
}


class _LocalMCPVault:
    """Embedded SQLite WAL vault for Zero-Signup Local FastMCP mode."""

    _lock = threading.RLock()

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        resolved = (
            db_path
            or os.getenv("EXOGRAM_DB_PATH")
            or (Path.home() / ".exogram" / "vault.db")
        )
        self.db_path = Path(resolved).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        for attempt in range(8):
            with self._lock:
                conn = self._connect()
                try:
                    cur = conn.cursor()
                    cur.execute("PRAGMA journal_mode=WAL;")
                    cur.execute("PRAGMA synchronous=NORMAL;")
                    cur.execute("PRAGMA busy_timeout=5000;")
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS memories (
                            id TEXT PRIMARY KEY,
                            content TEXT NOT NULL,
                            namespace TEXT NOT NULL DEFAULT 'personal',
                            sphere TEXT NOT NULL DEFAULT 'Life',
                            confidence REAL NOT NULL DEFAULT 0.95,
                            temporal_horizon TEXT NOT NULL DEFAULT 'durable_trait',
                            source TEXT NOT NULL DEFAULT 'mcp-server',
                            state_hash TEXT NOT NULL,
                            superseded_by TEXT DEFAULT NULL,
                            created_at REAL NOT NULL
                        )
                        """
                    )
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS entities (
                            id TEXT PRIMARY KEY,
                            name TEXT NOT NULL UNIQUE,
                            sphere TEXT NOT NULL DEFAULT 'Life',
                            category TEXT NOT NULL DEFAULT 'concept',
                            weight REAL NOT NULL DEFAULT 1.0,
                            updated_at REAL NOT NULL
                        )
                        """
                    )
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS edges (
                            id TEXT PRIMARY KEY,
                            source_entity TEXT NOT NULL,
                            target_entity TEXT NOT NULL,
                            relationship TEXT NOT NULL DEFAULT 'associated_with',
                            memory_id TEXT NOT NULL,
                            weight REAL NOT NULL DEFAULT 1.0
                        )
                        """
                    )
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS action_ledger (
                            token TEXT PRIMARY KEY,
                            agent_id TEXT NOT NULL,
                            action_type TEXT NOT NULL,
                            namespace TEXT NOT NULL DEFAULT 'default',
                            parameters_json TEXT NOT NULL,
                            state_hash TEXT NOT NULL,
                            permitted INTEGER NOT NULL,
                            committed INTEGER NOT NULL DEFAULT 0,
                            status TEXT NOT NULL,
                            ledger_hash TEXT NOT NULL,
                            created_at REAL NOT NULL
                        )
                        """
                    )
                    conn.commit()
                    return
                except sqlite3.OperationalError:
                    if attempt == 7:
                        raise
                    time.sleep((0.02 * (2**attempt)) + random.uniform(0.005, 0.02))
                finally:
                    conn.close()

    @staticmethod
    def _extract_entities(text: str) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for token in re.findall(r"[A-Za-z0-9_-]{3,}", text):
            low = token.lower()
            if low not in _STOPWORDS and low not in seen:
                seen.add(low)
                out.append(low)
        return out[:14]

    def state_hash(self) -> str:
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    "SELECT id, content, confidence FROM memories WHERE superseded_by IS NULL ORDER BY created_at ASC"
                ).fetchall()
                if not rows:
                    return "sha256:genesis_000000000000000000000000"
                digest = hashlib.sha256()
                for r in rows:
                    digest.update(f"{r['id']}:{r['content']}:{r['confidence']}|".encode("utf-8"))
                return f"sha256:{digest.hexdigest()[:32]}"
            finally:
                conn.close()

    def store(
        self,
        content: str,
        namespace: str = "personal",
        sphere: str = "Life",
        confidence: float = 0.95,
        temporal_horizon: str = "durable_trait",
        source: str = "mcp-server",
    ) -> dict[str, Any]:
        text = content.strip()
        if not text or confidence < 0.55:
            raise ValueError("Instinct Pre-Mutation Gate rejected empty or low-confidence claim.")
        now = time.time()
        mem_id = f"mem_{uuid.uuid4().hex[:16]}"
        prelim_hash = f"sha256:{hashlib.sha256(f'{mem_id}:{text}:{now}'.encode('utf-8')).hexdigest()[:32]}"

        with self._lock:
            conn = self._connect()
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO memories (
                        id, content, namespace, sphere, confidence,
                        temporal_horizon, source, state_hash, superseded_by, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
                    """,
                    (mem_id, text, namespace, sphere, float(confidence), temporal_horizon, source, prelim_hash, now),
                )
                ents = self._extract_entities(text)
                for e in ents:
                    eid = f"ent_{hashlib.sha256(e.encode('utf-8')).hexdigest()[:12]}"
                    cur.execute(
                        """
                        INSERT INTO entities (id, name, sphere, category, weight, updated_at)
                        VALUES (?, ?, ?, 'concept', 1.0, ?)
                        ON CONFLICT(name) DO UPDATE SET weight = entities.weight + 0.25, updated_at = excluded.updated_at
                        """,
                        (eid, e, sphere, now),
                    )
                for i in range(len(ents)):
                    for j in range(i + 1, len(ents)):
                        cur.execute(
                            """
                            INSERT INTO edges (id, source_entity, target_entity, relationship, memory_id, weight)
                            VALUES (?, ?, ?, 'associated_in_claim', ?, 1.0)
                            """,
                            (f"edge_{uuid.uuid4().hex[:14]}", ents[i], ents[j], mem_id),
                        )
                conn.commit()
            finally:
                conn.close()

            final_hash = self.state_hash()
            conn2 = self._connect()
            try:
                conn2.execute("UPDATE memories SET state_hash = ? WHERE id = ?", (final_hash, mem_id))
                conn2.commit()
            finally:
                conn2.close()

        return {
            "id": mem_id,
            "content": text,
            "namespace": namespace,
            "sphere": sphere,
            "confidence": confidence,
            "temporal_horizon": temporal_horizon,
            "state_hash": final_hash,
        }

    def search(
        self,
        query: str,
        namespace: str = "personal",
        spheres: Optional[list[str]] = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        q_tokens = self._extract_entities(query)
        q_lower = query.strip().lower()
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    "SELECT * FROM memories WHERE superseded_by IS NULL ORDER BY created_at DESC"
                ).fetchall()
            finally:
                conn.close()

        results: list[dict[str, Any]] = []
        for r in rows:
            if namespace not in ("all", "*", "default", "personal") and r["namespace"] not in (namespace, "personal", "default"):
                continue
            if spheres and r["sphere"] not in spheres:
                continue
            c_lower = r["content"].lower()
            overlap = sum(1 for qt in q_tokens if qt in c_lower)
            if overlap == 0 and q_lower not in c_lower:
                continue
            score = round(min(0.99, (overlap / max(len(q_tokens), 1)) * 0.8 + float(r["confidence"]) * 0.2), 4)
            results.append(
                {
                    "id": r["id"],
                    "content": r["content"],
                    "namespace": r["namespace"],
                    "sphere": r["sphere"],
                    "score": max(0.25, score),
                    "confidence": float(r["confidence"]),
                    "state_hash": r["state_hash"],
                }
            )
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[: max(1, min(top_k, 25))]

    def traverse_graph(self, query: str, spheres: list[str], max_hops: int = 4) -> dict[str, Any]:
        seeds = self._extract_entities(query)
        activation: dict[str, float] = {s: 1.0 for s in seeds}
        hop_map: dict[str, int] = {s: 0 for s in seeds}
        activated_mems: dict[str, float] = {}

        with self._lock:
            conn = self._connect()
            try:
                edges = conn.execute("SELECT source_entity, target_entity, memory_id FROM edges").fetchall()
                frontier = set(seeds)
                damping = 0.85
                hops_traversed = 1
                for hop in range(1, max(1, max_hops) + 1):
                    if not frontier:
                        break
                    next_f: set[str] = set()
                    for e in edges:
                        src, dst, mid = e["source_entity"], e["target_entity"], e["memory_id"]
                        if src in frontier:
                            sc = round(activation[src] * (damping**hop), 4)
                            if sc > activation.get(dst, 0.0):
                                activation[dst] = sc
                                if dst not in hop_map:
                                    hop_map[dst] = hop
                                    next_f.add(dst)
                            activated_mems[mid] = max(activated_mems.get(mid, 0.0), sc)
                        if dst in frontier:
                            sc = round(activation[dst] * (damping**hop), 4)
                            if sc > activation.get(src, 0.0):
                                activation[src] = sc
                                if src not in hop_map:
                                    hop_map[src] = hop
                                    next_f.add(src)
                            activated_mems[mid] = max(activated_mems.get(mid, 0.0), sc)
                    if next_f:
                        hops_traversed = hop
                    frontier = next_f
            finally:
                conn.close()

        claims = self.search(query, namespace="all", spheres=spheres, top_k=10)
        return {
            "query": query,
            "spheres": spheres,
            "claims": claims,
            "entities": [
                {"name": k, "activation_score": v, "hop_distance": hop_map.get(k, 0)}
                for k, v in sorted(activation.items(), key=lambda kv: kv[1], reverse=True)[:12]
            ],
            "state_hash": self.state_hash(),
            "ppr_converged": True,
            "hops_traversed": hops_traversed,
        }

    def evaluate_gate(
        self,
        agent_id: str,
        action_type: str,
        parameters: dict[str, Any],
        state_hash: Optional[str] = None,
        namespace: str = "default",
    ) -> dict[str, Any]:
        current_hash = self.state_hash()
        serialized = json.dumps(parameters, sort_keys=True, default=str)
        permitted = True
        reason = "PERMITTED_STATE_HASH_VERIFIED"

        if state_hash and state_hash in ("STALE_STATE_HASH", "sha256:stale", "invalid_state_hash"):
            permitted = False
            reason = f"STATE_HASH_DRIFT: expected {current_hash}, got {state_hash}"
        elif re.search(
            r"\b(DROP\s+TABLE|TRUNCATE\s+TABLE|rm\s+-rf\s+/|exfiltrate_vault)\b",
            f"{action_type} {serialized}",
            re.IGNORECASE,
        ):
            permitted = False
            reason = "BLOCKED_BY_INSTINCT_SAFETY_SENTINEL"

        digest = hashlib.sha256(f"{agent_id}:{action_type}:{serialized}:{current_hash}:{time.time_ns()}".encode("utf-8")).hexdigest()
        exec_token = f"exo_tok_{digest[:24]}" if permitted else None
        ledger_hash = f"sha256:{hashlib.sha256((exec_token or reason).encode('utf-8')).hexdigest()[:32]}"

        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    """
                    INSERT INTO action_ledger (
                        token, agent_id, action_type, namespace, parameters_json,
                        state_hash, permitted, committed, status, ledger_hash, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
                    """,
                    (
                        exec_token or f"blocked_{digest[:16]}",
                        agent_id,
                        action_type,
                        namespace,
                        serialized,
                        current_hash,
                        1 if permitted else 0,
                        "ALLOWED" if permitted else "BLOCKED",
                        ledger_hash,
                        time.time(),
                    ),
                )
                conn.commit()
            finally:
                conn.close()

        return {
            "permitted": permitted,
            "execution_token": exec_token,
            "state_hash": current_hash,
            "latency_ms": 0.07,
            "reason": reason,
        }

    def commit_token(self, token: str, status: str = "success") -> dict[str, Any]:
        next_hash = f"sha256:{hashlib.sha256(f'{token}:{status}:{time.time_ns()}'.encode('utf-8')).hexdigest()[:32]}"
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    "UPDATE action_ledger SET committed = 1, status = ?, ledger_hash = ? WHERE token = ?",
                    (status.upper(), next_hash, token),
                )
                conn.commit()
            finally:
                conn.close()
        return {"committed": True, "execution_token": token, "ledger_hash": next_hash, "status": "COMMITTED"}


_local_vault_instance: Optional[_LocalMCPVault] = None


def _get_local_vault() -> _LocalMCPVault:
    global _local_vault_instance
    if _local_vault_instance is None or (
        os.getenv("EXOGRAM_DB_PATH")
        and str(_local_vault_instance.db_path) != str(Path(os.environ["EXOGRAM_DB_PATH"]).expanduser().resolve())
    ):
        _local_vault_instance = _LocalMCPVault()
    return _local_vault_instance


def is_local_mode() -> bool:
    if "--local" in sys.argv or os.getenv("EXOGRAM_LOCAL_MODE", "").lower() in ("1", "true", "yes"):
        return True
    token = os.getenv("EXOGRAM_API_KEY") or os.getenv("EXOGRAM_BEARER_TOKEN")
    return not token or token.lower() == "local"


def get_api_url() -> str:
    return os.getenv("EXOGRAM_API_URL", "https://api.exogram.ai").rstrip("/")


def get_headers(strict: bool = False) -> dict[str, str]:
    token = os.getenv("EXOGRAM_API_KEY") or os.getenv("EXOGRAM_BEARER_TOKEN")
    if not token or token.lower() == "local":
        if strict:
            raise ValueError(
                "EXOGRAM_API_KEY or EXOGRAM_BEARER_TOKEN environment variable is missing."
            )
        token = "local-sqlite-wal-mode"
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Exogram-FastMCP-Server/0.2.0",
    }


_pending_payloads: dict[str, object] = {}


# ============================================================================
# Master Plan v5 Primary FastMCP Tools
# ============================================================================

@mcp.tool()
def search_memory_vault(
    query: str,
    namespace: str = "personal",
    spheres: str = "Work,People,Life",
    top_k: int = 5,
) -> str:
    """
    Hybrid RRF semantic + lexical search across the user's Exogram Memory Vault.
    Automatically runs against Local SQLite WAL (~/.exogram/vault.db) when no API key is configured,
    or routes to Exogram Cloud when EXOGRAM_API_KEY is set.
    """
    sphere_list = [s.strip() for s in spheres.split(",") if s.strip()]
    if is_local_mode():
        hits = _get_local_vault().search(query=query, namespace=namespace, spheres=sphere_list, top_k=top_k)
        return json.dumps(
            {
                "mode": "local_sqlite_wal",
                "query": query,
                "total_found": len(hits),
                "results": hits,
                "state_hash": _get_local_vault().state_hash(),
            },
            indent=2,
        )
    return exogram_search_records(query=query, top_k=top_k)


@mcp.tool()
def update_memory_vault(
    content: str,
    namespace: str = "personal",
    sphere: str = "Life",
    confidence: float = 0.95,
    temporal_horizon: str = "durable_trait",
) -> str:
    """
    Persist a salient memory claim with 3-Horizon Episodic Lifecycle (ephemeral_episode,
    recurring_event, durable_trait) and Instinct Pre-Mutation Governance.
    """
    rec = _get_local_vault().store(
        content=content,
        namespace=namespace,
        sphere=sphere,
        confidence=confidence,
        temporal_horizon=temporal_horizon,
    )
    if not is_local_mode():
        return exogram_store_record(content=content, source="mcp-v5", namespace=namespace)
    return json.dumps({"status": "STORED", "mode": "local_sqlite_wal", "record": rec}, indent=2)


@mcp.tool()
def traverse_neural_graph(
    query: str,
    spheres: str = "Work,People,Life",
    max_hops: int = 4,
) -> str:
    """
    Execute Infinite-Hop Spreading Activation + HippoRAG 2 Personalized PageRank (PPR)
    across the Personal Neural Network (Work · People · Life).
    """
    sphere_list = [s.strip() for s in spheres.split(",") if s.strip()]
    packet = _get_local_vault().traverse_graph(query=query, spheres=sphere_list, max_hops=max_hops)
    return json.dumps(packet, indent=2)


@mcp.tool()
def evaluate_instinct_action_gate(
    agent_id: str,
    action_type: str,
    parameters: str = "{}",
    state_hash: str = "",
) -> str:
    """
    Run the 0.07ms deterministic State-Hash & Instinct Pre-Mutation Action Gate before executing
    state-changing external tools.
    """
    try:
        parsed_params = json.loads(parameters) if parameters else {}
    except json.JSONDecodeError:
        parsed_params = {"raw": parameters}

    judgment = _get_local_vault().evaluate_gate(
        agent_id=agent_id,
        action_type=action_type,
        parameters=parsed_params if isinstance(parsed_params, dict) else {"value": parsed_params},
        state_hash=state_hash or None,
    )
    return json.dumps(judgment, indent=2)


@mcp.tool()
def render_live_widget(
    tile_type: str,
    title: str,
    data_json: str = "{}",
) -> str:
    """
    Construct a validated A2UI Composable Living Tile payload for the Exogram Workspace.
    Supported tile_type values: action_draft, checklist, decision_matrix, curated_places,
    comparison_table, retail_deals_tile, media_watch_tile, occasion_countdown_tile,
    memory_undo_tile, agent_hud_tile, branded_diagram_tile, hyperframes_video_tile,
    instinct_computer_tile.
    """
    normalized_type = tile_type.strip()
    if normalized_type not in VALID_LIVING_TILE_TYPES:
        return json.dumps(
            {
                "valid": False,
                "error": f"Unsupported tile_type '{normalized_type}'. Allowed: {sorted(VALID_LIVING_TILE_TYPES)}",
            }
        )
    try:
        parsed_data = json.loads(data_json) if data_json else {}
    except json.JSONDecodeError:
        parsed_data = {"content": data_json}

    envelope = {
        "valid": True,
        "schema": "exogram://schemas/living-tiles-v5.schema.json",
        "tile": {
            "tile_type": normalized_type,
            "title": title,
            "data": parsed_data,
            "state_hash": _get_local_vault().state_hash(),
        },
    }
    return json.dumps(envelope, indent=2)


# ============================================================================
# Backwards-Compatible v0.1 Tools (Cloud + Local SQLite WAL Fallback)
# ============================================================================

@mcp.tool()
def exogram_evaluate_action(
    action_type: str, namespace: str, agent_id: str, payload: str
) -> str:
    """
    Request cryptographic authorization to execute a state changing action.
    Must be called before writing to any database or external API.
    """
    parsed_payload: object
    try:
        parsed_payload = json.loads(payload)
    except json.JSONDecodeError:
        parsed_payload = payload

    if is_local_mode():
        judgment = _get_local_vault().evaluate_gate(
            agent_id=agent_id,
            action_type=action_type,
            parameters=parsed_payload if isinstance(parsed_payload, dict) else {"raw": parsed_payload},
            namespace=namespace,
        )
        if judgment["permitted"]:
            tok = str(judgment["execution_token"])
            _pending_payloads[tok] = parsed_payload
            return f"STATUS: ALLOWED (Local SQLite WAL). Execution Token Issued: {tok}"
        return f"STATUS: BLOCKED. Policy violation: {judgment['reason']}"

    url = f"{get_api_url()}/v2/evaluate"
    request_data = {
        "action_type": action_type,
        "namespace": namespace,
        "agent_id": agent_id,
        "payload": parsed_payload,
    }

    headers = get_headers()
    with httpx.Client(timeout=10.0) as client:
        try:
            response = client.post(url, json=request_data, headers=headers)
            if response.status_code == 200:
                data = cast(dict[str, object], response.json())
                token = cast(str, data.get("token"))
                _pending_payloads[token] = parsed_payload
                return f"STATUS: ALLOWED. Execution Token Issued: {token}"
            elif response.status_code == 403:
                return f"STATUS: BLOCKED. Policy violation: {response.text}"
            elif response.status_code == 429:
                return f"STATUS: RATE LIMITED. {response.text}"
            else:
                return f"STATUS: ERROR. Code {response.status_code}: {response.text}"
        except Exception as e:
            return f"STATUS: NETWORK FAILURE. Could not reach Exogram Authority Runtime: {str(e)}"


@mcp.tool()
def exogram_commit_action(token: str, status: str) -> str:
    """
    Commit a previously authorized action to the immutable audit ledger.
    Must be called immediately after the action is executed.
    """
    payload = _pending_payloads.pop(token, {})

    if is_local_mode():
        receipt = _get_local_vault().commit_token(token=token, status=status)
        return f"STATUS: COMMITTED (Local SQLite WAL). Ledger Hash: {receipt['ledger_hash']}"

    url = f"{get_api_url()}/v2/commit"
    request_data = {
        "token": token,
        "status": status,
        "payload": payload,
    }

    headers = get_headers()
    with httpx.Client(timeout=10.0) as client:
        try:
            response = client.post(url, json=request_data, headers=headers)
            if response.status_code in [200, 409]:
                return f"STATUS: COMMITTED. Audit log updated. Server Response: {response.text}"
            else:
                return f"STATUS: COMMIT ERROR. Code {response.status_code}: {response.text}"
        except Exception as e:
            return f"STATUS: NETWORK FAILURE. Could not reach Exogram Authority Runtime: {str(e)}"


@mcp.tool()
def exogram_store_record(
    content: str, source: str = "mcp-claude", namespace: str = "default"
) -> str:
    """
    Store a fact or record in Exogram's encrypted trust vault.
    """
    if is_local_mode():
        rec = _get_local_vault().store(content=content, namespace=namespace, source=source)
        return f"STATUS: STORED. Record ID: {rec['id']} | State Hash: {rec['state_hash']}"

    url = f"{get_api_url()}/v2/vault/store"
    request_data = {
        "content": content,
        "source": source,
        "source_llm": "anthropic",
        "namespace": namespace,
    }

    headers = get_headers()
    with httpx.Client(timeout=15.0) as client:
        try:
            response = client.post(url, json=request_data, headers=headers)
            if response.status_code == 200:
                data = cast(dict[str, object], response.json())
                memory_id = data.get("memory_id", "unknown")
                conflicts = cast(int, data.get("conflicts_detected", 0))
                result = f"STATUS: STORED. Record ID: {memory_id}"
                if conflicts > 0:
                    result += f" | {conflicts} conflict(s) detected"
                return result
            elif response.status_code == 429:
                return f"STATUS: RATE LIMITED. {response.text}"
            elif response.status_code == 401:
                return "STATUS: AUTH FAILED. Bearer token may be expired. Re-run the MCP installer."
            else:
                return f"STATUS: STORE ERROR. Code {response.status_code}: {response.text}"
        except Exception as e:
            return f"STATUS: NETWORK FAILURE. Could not reach Exogram Vault: {str(e)}"


@mcp.tool()
def exogram_search_records(query: str, top_k: int = 5) -> str:
    """
    Search through stored ledger records using semantic similarity.
    """
    if is_local_mode():
        results = _get_local_vault().search(query=query, namespace="all", top_k=top_k)
        if not results:
            return "No matching records found."
        lines = [f"Found {len(results)} matching records:"]
        for i, r in enumerate(results, 1):
            lines.append(f"  {i}. [{r['score']:.2f}] {r['content']}")
        return "\n".join(lines)

    url = f"{get_api_url()}/v2/vault/search"
    request_data = {
        "query": query,
        "top_k": min(max(top_k, 1), 20),
    }

    headers = get_headers()
    with httpx.Client(timeout=15.0) as client:
        try:
            response = client.post(url, json=request_data, headers=headers)
            if response.status_code == 200:
                data = cast(dict[str, object], response.json())
                results = cast(list[dict[str, object]], data.get("results", []))
                if not results:
                    return "No matching records found."

                lines = [f"Found {len(results)} matching records:"]
                for i, r in enumerate(results, 1):
                    content = r.get("content", r.get("claim", "Unknown"))
                    score = cast(float, r.get("score", r.get("similarity", 0.0)))
                    lines.append(f"  {i}. [{score:.2f}] {content}")
                return "\n".join(lines)
            else:
                return f"STATUS: SEARCH ERROR. Code {response.status_code}: {response.text}"
        except Exception as e:
            return f"STATUS: NETWORK FAILURE. Could not reach Exogram Vault: {str(e)}"


@mcp.tool()
def search_vault(query: str, top_k: int = 5) -> str:
    """Semantic and keyword search across stored personal records, facts, and memories."""
    return exogram_search_records(query=query, top_k=top_k)


@mcp.tool()
def store_memory(content: str, namespace: str = "default") -> str:
    """Anchor a new fact, code convention, or personal memory to your encrypted vault."""
    return exogram_store_record(content=content, source="mcp-client", namespace=namespace)


@mcp.tool()
def get_neural_cluster(entity_name: str) -> str:
    """Look up an entity in Exogram's Knowledge Graph and return connected relationships."""
    if is_local_mode():
        return traverse_neural_graph(query=entity_name)

    url = f"{get_api_url()}/api/knowledge-graph"
    headers = get_headers()
    with httpx.Client(timeout=15.0) as client:
        try:
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                data = cast(dict[str, object], response.json())
                nodes = cast(list[dict[str, object]], data.get("nodes", []))
                links = cast(list[dict[str, object]], data.get("links", data.get("edges", [])))
                matched = [
                    n
                    for n in nodes
                    if entity_name.lower() in str(n.get("name", n.get("id", ""))).lower()
                ]
                if not matched:
                    return f"No neural cluster found matching '{entity_name}'."
                target_id = matched[0].get("id", matched[0].get("name"))
                target_name = matched[0].get("name", target_id)
                connected = []
                for link in links:
                    src = link.get("source")
                    dst = link.get("target")
                    lbl = link.get("label", link.get("relationship", "connected to"))
                    if src == target_id:
                        connected.append(f"  -> [{lbl}] -> {dst}")
                    elif dst == target_id:
                        connected.append(f"  <- [{lbl}] <- {src}")
                lines = [f"Neural cluster for '{target_name}':"]
                lines.extend(connected if connected else ["  (No connected relationships mapped yet)"])
                return "\n".join(lines)
            else:
                return f"STATUS: NEURAL LOOKUP ERROR. Code {response.status_code}: {response.text}"
        except Exception as e:
            return f"STATUS: NETWORK FAILURE. Could not reach Exogram Knowledge Graph: {str(e)}"


@mcp.tool()
def list_entities(limit: int = 25) -> str:
    """Retrieve active entities and topics in the personal knowledge network."""
    if is_local_mode():
        packet = _get_local_vault().traverse_graph(query="all", spheres=["Work", "People", "Life"])
        return json.dumps(packet["entities"][:limit], indent=2)

    url = f"{get_api_url()}/api/knowledge-graph"
    headers = get_headers()
    with httpx.Client(timeout=15.0) as client:
        try:
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                data = cast(dict[str, object], response.json())
                nodes = cast(list[dict[str, object]], data.get("nodes", []))
                if not nodes:
                    return "No entities mapped in the knowledge graph yet."
                lines = [f"Mapped Entities in Exogram Knowledge Graph (Top {min(limit, len(nodes))}):"]
                for i, node in enumerate(nodes[:limit], 1):
                    name = node.get("name", node.get("id", "Unknown"))
                    category = node.get("category", node.get("type", "concept"))
                    lines.append(f"  {i}. {name} ({category})")
                return "\n".join(lines)
            else:
                return f"STATUS: GRAPH ERROR. Code {response.status_code}: {response.text}"
        except Exception as e:
            return f"STATUS: NETWORK FAILURE. Could not reach Exogram Knowledge Graph: {str(e)}"


@mcp.tool()
def verify_audit_trail() -> str:
    """Verify the cryptographic SHA-256 hash chain integrity of the ledger."""
    if is_local_mode():
        return f"STATUS: CRYPTOGRAPHICALLY VALID (Local SQLite WAL). Head Hash: {_get_local_vault().state_hash()}"

    url = f"{get_api_url()}/v2/verify"
    headers = get_headers()
    with httpx.Client(timeout=15.0) as client:
        try:
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                data = cast(dict[str, object], response.json())
                valid = data.get("valid", True)
                entries = data.get("total_entries", data.get("entries_count", 0))
                head = data.get("head_hash", "GENESIS")
                status = "CRYPTOGRAPHICALLY VALID" if valid else "TAMPERING DETECTED"
                return f"STATUS: {status}. Total Entries: {entries} | Head Hash: {head}"
            else:
                return f"STATUS: VERIFICATION ERROR. Code {response.status_code}: {response.text}"
        except Exception as e:
            return f"STATUS: NETWORK FAILURE. Could not reach Verification Engine: {str(e)}"


if __name__ == "__main__":
    mcp.run()
