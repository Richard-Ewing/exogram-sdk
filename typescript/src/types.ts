/**
 * Typed interfaces for Exogram TypeScript SDK (v0.2.0).
 */

export interface ExogramClientConfig {
    apiKey?: string;
    token?: string;
    baseUrl?: string;
    apiUrl?: string;
    timeoutMs?: number;
    localMode?: boolean;
}

export interface MemoryRecord {
    id: string;
    content: string;
    namespace: string;
    sphere: string;
    score: number;
    confidence: number;
    stateHash: string;
    state_hash?: string;
    temporalHorizon: string;
    conflictsSuperseded?: number;
    createdAt?: number;
    metadata?: Record<string, unknown>;
}

export interface NeuralEntityNode {
    name: string;
    sphere: string;
    activationScore: number;
    hopDistance: number;
}

export interface NeuralContextPacket {
    query: string;
    spheres: string[];
    claims: MemoryRecord[];
    entities: NeuralEntityNode[];
    stateHash: string;
    state_hash?: string;
    pprConverged: boolean;
    ppr_converged?: boolean;
    hopsTraversed: number;
}

export interface ActionJudgment {
    permitted: boolean;
    allowed: boolean;
    executionToken?: string;
    execution_token?: string;
    stateHash: string;
    state_hash?: string;
    latencyMs: number;
    latency_ms?: number;
    reason: string;
}

export interface ExecutionReceipt {
    committed: boolean;
    executionToken: string;
    execution_token?: string;
    ledgerHash: string;
    ledger_hash?: string;
    status: string;
}

export interface EvaluationResult {
    allowed: boolean;
    token?: string;
    status: string;
    policyViolation?: string;
    rawResponse?: Record<string, unknown>;
}

export interface CommitResult {
    committed: boolean;
    status: string;
    responseText: string;
    rawResponse?: Record<string, unknown>;
}

export interface VaultStoreResult {
    stored: boolean;
    memoryId?: string;
    conflictsDetected: number;
    status: string;
    rawResponse?: Record<string, unknown>;
}

export interface VaultRecord {
    content: string;
    score: number;
    memoryId?: string;
    source?: string;
    metadata?: Record<string, unknown>;
}

export interface VaultSearchResult {
    results: VaultRecord[];
    totalFound: number;
    rawResponse?: Record<string, unknown>;
}
