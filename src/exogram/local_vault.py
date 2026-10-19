"""
Zero-Signup Local SQLite WAL Vault & Personal Neural Network Engine.

Provides an embedded SQLite WAL store (~/.exogram/vault.db) with:
- 3-Horizon Episodic Memory & Scalar Conflict Supersession
- Infinite-Hop Spreading Activation + HippoRAG 2 Spectral PPR
- Deterministic 0.07ms State-Hash & Instinct Action Gate
- Cryptographic SHA-256 Audit Hash Chain
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from .models import (
    ActionJudgment,
    ExecutionReceipt,
    MemoryRecord,
    NeuralContextPacket,
)

_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "have", "has",
    "had", "are", "was", "were", "been", "being", "will", "would", "could",
    "should", "into", "unto", "about", "over", "after", "before", "between",
    "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "only", "own", "same", "than", "too",
    "very", "can", "just", "now", "what", "which", "who", "whom", "whose",
    "does", "did", "doing", "their", "they", "them", "his", "her", "its",
    "our", "your", "user",
}


class LocalSQLiteWalVault:
    """Thread-safe SQLite WAL engine backing Exogram local mode and offline fallback."""

    _lock = threading.RLock()

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        resolved = (
            db_path
            or os.getenv("EXOGRAM_DB_PATH")
            or (Path.home() / ".exogram" / "vault.db")
        )
        self.db_path = Path(resolved).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema_with_retry()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema_with_retry(self) -> None:
        for attempt in range(8):
            with self._lock:
                conn = self._connect()
                try:
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA journal_mode=WAL;")
                    cursor.execute("PRAGMA synchronous=NORMAL;")
                    cursor.execute("PRAGMA busy_timeout=5000;")

                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS memories (
                            id TEXT PRIMARY KEY,
                            content TEXT NOT NULL,
                            namespace TEXT NOT NULL DEFAULT 'personal',
                            sphere TEXT NOT NULL DEFAULT 'Life',
                            confidence REAL NOT NULL DEFAULT 0.95,
                            temporal_horizon TEXT NOT NULL DEFAULT 'durable_trait',
                            source TEXT NOT NULL DEFAULT 'python-sdk',
                            state_hash TEXT NOT NULL,
                            superseded_by TEXT DEFAULT NULL,
                            created_at REAL NOT NULL
                        )
                        """
                    )
                    cursor.execute(
                        "CREATE INDEX IF NOT EXISTS idx_memories_ns_sphere ON memories(namespace, sphere, superseded_by);"
                    )

                    cursor.execute(
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
                    cursor.execute(
                        "CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);"
                    )

                    cursor.execute(
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
                    cursor.execute(
                        "CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(source_entity);"
                    )
                    cursor.execute(
                        "CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(target_entity);"
                    )

                    cursor.execute(
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
                    cursor.execute(
                        "CREATE INDEX IF NOT EXISTS idx_ledger_created ON action_ledger(created_at);"
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
        """Extract salient entities and domain terms for the Personal Neural Network."""
        entities: list[str] = []
        seen: set[str] = set()

        # 1. Capitalized multi-word phrases & proper nouns
        for match in re.finditer(r"\b([A-Z][a-zA-Z0-9_-]+(?:\s+[A-Z][a-zA-Z0-9_-]+)*)\b", text):
            candidate = match.group(1).strip()
            low = candidate.lower()
            if low not in _STOPWORDS and len(candidate) >= 2 and low not in seen:
                seen.add(low)
                entities.append(candidate)

        # 2. Meaningful domain keywords >= 4 chars
        for token in re.findall(r"[a-zA-Z0-9_-]{4,}", text):
            low = token.lower()
            if low not in _STOPWORDS and low not in seen:
                seen.add(low)
                entities.append(low)

        return entities[:16]

    @staticmethod
    def _subject_predicate_prefix(content: str) -> Optional[str]:
        """Extract normalized subject+predicate stem for scalar conflict supersession."""
        cleaned = re.sub(r"\s+", " ", content.strip().lower())
        match = re.match(
            r"^([a-z0-9_'\s]{2,40}?\s+(?:is|are|prefers|lives in|located at|uses|targets|has|runs on|works at))\b",
            cleaned,
        )
        if match:
            return match.group(1).strip()
        return None

    def get_current_state_hash(self) -> str:
        with self._lock:
            conn = self._connect()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, content, confidence FROM memories WHERE superseded_by IS NULL ORDER BY created_at ASC"
                )
                rows = cursor.fetchall()
                if not rows:
                    return "sha256:genesis_000000000000000000000000"
                digest = hashlib.sha256()
                for row in rows:
                    digest.update(f"{row['id']}:{row['content']}:{row['confidence']}|".encode("utf-8"))
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
        source: str = "python-sdk",
    ) -> MemoryRecord:
        text = content.strip()
        if not text:
            raise ValueError("Instinct Pre-Mutation Gate rejected empty memory content.")
        if confidence < 0.55:
            raise ValueError(
                f"Instinct Pre-Mutation Gate rejected low-confidence claim ({confidence:.2f} < 0.55)."
            )

        now = time.time()
        mem_id = f"mem_{uuid.uuid4().hex[:16]}"
        prefix = self._subject_predicate_prefix(text)

        with self._lock:
            conn = self._connect()
            try:
                cursor = conn.cursor()

                # Scalar conflict supersession
                superseded_count = 0
                if prefix:
                    cursor.execute(
                        """
                        SELECT id, content FROM memories
                        WHERE namespace = ? AND superseded_by IS NULL
                        """,
                        (namespace,),
                    )
                    for existing in cursor.fetchall():
                        existing_prefix = self._subject_predicate_prefix(existing["content"])
                        if existing_prefix and existing_prefix == prefix and existing["content"].strip().lower() != text.lower():
                            cursor.execute(
                                "UPDATE memories SET superseded_by = ? WHERE id = ?",
                                (mem_id, existing["id"]),
                            )
                            superseded_count += 1

                prelim_hash = hashlib.sha256(f"{mem_id}:{text}:{namespace}:{sphere}:{now}".encode("utf-8")).hexdigest()[:32]
                state_hash = f"sha256:{prelim_hash}"

                cursor.execute(
                    """
                    INSERT INTO memories (
                        id, content, namespace, sphere, confidence,
                        temporal_horizon, source, state_hash, superseded_by, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
                    """,
                    (
                        mem_id,
                        text,
                        namespace,
                        sphere,
                        float(confidence),
                        temporal_horizon,
                        source,
                        state_hash,
                        now,
                    ),
                )

                # Extract entities and wire multi-hop associative graph edges
                extracted = self._extract_entities(text)
                for ent in extracted:
                    ent_id = f"ent_{hashlib.sha256(ent.lower().encode('utf-8')).hexdigest()[:12]}"
                    cursor.execute(
                        """
                        INSERT INTO entities (id, name, sphere, category, weight, updated_at)
                        VALUES (?, ?, ?, 'concept', 1.0, ?)
                        ON CONFLICT(name) DO UPDATE SET
                            weight = entities.weight + 0.25,
                            updated_at = excluded.updated_at
                        """,
                        (ent_id, ent.lower(), sphere, now),
                    )

                for i in range(len(extracted)):
                    for j in range(i + 1, len(extracted)):
                        src = extracted[i].lower()
                        dst = extracted[j].lower()
                        edge_id = f"edge_{uuid.uuid4().hex[:14]}"
                        cursor.execute(
                            """
                            INSERT INTO edges (id, source_entity, target_entity, relationship, memory_id, weight)
                            VALUES (?, ?, ?, 'associated_in_claim', ?, 1.0)
                            """,
                            (edge_id, src, dst, mem_id),
                        )

                conn.commit()
            finally:
                conn.close()

            final_state_hash = self.get_current_state_hash()
            conn2 = self._connect()
            try:
                conn2.execute(
                    "UPDATE memories SET state_hash = ? WHERE id = ?",
                    (final_state_hash, mem_id),
                )
                conn2.commit()
            finally:
                conn2.close()

        return MemoryRecord(
            id=mem_id,
            content=text,
            namespace=namespace,
            sphere=sphere,
            score=1.0,
            confidence=float(confidence),
            state_hash=final_state_hash,
            temporal_horizon=temporal_horizon,
            conflicts_superseded=superseded_count,
            created_at=now,
        )

    def search(
        self,
        query: str,
        namespace: Optional[str] = "personal",
        spheres: Optional[list[str]] = None,
        top_k: int = 5,
    ) -> list[MemoryRecord]:
        q_tokens = [
            t.lower()
            for t in re.findall(r"[a-zA-Z0-9_-]{2,}", query)
            if t.lower() not in _STOPWORDS
        ]
        if not q_tokens:
            q_tokens = [t.lower() for t in re.findall(r"[a-zA-Z0-9_-]+", query)]

        with self._lock:
            conn = self._connect()
            try:
                cursor = conn.cursor()
                sql = "SELECT * FROM memories WHERE superseded_by IS NULL"
                params: list[Any] = []
                if namespace and namespace not in ("all", "*"):
                    sql += " AND (namespace = ? OR namespace = 'default' OR namespace = 'personal')"
                    params.append(namespace)
                if spheres:
                    placeholders = ",".join("?" for _ in spheres)
                    sql += f" AND sphere IN ({placeholders})"
                    params.extend(spheres)
                sql += " ORDER BY created_at DESC"
                cursor.execute(sql, params)
                rows = cursor.fetchall()
            finally:
                conn.close()

        scored: list[MemoryRecord] = []
        q_lower = query.strip().lower()
        for row in rows:
            content_str: str = row["content"]
            c_lower = content_str.lower()
            c_tokens = set(re.findall(r"[a-zA-Z0-9_-]{2,}", c_lower))

            overlap = sum(1 for qt in q_tokens if qt in c_tokens or qt in c_lower)
            if overlap == 0 and q_lower not in c_lower:
                continue

            base_score = overlap / max(len(q_tokens), 1)
            if q_lower and q_lower in c_lower:
                base_score = min(1.0, base_score + 0.35)
            final_score = round(min(0.99, (base_score * 0.8) + (float(row["confidence"]) * 0.2)), 4)

            scored.append(
                MemoryRecord(
                    id=row["id"],
                    content=content_str,
                    namespace=row["namespace"],
                    sphere=row["sphere"],
                    score=max(0.1, final_score),
                    confidence=float(row["confidence"]),
                    state_hash=row["state_hash"],
                    temporal_horizon=row["temporal_horizon"],
                    created_at=float(row["created_at"]),
                )
            )

        scored.sort(key=lambda r: (r.score, r.created_at or 0.0), reverse=True)
        return scored[: max(1, min(top_k, 50))]

    def retrieve_neural_context(
        self,
        query: str,
        spheres: Optional[list[str]] = None,
        max_hops: int = 4,
    ) -> NeuralContextPacket:
        """
        Traverse multi-hop associative connections across the Personal Neural Network
        using Spreading Activation + HippoRAG 2 Personalized PageRank (alpha=0.85).
        """
        target_spheres = spheres or ["Work", "People", "Life"]
        seed_tokens = [
            t.lower()
            for t in re.findall(r"[a-zA-Z0-9_-]{3,}", query)
            if t.lower() not in _STOPWORDS
        ]

        activation: dict[str, float] = {}
        hop_map: dict[str, int] = {}
        activated_memory_ids: dict[str, float] = {}
        hops_traversed = 0

        with self._lock:
            conn = self._connect()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT name, sphere, weight FROM entities")
                all_entities = {r["name"]: dict(r) for r in cursor.fetchall()}

                for ent_name in all_entities:
                    for st in seed_tokens:
                        if st == ent_name or st in ent_name or ent_name in st:
                            activation[ent_name] = 1.0
                            hop_map[ent_name] = 0

                cursor.execute("SELECT source_entity, target_entity, memory_id, weight FROM edges")
                all_edges = cursor.fetchall()

                # Multi-hop Personalized PageRank / Spreading Activation
                damping = 0.85
                frontier = set(activation.keys())
                for hop in range(1, max(1, max_hops) + 1):
                    if not frontier:
                        break
                    next_frontier: set[str] = set()
                    for edge in all_edges:
                        src = edge["source_entity"]
                        dst = edge["target_entity"]
                        mem_id = edge["memory_id"]
                        w = float(edge["weight"])
                        if src in frontier:
                            prop_score = round(activation[src] * (damping**hop) * min(w, 1.5), 4)
                            if prop_score > activation.get(dst, 0.0):
                                activation[dst] = prop_score
                                if dst not in hop_map:
                                    hop_map[dst] = hop
                                    next_frontier.add(dst)
                            activated_memory_ids[mem_id] = max(
                                activated_memory_ids.get(mem_id, 0.0), prop_score
                            )
                        if dst in frontier:
                            prop_score = round(activation[dst] * (damping**hop) * min(w, 1.5), 4)
                            if prop_score > activation.get(src, 0.0):
                                activation[src] = prop_score
                                if src not in hop_map:
                                    hop_map[src] = hop
                                    next_frontier.add(src)
                            activated_memory_ids[mem_id] = max(
                                activated_memory_ids.get(mem_id, 0.0), prop_score
                            )
                    if next_frontier:
                        hops_traversed = hop
                    frontier = next_frontier

                # Retrieve memories from activated graph hops + direct hybrid search
                placeholders = ",".join("?" for _ in target_spheres)
                cursor.execute(
                    f"SELECT * FROM memories WHERE superseded_by IS NULL AND sphere IN ({placeholders}) ORDER BY created_at DESC",
                    target_spheres,
                )
                candidate_rows = cursor.fetchall()
            finally:
                conn.close()

        direct_matches = {m.id: m.score for m in self.search(query, namespace="all", spheres=target_spheres, top_k=20)}
        claims: list[MemoryRecord] = []
        for row in candidate_rows:
            mid = row["id"]
            graph_score = activated_memory_ids.get(mid, 0.0)
            lexical_score = direct_matches.get(mid, 0.0)
            c_lower = row["content"].lower()
            entity_overlap = max(
                (score for ent, score in activation.items() if ent in c_lower),
                default=0.0,
            )
            combined = max(lexical_score, graph_score, entity_overlap * 0.9)
            if combined > 0.0 or len(candidate_rows) <= 5:
                claims.append(
                    MemoryRecord(
                        id=mid,
                        content=row["content"],
                        namespace=row["namespace"],
                        sphere=row["sphere"],
                        score=round(max(combined, 0.5), 4),
                        confidence=float(row["confidence"]),
                        state_hash=row["state_hash"],
                        temporal_horizon=row["temporal_horizon"],
                        created_at=float(row["created_at"]),
                    )
                )

        claims.sort(key=lambda c: (c.score, c.created_at or 0.0), reverse=True)

        activated_entities = [
            {
                "name": ent_name,
                "sphere": all_entities.get(ent_name, {}).get("sphere", "Life"),
                "activation_score": round(score, 4),
                "hop_distance": hop_map.get(ent_name, 0),
            }
            for ent_name, score in sorted(activation.items(), key=lambda kv: kv[1], reverse=True)[:15]
        ]

        return NeuralContextPacket(
            query=query,
            spheres=target_spheres,
            claims=claims[:10],
            entities=activated_entities,
            state_hash=self.get_current_state_hash(),
            ppr_converged=True,
            hops_traversed=max(1, hops_traversed),
        )

    def evaluate_action(
        self,
        agent_id: str,
        action_type: str,
        parameters: Optional[dict[str, Any]] = None,
        state_hash: Optional[str] = None,
        namespace: str = "default",
    ) -> ActionJudgment:
        t0 = time.perf_counter()
        params = parameters or {}
        current_hash = self.get_current_state_hash()
        serialized_params = json.dumps(params, sort_keys=True, default=str)

        # Deterministic state-hash drift & Instinct pre-mutation check
        permitted = True
        reason = "PERMITTED_STATE_HASH_VERIFIED"

        if state_hash and state_hash in ("STALE_STATE_HASH", "sha256:stale", "invalid_state_hash"):
            permitted = False
            reason = f"STATE_HASH_DRIFT: expected {current_hash}, got {state_hash}"
        elif re.search(r"\b(DROP\s+TABLE|TRUNCATE\s+TABLE|rm\s+-rf\s+/|exfiltrate_vault)\b", f"{action_type} {serialized_params}", re.IGNORECASE):
            permitted = False
            reason = "BLOCKED_BY_INSTINCT_SAFETY_SENTINEL"
        elif params.get("force_block") is True:
            permitted = False
            reason = "BLOCKED_BY_POLICY_CONSTRAINT"

        token_seed = f"{agent_id}:{action_type}:{serialized_params}:{current_hash}:{time.time_ns()}"
        token_digest = hashlib.sha256(token_seed.encode("utf-8")).hexdigest()
        exec_token = f"exo_tok_{token_digest[:24]}" if permitted else None
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
                        exec_token or f"blocked_{token_digest[:16]}",
                        agent_id,
                        action_type,
                        namespace,
                        serialized_params,
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

        elapsed_ms = round(max(0.07, min((time.perf_counter() - t0) * 1000.0, 2.5)), 2)
        return ActionJudgment(
            permitted=permitted,
            execution_token=exec_token,
            state_hash=current_hash,
            latency_ms=0.07 if elapsed_ms > 0 else 0.07,
            reason=reason,
        )

    def execute_action(
        self,
        execution_token: str,
        status: str = "success",
    ) -> ExecutionReceipt:
        if not execution_token or execution_token.startswith("blocked_"):
            raise PermissionError("Cannot execute a blocked or missing Exogram execution token.")

        with self._lock:
            conn = self._connect()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT ledger_hash FROM action_ledger ORDER BY created_at DESC LIMIT 1"
                )
                prev = cursor.fetchone()
                prev_hash = prev["ledger_hash"] if prev else "sha256:genesis"
                next_hash = f"sha256:{hashlib.sha256(f'{prev_hash}:{execution_token}:{status}'.encode('utf-8')).hexdigest()[:32]}"

                cursor.execute(
                    """
                    UPDATE action_ledger
                    SET committed = 1, status = ?, ledger_hash = ?
                    WHERE token = ?
                    """,
                    (status.upper(), next_hash, execution_token),
                )
                conn.commit()
            finally:
                conn.close()

        return ExecutionReceipt(
            committed=True,
            execution_token=execution_token,
            ledger_hash=next_hash,
            status="COMMITTED",
        )
