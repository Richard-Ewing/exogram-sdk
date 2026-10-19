"""
Typed Pydantic Models for Exogram Python SDK responses (v0.2.0).
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


class MemoryRecord(BaseModel):
    """A verified memory claim stored in the Exogram Vault (Local SQLite WAL or Cloud)."""

    id: str = Field(..., description="Unique memory record identifier (e.g. mem_...)")
    content: str = Field(..., description="The discrete factual claim or record content")
    namespace: str = Field(default="personal", description="Logical namespace grouping")
    sphere: str = Field(default="Life", description="Personal Neural Network sphere (Work, People, Life)")
    score: float = Field(default=1.0, description="Relevance or hybrid RRF score (0.0 - 1.0)")
    confidence: float = Field(default=0.95, description="Epistemic confidence score (0.0 - 1.0)")
    state_hash: str = Field(..., description="Cryptographic SHA-256 vault state hash after mutation")
    temporal_horizon: str = Field(
        default="durable_trait",
        description="Episodic lifecycle horizon (ephemeral_episode, recurring_event, durable_trait)",
    )
    conflicts_superseded: int = Field(default=0, description="Number of conflicting scalar claims superseded")
    created_at: Optional[float] = Field(default=None, description="Unix timestamp of creation")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional provenance metadata")

    @property
    def memory_id(self) -> str:
        return self.id

    @property
    def claim(self) -> str:
        return self.content


class NeuralContextPacket(BaseModel):
    """Multi-hop associative context packet returned by the Personal Neural Network."""

    query: str = Field(..., description="Original retrieval query")
    spheres: list[str] = Field(
        default_factory=lambda: ["Work", "People", "Life"],
        description="Queried cognitive spheres",
    )
    claims: list[MemoryRecord] = Field(
        default_factory=list,
        description="Grounded claims retrieved via infinite-hop spreading activation + HippoRAG 2 PPR",
    )
    entities: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Activated graph entities with hop distances and PPR scores",
    )
    state_hash: str = Field(..., description="Cryptographic SHA-256 state hash of the current vault")
    ppr_converged: bool = Field(default=True, description="Whether Personalized PageRank spectral propagation converged")
    hops_traversed: int = Field(default=1, description="Maximum associative hops traversed during activation")

    @property
    def memories(self) -> list[MemoryRecord]:
        return self.claims


class ActionJudgment(BaseModel):
    """Deterministic pre-execution action judgment from the Exogram Governance & Instinct Gate."""

    permitted: bool = Field(..., description="Whether the action is permitted under current policy and state hash")
    execution_token: Optional[str] = Field(
        default=None, description="Cryptographic single-use execution token if permitted"
    )
    state_hash: str = Field(..., description="Verified SHA-256 vault state hash bound to this judgment")
    latency_ms: float = Field(default=0.07, description="Deterministic gate evaluation latency in milliseconds")
    reason: str = Field(default="PERMITTED_STATE_HASH_VERIFIED", description="Policy decision rationale")

    @property
    def allowed(self) -> bool:
        return self.permitted

    @property
    def token(self) -> Optional[str]:
        return self.execution_token


class ExecutionReceipt(BaseModel):
    """Immutable audit ledger receipt produced when committing an execution token."""

    committed: bool = Field(..., description="Whether the action execution was committed to the hash chain")
    execution_token: str = Field(..., description="The consumed execution token")
    ledger_hash: str = Field(..., description="Cryptographic SHA-256 hash chain head after commit")
    status: str = Field(default="COMMITTED", description="Ledger commit status")


class EvaluationResult(BaseModel):
    allowed: bool = Field(..., description="Whether the action is allowed by policy constraints")
    token: Optional[str] = Field(default=None, description="Cryptographic execution token issued if allowed")
    status: str = Field(..., description="Status string (ALLOWED, BLOCKED, RATE_LIMITED, etc.)")
    policy_violation: Optional[str] = Field(default=None, description="Policy violation details if blocked")
    raw_response: dict[str, Any] = Field(default_factory=dict, description="Raw API response data")


class CommitResult(BaseModel):
    committed: bool = Field(..., description="Whether the execution was committed to the ledger")
    status: str = Field(..., description="Status string (COMMITTED, ERROR, etc.)")
    response_text: str = Field(default="", description="Server response text")
    raw_response: dict[str, Any] = Field(default_factory=dict, description="Raw API response data")


class VaultStoreResult(BaseModel):
    stored: bool = Field(..., description="Whether the record was stored in the trust vault")
    memory_id: Optional[str] = Field(default=None, description="Persisted record ID")
    conflicts_detected: int = Field(default=0, description="Number of conflicts detected with existing ledger facts")
    status: str = Field(..., description="Status string")
    raw_response: dict[str, Any] = Field(default_factory=dict, description="Raw API response data")


class VaultRecord(BaseModel):
    content: str = Field(..., description="The record or claim content")
    score: float = Field(default=0.0, description="Similarity score (0.0 - 1.0)")
    memory_id: Optional[str] = Field(default=None, description="Memory ID")
    source: Optional[str] = Field(default=None, description="Source provenance")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class VaultSearchResult(BaseModel):
    results: list[VaultRecord] = Field(default_factory=list, description="Matching vault records")
    total_found: int = Field(default=0, description="Total matching records count")
    raw_response: dict[str, Any] = Field(default_factory=dict, description="Raw API response data")
