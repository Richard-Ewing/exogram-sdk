"""
Exogram Python Client SDK (v0.2.0).

Provides synchronous (Exogram / ExogramClient) and asynchronous (AsyncExogram / AsyncExogramClient)
clients with Zero-Signup Local SQLite WAL Mode (~/.exogram/vault.db) and Cloud Mode (https://api.exogram.ai).
"""

from __future__ import annotations

import functools
import json
import os
from typing import Any, Callable, Optional, TypeVar, cast

import httpx

from .local_vault import LocalSQLiteWalVault
from .models import (
    ActionJudgment,
    CommitResult,
    EvaluationResult,
    ExecutionReceipt,
    MemoryRecord,
    NeuralContextPacket,
    VaultRecord,
    VaultSearchResult,
    VaultStoreResult,
)

F = TypeVar("F", bound=Callable[..., Any])


class VaultSubClient:
    """Sub-client for Exogram Encrypted Trust Vault operations (client.vault)."""

    def __init__(self, parent: Exogram) -> None:
        self._parent = parent

    def store(
        self,
        content: str,
        namespace: str = "personal",
        sphere: str = "Life",
        confidence: float = 0.95,
        temporal_horizon: str = "durable_trait",
        source: str = "python-sdk",
    ) -> MemoryRecord:
        """
        Store a salient memory claim with 3-Horizon lifecycle & Instinct Pre-Mutation gating.
        """
        local_rec = self._parent._local_vault.store(
            content=content,
            namespace=namespace,
            sphere=sphere,
            confidence=confidence,
            temporal_horizon=temporal_horizon,
            source=source,
        )
        if not self._parent.local_mode:
            url = f"{self._parent.api_url}/v2/vault/store"
            payload = {
                "content": content,
                "namespace": namespace,
                "sphere": sphere,
                "confidence": confidence,
                "temporal_horizon": temporal_horizon,
                "source": source,
            }
            try:
                with httpx.Client(timeout=self._parent.timeout) as client:
                    resp = client.post(url, json=payload, headers=self._parent._get_headers())
                    if resp.status_code == 200:
                        data = cast(dict[str, Any], resp.json())
                        if data.get("memory_id"):
                            local_rec.id = str(data["memory_id"])
                        if data.get("state_hash"):
                            local_rec.state_hash = str(data["state_hash"])
            except Exception:
                pass
        return local_rec

    def search(
        self,
        query: str,
        namespace: Optional[str] = "personal",
        spheres: Optional[list[str]] = None,
        top_k: int = 5,
    ) -> list[MemoryRecord]:
        """
        Hybrid RRF semantic + lexical search across the Personal Memory Vault.
        """
        if not self._parent.local_mode:
            url = f"{self._parent.api_url}/v2/vault/search"
            payload: dict[str, Any] = {
                "query": query,
                "namespace": namespace or "personal",
                "top_k": min(max(top_k, 1), 20),
            }
            if spheres:
                payload["spheres"] = spheres
            try:
                with httpx.Client(timeout=self._parent.timeout) as client:
                    resp = client.post(url, json=payload, headers=self._parent._get_headers())
                    if resp.status_code == 200:
                        data = cast(dict[str, Any], resp.json())
                        raw_results = cast(list[dict[str, Any]], data.get("results", []))
                        if raw_results:
                            state_hash = self._parent._local_vault.get_current_state_hash()
                            return [
                                MemoryRecord(
                                    id=str(r.get("id") or r.get("memory_id") or f"mem_{i}"),
                                    content=str(r.get("content") or r.get("claim") or ""),
                                    namespace=str(r.get("namespace") or namespace or "personal"),
                                    sphere=str(r.get("sphere") or (spheres[0] if spheres else "Life")),
                                    score=float(r.get("score", r.get("similarity", 0.9))),
                                    confidence=float(r.get("confidence", 0.95)),
                                    state_hash=str(r.get("state_hash") or state_hash),
                                    temporal_horizon=str(r.get("temporal_horizon") or "durable_trait"),
                                )
                                for i, r in enumerate(raw_results)
                            ]
            except Exception:
                pass
        return self._parent._local_vault.search(
            query=query,
            namespace=namespace,
            spheres=spheres,
            top_k=top_k,
        )


class NeuralNetworkSubClient:
    """Sub-client for the Personal Neural Network (Work · People · Life) (client.neural_network)."""

    def __init__(self, parent: Exogram) -> None:
        self._parent = parent

    def retrieve(
        self,
        query: str,
        spheres: Optional[list[str]] = None,
        max_hops: int = 4,
    ) -> NeuralContextPacket:
        """
        Execute Infinite-Hop Spreading Activation + HippoRAG 2 Spectral PPR traversal.
        """
        return self._parent._local_vault.retrieve_neural_context(
            query=query,
            spheres=spheres,
            max_hops=max_hops,
        )

    def traverse(
        self,
        query: str,
        spheres: Optional[list[str]] = None,
        max_hops: int = 4,
    ) -> NeuralContextPacket:
        return self.retrieve(query=query, spheres=spheres, max_hops=max_hops)


class GovernanceSubClient:
    """Sub-client for deterministic 0.07ms state-hash & Instinct pre-mutation governance (client.governance)."""

    def __init__(self, parent: Exogram) -> None:
        self._parent = parent

    def evaluate_action(
        self,
        agent_id: str = "python-sdk-agent",
        action_type: str = "tool_call",
        parameters: Optional[dict[str, Any]] = None,
        state_hash: Optional[str] = None,
        namespace: str = "default",
    ) -> ActionJudgment:
        """
        Run deterministic 0.07ms state-hash verification + Instinct pre-mutation safety gate.
        """
        return self._parent._local_vault.evaluate_action(
            agent_id=agent_id,
            action_type=action_type,
            parameters=parameters,
            state_hash=state_hash,
            namespace=namespace,
        )


class ActionsSubClient:
    """Sub-client for cryptographic action execution & audit ledger commits (client.actions)."""

    def __init__(self, parent: Exogram) -> None:
        self._parent = parent

    def execute(
        self,
        execution_token: str,
        status: str = "success",
    ) -> ExecutionReceipt:
        """
        Verify single-use execution token and commit to the SHA-256 audit hash chain.
        """
        return self._parent._local_vault.execute_action(
            execution_token=execution_token,
            status=status,
        )


class Exogram:
    """
    Official Exogram Client (Synchronous).
    Supports both Zero-Signup Local SQLite WAL mode (~/.exogram/vault.db) and Cloud API mode.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        api_url: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
        local_mode: Optional[bool] = None,
        db_path: Optional[str] = None,
    ) -> None:
        resolved_token = (
            api_key
            or token
            or os.getenv("EXOGRAM_API_KEY")
            or os.getenv("EXOGRAM_BEARER_TOKEN")
        )
        if local_mode is True or not resolved_token or resolved_token.lower() == "local":
            self.local_mode: bool = True
            self.token: str = "local"
        else:
            self.local_mode = False
            self.token = resolved_token

        self.api_key: str = self.token
        self.api_url: str = (
            api_url
            or base_url
            or os.getenv("EXOGRAM_API_URL")
            or "https://api.exogram.ai"
        ).rstrip("/")
        self.timeout: float = timeout

        self._local_vault = LocalSQLiteWalVault(db_path=db_path)
        self.vault = VaultSubClient(self)
        self.neural_network = NeuralNetworkSubClient(self)
        self.governance = GovernanceSubClient(self)
        self.actions = ActionsSubClient(self)

    @property
    def db_path(self) -> str:
        return str(self._local_vault.db_path)

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "Exogram-Python-SDK/0.2.0",
        }

    def evaluate(
        self,
        action_type: str,
        namespace: str = "default",
        agent_id: str = "python-sdk-agent",
        payload: dict[str, Any] | str | None = None,
    ) -> EvaluationResult:
        """
        Request cryptographic authorization before executing an action.
        """
        parsed_payload: dict[str, Any]
        if isinstance(payload, str):
            try:
                loaded = json.loads(payload)
                parsed_payload = loaded if isinstance(loaded, dict) else {"raw": payload}
            except json.JSONDecodeError:
                parsed_payload = {"raw": payload}
        elif isinstance(payload, dict):
            parsed_payload = payload
        else:
            parsed_payload = {}

        if self.local_mode:
            judgment = self.governance.evaluate_action(
                agent_id=agent_id,
                action_type=action_type,
                parameters=parsed_payload,
                namespace=namespace,
            )
            return EvaluationResult(
                allowed=judgment.permitted,
                token=judgment.execution_token,
                status="ALLOWED" if judgment.permitted else "BLOCKED",
                policy_violation=None if judgment.permitted else judgment.reason,
                raw_response=judgment.model_dump(),
            )

        url = f"{self.api_url}/v2/evaluate"
        request_data = {
            "action_type": action_type,
            "namespace": namespace,
            "agent_id": agent_id,
            "payload": parsed_payload,
        }

        with httpx.Client(timeout=self.timeout) as client:
            try:
                response = client.post(url, json=request_data, headers=self._get_headers())
                if response.status_code == 200:
                    data = cast(dict[str, Any], response.json())
                    eval_token = cast(str | None, data.get("token"))
                    return EvaluationResult(
                        allowed=True,
                        token=eval_token,
                        status="ALLOWED",
                        raw_response=data,
                    )
                elif response.status_code == 403:
                    return EvaluationResult(
                        allowed=False,
                        status="BLOCKED",
                        policy_violation=response.text,
                    )
                else:
                    return EvaluationResult(
                        allowed=False,
                        status=f"ERROR_{response.status_code}",
                        policy_violation=response.text,
                    )
            except Exception as e:
                return EvaluationResult(
                    allowed=False,
                    status="NETWORK_FAILURE",
                    policy_violation=str(e),
                )

    def commit(
        self,
        token: str,
        status: str = "success",
        payload: dict[str, Any] | str | None = None,
    ) -> CommitResult:
        """
        Commit an authorized execution token to the immutable audit ledger.
        """
        if self.local_mode:
            receipt = self.actions.execute(execution_token=token, status=status)
            return CommitResult(
                committed=receipt.committed,
                status=receipt.status,
                response_text=f"Ledger Hash: {receipt.ledger_hash}",
                raw_response=receipt.model_dump(),
            )

        url = f"{self.api_url}/v2/commit"
        request_data = {
            "token": token,
            "status": status,
            "payload": payload or {},
        }

        with httpx.Client(timeout=self.timeout) as client:
            try:
                response = client.post(url, json=request_data, headers=self._get_headers())
                committed = response.status_code in [200, 409]
                status_str = "COMMITTED" if committed else f"ERROR_{response.status_code}"
                return CommitResult(
                    committed=committed,
                    status=status_str,
                    response_text=response.text,
                )
            except Exception as e:
                return CommitResult(
                    committed=False,
                    status="NETWORK_FAILURE",
                    response_text=str(e),
                )

    def store_record(
        self,
        content: str,
        source: str = "python-sdk",
        namespace: str = "default",
    ) -> VaultStoreResult:
        """
        Store a fact or record in Exogram's encrypted trust vault.
        """
        if self.local_mode:
            rec = self._local_vault.store(
                content=content,
                namespace=namespace,
                source=source,
            )
            return VaultStoreResult(
                stored=True,
                memory_id=rec.id,
                conflicts_detected=rec.conflicts_superseded,
                status="STORED",
                raw_response=rec.model_dump(),
            )

        url = f"{self.api_url}/v2/vault/store"
        request_data = {
            "content": content,
            "source": source,
            "source_llm": "python-sdk",
            "namespace": namespace,
        }

        with httpx.Client(timeout=self.timeout) as client:
            try:
                response = client.post(url, json=request_data, headers=self._get_headers())
                if response.status_code == 200:
                    data = cast(dict[str, Any], response.json())
                    return VaultStoreResult(
                        stored=True,
                        memory_id=cast(str | None, data.get("memory_id")),
                        conflicts_detected=cast(int, data.get("conflicts_detected", 0)),
                        status="STORED",
                        raw_response=data,
                    )
                else:
                    return VaultStoreResult(
                        stored=False,
                        status=f"ERROR_{response.status_code}",
                    )
            except Exception as e:
                return VaultStoreResult(
                    stored=False,
                    status=f"NETWORK_FAILURE: {str(e)}",
                )

    def store(
        self,
        content: str,
        source: str = "python-sdk",
        namespace: str = "default",
    ) -> VaultStoreResult:
        """Alias for store_record for backwards compatibility."""
        return self.store_record(content=content, source=source, namespace=namespace)

    def search_records(self, query: str, top_k: int = 5) -> VaultSearchResult:
        """
        Search stored vault records using semantic similarity.
        """
        if self.local_mode:
            matches = self._local_vault.search(query=query, namespace="all", top_k=top_k)
            records = [
                VaultRecord(
                    content=m.content,
                    score=m.score,
                    memory_id=m.id,
                    source="local-sqlite-wal",
                    metadata=m.model_dump(),
                )
                for m in matches
            ]
            return VaultSearchResult(
                results=records,
                total_found=len(records),
                raw_response={"mode": "local_sqlite_wal", "count": len(records)},
            )

        url = f"{self.api_url}/v2/vault/search"
        request_data = {
            "query": query,
            "top_k": min(max(top_k, 1), 20),
        }

        with httpx.Client(timeout=self.timeout) as client:
            try:
                response = client.post(url, json=request_data, headers=self._get_headers())
                if response.status_code == 200:
                    data = cast(dict[str, Any], response.json())
                    raw_results = cast(list[dict[str, Any]], data.get("results", []))
                    records = [
                        VaultRecord(
                            content=r.get("content", r.get("claim", "Unknown")),
                            score=float(r.get("score", r.get("similarity", 0.0))),
                            memory_id=r.get("memory_id"),
                            source=r.get("source"),
                            metadata=r,
                        )
                        for r in raw_results
                    ]
                    return VaultSearchResult(
                        results=records,
                        total_found=len(records),
                        raw_response=data,
                    )
                else:
                    return VaultSearchResult(results=[], total_found=0)
            except Exception:
                return VaultSearchResult(results=[], total_found=0)

    def search(self, query: str, top_k: int = 5) -> VaultSearchResult:
        """Alias for search_records for backwards compatibility."""
        return self.search_records(query=query, top_k=top_k)

    def governed(self, action_type: str, namespace: str = "default") -> Callable[[F], F]:
        """
        Decorator that wraps a Python function with Exogram evaluate & commit logic.
        """

        def decorator(func: F) -> F:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                payload = {
                    "args": [str(a) for a in args],
                    "kwargs": {k: str(v) for k, v in kwargs.items()},
                }
                eval_res = self.evaluate(action_type=action_type, namespace=namespace, payload=payload)

                if not eval_res.allowed:
                    raise PermissionError(
                        f"Exogram Governance Blocked Action: {eval_res.policy_violation}"
                    )

                try:
                    result = func(*args, **kwargs)
                    if eval_res.token:
                        self.commit(token=eval_res.token, status="success", payload=payload)
                    return result
                except Exception as e:
                    if eval_res.token:
                        self.commit(token=eval_res.token, status="failure", payload=payload)
                    raise e

            return cast(F, wrapper)

        return decorator


class AsyncExogram:
    """
    Asynchronous Exogram Client (v0.2.0).
    Supports Zero-Signup Local SQLite WAL mode and Cloud API mode.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        api_url: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
        local_mode: Optional[bool] = None,
        db_path: Optional[str] = None,
    ) -> None:
        resolved_token = (
            api_key
            or token
            or os.getenv("EXOGRAM_API_KEY")
            or os.getenv("EXOGRAM_BEARER_TOKEN")
        )
        if local_mode is True or not resolved_token or resolved_token.lower() == "local":
            self.local_mode: bool = True
            self.token: str = "local"
        else:
            self.local_mode = False
            self.token = resolved_token

        self.api_key: str = self.token
        self.api_url: str = (
            api_url
            or base_url
            or os.getenv("EXOGRAM_API_URL")
            or "https://api.exogram.ai"
        ).rstrip("/")
        self.timeout: float = timeout

        self._sync_bridge = Exogram(
            api_key=self.api_key,
            api_url=self.api_url,
            timeout=self.timeout,
            local_mode=self.local_mode,
            db_path=db_path,
        )
        self.vault = self._sync_bridge.vault
        self.neural_network = self._sync_bridge.neural_network
        self.governance = self._sync_bridge.governance
        self.actions = self._sync_bridge.actions

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "Exogram-Async-Python-SDK/0.2.0",
        }

    async def evaluate(
        self,
        action_type: str,
        namespace: str = "default",
        agent_id: str = "python-sdk-agent",
        payload: dict[str, Any] | str | None = None,
    ) -> EvaluationResult:
        if self.local_mode:
            return self._sync_bridge.evaluate(
                action_type=action_type,
                namespace=namespace,
                agent_id=agent_id,
                payload=payload,
            )

        url = f"{self.api_url}/v2/evaluate"
        request_data = {
            "action_type": action_type,
            "namespace": namespace,
            "agent_id": agent_id,
            "payload": payload or {},
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=request_data, headers=self._get_headers())
                if response.status_code == 200:
                    data = cast(dict[str, Any], response.json())
                    return EvaluationResult(
                        allowed=True,
                        token=cast(str | None, data.get("token")),
                        status="ALLOWED",
                        raw_response=data,
                    )
                elif response.status_code == 403:
                    return EvaluationResult(
                        allowed=False,
                        status="BLOCKED",
                        policy_violation=response.text,
                    )
                else:
                    return EvaluationResult(
                        allowed=False,
                        status=f"ERROR_{response.status_code}",
                        policy_violation=response.text,
                    )
            except Exception as e:
                return EvaluationResult(
                    allowed=False,
                    status="NETWORK_FAILURE",
                    policy_violation=str(e),
                )


ExogramClient = Exogram
AsyncExogramClient = AsyncExogram
