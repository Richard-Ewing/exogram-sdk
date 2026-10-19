/**
 * Typed interfaces for Exogram TypeScript SDK (v0.2.0).
 */
interface ExogramClientConfig {
    apiKey?: string;
    token?: string;
    baseUrl?: string;
    apiUrl?: string;
    timeoutMs?: number;
    localMode?: boolean;
}
interface MemoryRecord {
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
interface NeuralEntityNode {
    name: string;
    sphere: string;
    activationScore: number;
    hopDistance: number;
}
interface NeuralContextPacket {
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
interface ActionJudgment {
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
interface ExecutionReceipt {
    committed: boolean;
    executionToken: string;
    execution_token?: string;
    ledgerHash: string;
    ledger_hash?: string;
    status: string;
}
interface EvaluationResult {
    allowed: boolean;
    token?: string;
    status: string;
    policyViolation?: string;
    rawResponse?: Record<string, unknown>;
}
interface CommitResult {
    committed: boolean;
    status: string;
    responseText: string;
    rawResponse?: Record<string, unknown>;
}
interface VaultStoreResult {
    stored: boolean;
    memoryId?: string;
    conflictsDetected: number;
    status: string;
    rawResponse?: Record<string, unknown>;
}
interface VaultRecord {
    content: string;
    score: number;
    memoryId?: string;
    source?: string;
    metadata?: Record<string, unknown>;
}
interface VaultSearchResult {
    results: VaultRecord[];
    totalFound: number;
    rawResponse?: Record<string, unknown>;
}

/**
 * Official TypeScript & Node.js SDK for Exogram (v0.2.0).
 * Supports Zero-Signup Local Mode and Cloud Authority Runtime Mode.
 */

declare class Exogram {
    readonly localMode: boolean;
    private token;
    private apiUrl;
    private timeoutMs;
    private localMemories;
    private localEdges;
    private lastLedgerHash;
    readonly vault: {
        store: (content: string, options?: {
            namespace?: string;
            sphere?: string;
            confidence?: number;
            temporalHorizon?: string;
            source?: string;
        }) => Promise<MemoryRecord>;
        search: (query: string, optionsOrTopK?: {
            namespace?: string;
            spheres?: string[];
            topK?: number;
        } | number) => Promise<MemoryRecord[]>;
    };
    readonly neuralNetwork: {
        retrieve: (query: string, options?: {
            spheres?: string[];
            maxHops?: number;
        }) => Promise<NeuralContextPacket>;
    };
    readonly governance: {
        evaluateAction: (agentIdOrOptions: {
            agentId?: string;
            actionType: string;
            parameters?: Record<string, unknown>;
            stateHash?: string;
            namespace?: string;
        } | string, actionType?: string, parameters?: Record<string, unknown>, stateHash?: string) => Promise<ActionJudgment>;
    };
    readonly actions: {
        execute: (executionToken: string, status?: string) => Promise<ExecutionReceipt>;
    };
    constructor(config?: ExogramClientConfig);
    private getHeaders;
    getCurrentStateHash(): string;
    private _vaultStore;
    private _vaultSearch;
    private _neuralRetrieve;
    private _governanceEvaluate;
    private _actionsExecute;
    /**
     * Request cryptographic action authorization before executing a tool call.
     */
    evaluate(actionType: string, options?: {
        namespace?: string;
        agentId?: string;
        payload?: Record<string, unknown> | string;
    }): Promise<EvaluationResult>;
    /**
     * Commit an executed action token to the immutable audit trail.
     */
    commit(token: string, status?: string, payload?: Record<string, unknown>): Promise<CommitResult>;
    /**
     * Store a record or fact in the Exogram Encrypted Trust Vault.
     */
    storeRecord(content: string, options?: {
        source?: string;
        namespace?: string;
    }): Promise<VaultStoreResult>;
    store(content: string, options?: {
        source?: string;
        namespace?: string;
    }): Promise<VaultStoreResult>;
    /**
     * Search vault records using semantic vector search.
     */
    searchRecords(query: string, topK?: number): Promise<VaultSearchResult>;
    search(query: string, topK?: number): Promise<VaultSearchResult>;
}
declare const ExogramClient: typeof Exogram;
type ExogramClient = Exogram;

export { type ActionJudgment, type CommitResult, type EvaluationResult, type ExecutionReceipt, Exogram, ExogramClient, type ExogramClientConfig, type MemoryRecord, type NeuralContextPacket, type NeuralEntityNode, type VaultRecord, type VaultSearchResult, type VaultStoreResult };
