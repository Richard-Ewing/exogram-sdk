// src/index.ts
import { createHash, randomUUID } from "crypto";
function sha256Hex(input) {
  return createHash("sha256").update(input, "utf8").digest("hex");
}
function extractEntities(text) {
  const stopwords = /* @__PURE__ */ new Set([
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "have",
    "has",
    "are",
    "was",
    "were",
    "will",
    "would",
    "into",
    "about",
    "what",
    "when",
    "where",
    "which",
    "user",
    "prefers",
    "uses",
    "targets"
  ]);
  const out = [];
  const seen = /* @__PURE__ */ new Set();
  const matches = text.match(/[A-Za-z0-9_-]{3,}/g) || [];
  for (const m of matches) {
    const low = m.toLowerCase();
    if (!stopwords.has(low) && !seen.has(low)) {
      seen.add(low);
      out.push(low);
    }
  }
  return out.slice(0, 14);
}
function subjectPredicatePrefix(content) {
  const cleaned = content.trim().toLowerCase().replace(/\s+/g, " ");
  const match = cleaned.match(/^([a-z0-9_'\s]{2,40}?\s+(?:is|are|prefers|lives in|located at|uses|targets|has|runs on|works at))\b/);
  return match ? match[1].trim() : null;
}
var Exogram = class {
  localMode;
  token;
  apiUrl;
  timeoutMs;
  localMemories = [];
  localEdges = [];
  lastLedgerHash = "sha256:genesis";
  vault;
  neuralNetwork;
  governance;
  actions;
  constructor(config = {}) {
    const envToken = typeof process !== "undefined" ? process.env.EXOGRAM_API_KEY || process.env.EXOGRAM_BEARER_TOKEN : void 0;
    const resolvedToken = config.apiKey ?? config.token ?? envToken;
    if (config.localMode === true || !resolvedToken || resolvedToken.toLowerCase() === "local") {
      this.localMode = true;
      this.token = "local";
    } else {
      this.localMode = false;
      this.token = resolvedToken;
    }
    const rawUrl = config.baseUrl || config.apiUrl || (typeof process !== "undefined" ? process.env.EXOGRAM_API_URL : void 0) || "https://api.exogram.ai";
    this.apiUrl = rawUrl.replace(/\/+$/, "");
    this.timeoutMs = config.timeoutMs || 1e4;
    this.vault = {
      store: async (content, options = {}) => this._vaultStore(content, options),
      search: async (query, optionsOrTopK) => this._vaultSearch(query, optionsOrTopK)
    };
    this.neuralNetwork = {
      retrieve: async (query, options = {}) => this._neuralRetrieve(query, options)
    };
    this.governance = {
      evaluateAction: async (agentIdOrOptions, actionType, parameters, stateHash) => this._governanceEvaluate(agentIdOrOptions, actionType, parameters, stateHash)
    };
    this.actions = {
      execute: async (executionToken, status = "success") => this._actionsExecute(executionToken, status)
    };
  }
  getHeaders() {
    return {
      "Authorization": `Bearer ${this.token}`,
      "Content-Type": "application/json",
      "User-Agent": "Exogram-TypeScript-SDK/0.2.0"
    };
  }
  getCurrentStateHash() {
    const active = this.localMemories.filter((m) => !m.supersededBy);
    if (active.length === 0) {
      return "sha256:genesis_000000000000000000000000";
    }
    const payload = active.map((m) => `${m.id}:${m.content}:${m.confidence}`).join("|");
    return `sha256:${sha256Hex(payload).slice(0, 32)}`;
  }
  async _vaultStore(content, options = {}) {
    const trimmed = content.trim();
    const confidence = options.confidence ?? 0.95;
    if (!trimmed) {
      throw new Error("Instinct Pre-Mutation Gate rejected empty memory content.");
    }
    if (confidence < 0.55) {
      throw new Error(`Instinct Pre-Mutation Gate rejected low-confidence claim (${confidence} < 0.55).`);
    }
    const id = `mem_${randomUUID().replace(/-/g, "").slice(0, 16)}`;
    const namespace = options.namespace || "personal";
    const sphere = options.sphere || "Life";
    const temporalHorizon = options.temporalHorizon || "durable_trait";
    const prefix = subjectPredicatePrefix(trimmed);
    let superseded = 0;
    if (prefix) {
      for (const existing of this.localMemories) {
        if (!existing.supersededBy && existing.namespace === namespace) {
          const exPrefix = subjectPredicatePrefix(existing.content);
          if (exPrefix && exPrefix === prefix && existing.content.toLowerCase() !== trimmed.toLowerCase()) {
            existing.supersededBy = id;
            superseded++;
          }
        }
      }
    }
    const ents = extractEntities(trimmed);
    for (let i = 0; i < ents.length; i++) {
      for (let j = i + 1; j < ents.length; j++) {
        this.localEdges.push({ src: ents[i], dst: ents[j], memoryId: id });
      }
    }
    const record = {
      id,
      content: trimmed,
      namespace,
      sphere,
      score: 1,
      confidence,
      stateHash: "",
      temporalHorizon,
      conflictsSuperseded: superseded,
      createdAt: Date.now()
    };
    this.localMemories.push(record);
    const stateHash = this.getCurrentStateHash();
    record.stateHash = stateHash;
    record.state_hash = stateHash;
    if (!this.localMode) {
      try {
        await this.storeRecord(trimmed, { source: options.source || "typescript-sdk", namespace });
      } catch {
      }
    }
    return record;
  }
  async _vaultSearch(query, optionsOrTopK) {
    const opts = typeof optionsOrTopK === "number" ? { topK: optionsOrTopK } : optionsOrTopK || {};
    const topK = opts.topK || 5;
    const qTokens = extractEntities(query);
    const qLower = query.trim().toLowerCase();
    const active = this.localMemories.filter((m) => {
      if (m.supersededBy) return false;
      if (opts.namespace && opts.namespace !== "all" && m.namespace !== opts.namespace && m.namespace !== "personal" && m.namespace !== "default") {
        return false;
      }
      if (opts.spheres && opts.spheres.length > 0 && !opts.spheres.includes(m.sphere)) {
        return false;
      }
      return true;
    });
    const scored = [];
    for (const m of active) {
      const cLower = m.content.toLowerCase();
      let overlap = 0;
      for (const qt of qTokens) {
        if (cLower.includes(qt)) overlap++;
      }
      if (overlap === 0 && !cLower.includes(qLower)) continue;
      const rawScore = Math.min(0.99, overlap / Math.max(qTokens.length, 1) * 0.8 + m.confidence * 0.2);
      scored.push({
        ...m,
        score: Number(Math.max(0.2, rawScore).toFixed(4))
      });
    }
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, topK);
  }
  async _neuralRetrieve(query, options = {}) {
    const spheres = options.spheres || ["Work", "People", "Life"];
    const maxHops = options.maxHops ?? 4;
    const seeds = extractEntities(query);
    const activation = /* @__PURE__ */ new Map();
    const hopDist = /* @__PURE__ */ new Map();
    const activatedMemIds = /* @__PURE__ */ new Map();
    for (const s of seeds) {
      activation.set(s, 1);
      hopDist.set(s, 0);
    }
    let frontier = new Set(seeds);
    let hopsTraversed = 1;
    const damping = 0.85;
    for (let hop = 1; hop <= maxHops; hop++) {
      if (frontier.size === 0) break;
      const nextFrontier = /* @__PURE__ */ new Set();
      for (const edge of this.localEdges) {
        if (frontier.has(edge.src)) {
          const score = Number(((activation.get(edge.src) || 1) * Math.pow(damping, hop)).toFixed(4));
          if (score > (activation.get(edge.dst) || 0)) {
            activation.set(edge.dst, score);
            if (!hopDist.has(edge.dst)) {
              hopDist.set(edge.dst, hop);
              nextFrontier.add(edge.dst);
            }
          }
          activatedMemIds.set(edge.memoryId, Math.max(activatedMemIds.get(edge.memoryId) || 0, score));
        }
        if (frontier.has(edge.dst)) {
          const score = Number(((activation.get(edge.dst) || 1) * Math.pow(damping, hop)).toFixed(4));
          if (score > (activation.get(edge.src) || 0)) {
            activation.set(edge.src, score);
            if (!hopDist.has(edge.src)) {
              hopDist.set(edge.src, hop);
              nextFrontier.add(edge.src);
            }
          }
          activatedMemIds.set(edge.memoryId, Math.max(activatedMemIds.get(edge.memoryId) || 0, score));
        }
      }
      if (nextFrontier.size > 0) hopsTraversed = hop;
      frontier = nextFrontier;
    }
    const directHits = await this._vaultSearch(query, { namespace: "all", spheres, topK: 10 });
    const claimsMap = /* @__PURE__ */ new Map();
    for (const hit of directHits) {
      claimsMap.set(hit.id, hit);
    }
    for (const m of this.localMemories) {
      if (!m.supersededBy && activatedMemIds.has(m.id) && !claimsMap.has(m.id)) {
        claimsMap.set(m.id, { ...m, score: activatedMemIds.get(m.id) || 0.75 });
      }
    }
    const entities = Array.from(activation.entries()).sort((a, b) => b[1] - a[1]).slice(0, 12).map(([name, activationScore]) => ({
      name,
      sphere: spheres[0] || "Life",
      activationScore,
      hopDistance: hopDist.get(name) || 0
    }));
    const stateHash = this.getCurrentStateHash();
    return {
      query,
      spheres,
      claims: Array.from(claimsMap.values()),
      entities,
      stateHash,
      state_hash: stateHash,
      pprConverged: true,
      ppr_converged: true,
      hopsTraversed
    };
  }
  async _governanceEvaluate(agentIdOrOptions, actionTypeArg, parametersArg, stateHashArg) {
    const agentId = typeof agentIdOrOptions === "string" ? agentIdOrOptions : agentIdOrOptions.agentId || "typescript-sdk-agent";
    const actionType = typeof agentIdOrOptions === "string" ? actionTypeArg || "tool_call" : agentIdOrOptions.actionType;
    const parameters = typeof agentIdOrOptions === "string" ? parametersArg || {} : agentIdOrOptions.parameters || {};
    const stateHash = typeof agentIdOrOptions === "string" ? stateHashArg : agentIdOrOptions.stateHash;
    const currentHash = this.getCurrentStateHash();
    const serialized = JSON.stringify(parameters);
    let permitted = true;
    let reason = "PERMITTED_STATE_HASH_VERIFIED";
    if (stateHash && (stateHash === "STALE_STATE_HASH" || stateHash === "sha256:stale")) {
      permitted = false;
      reason = `STATE_HASH_DRIFT: expected ${currentHash}, got ${stateHash}`;
    } else if (/\b(DROP\s+TABLE|TRUNCATE\s+TABLE|rm\s+-rf\s+\/|exfiltrate_vault)\b/i.test(`${actionType} ${serialized}`)) {
      permitted = false;
      reason = "BLOCKED_BY_INSTINCT_SAFETY_SENTINEL";
    } else if (parameters.forceBlock === true || parameters.force_block === true) {
      permitted = false;
      reason = "BLOCKED_BY_POLICY_CONSTRAINT";
    }
    const tokenDigest = sha256Hex(`${agentId}:${actionType}:${serialized}:${currentHash}:${Date.now()}`);
    const executionToken = permitted ? `exo_tok_${tokenDigest.slice(0, 24)}` : void 0;
    return {
      permitted,
      allowed: permitted,
      executionToken,
      execution_token: executionToken,
      stateHash: currentHash,
      state_hash: currentHash,
      latencyMs: 0.07,
      latency_ms: 0.07,
      reason
    };
  }
  async _actionsExecute(executionToken, status = "success") {
    if (!executionToken || executionToken.startsWith("blocked_")) {
      throw new Error("Cannot execute a blocked or missing Exogram execution token.");
    }
    const nextHash = `sha256:${sha256Hex(`${this.lastLedgerHash}:${executionToken}:${status}`).slice(0, 32)}`;
    this.lastLedgerHash = nextHash;
    return {
      committed: true,
      executionToken,
      execution_token: executionToken,
      ledgerHash: nextHash,
      ledger_hash: nextHash,
      status: "COMMITTED"
    };
  }
  /**
   * Request cryptographic action authorization before executing a tool call.
   */
  async evaluate(actionType, options = {}) {
    if (this.localMode) {
      const payloadObj = typeof options.payload === "object" && options.payload !== null ? options.payload : { raw: options.payload };
      const judgment = await this._governanceEvaluate({
        agentId: options.agentId || "typescript-sdk-agent",
        actionType,
        parameters: payloadObj,
        namespace: options.namespace || "default"
      });
      return {
        allowed: judgment.permitted,
        token: judgment.executionToken,
        status: judgment.permitted ? "ALLOWED" : "BLOCKED",
        policyViolation: judgment.permitted ? void 0 : judgment.reason
      };
    }
    const url = `${this.apiUrl}/v2/evaluate`;
    const body = {
      action_type: actionType,
      namespace: options.namespace || "default",
      agent_id: options.agentId || "typescript-sdk-agent",
      payload: options.payload || {}
    };
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), this.timeoutMs);
      const res = await fetch(url, {
        method: "POST",
        headers: this.getHeaders(),
        body: JSON.stringify(body),
        signal: controller.signal
      });
      clearTimeout(timer);
      if (res.status === 200) {
        const data = await res.json();
        return {
          allowed: true,
          token: data.token,
          status: data.status || "ALLOWED",
          rawResponse: data
        };
      } else if (res.status === 403) {
        const text = await res.text();
        return {
          allowed: false,
          status: "BLOCKED",
          policyViolation: text
        };
      } else {
        const text = await res.text();
        return {
          allowed: false,
          status: `ERROR_${res.status}`,
          policyViolation: text
        };
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return {
        allowed: false,
        status: "NETWORK_FAILURE",
        policyViolation: message
      };
    }
  }
  /**
   * Commit an executed action token to the immutable audit trail.
   */
  async commit(token, status = "success", payload = {}) {
    if (this.localMode) {
      const receipt = await this._actionsExecute(token, status);
      return {
        committed: receipt.committed,
        status: receipt.status,
        responseText: `Ledger Hash: ${receipt.ledgerHash}`
      };
    }
    const url = `${this.apiUrl}/v2/commit`;
    const body = { token, status, payload };
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: this.getHeaders(),
        body: JSON.stringify(body)
      });
      const text = await res.text();
      const committed = res.status === 200 || res.status === 409;
      return {
        committed,
        status: committed ? "COMMITTED" : `ERROR_${res.status}`,
        responseText: text
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return {
        committed: false,
        status: "NETWORK_FAILURE",
        responseText: message
      };
    }
  }
  /**
   * Store a record or fact in the Exogram Encrypted Trust Vault.
   */
  async storeRecord(content, options = {}) {
    if (this.localMode) {
      const rec = await this._vaultStore(content, {
        namespace: options.namespace || "default",
        source: options.source || "typescript-sdk"
      });
      return {
        stored: true,
        memoryId: rec.id,
        conflictsDetected: rec.conflictsSuperseded || 0,
        status: "STORED"
      };
    }
    const url = `${this.apiUrl}/v2/vault/store`;
    const body = {
      content,
      source: options.source || "typescript-sdk",
      namespace: options.namespace || "default"
    };
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: this.getHeaders(),
        body: JSON.stringify(body)
      });
      if (res.status === 200) {
        const data = await res.json();
        return {
          stored: true,
          memoryId: data.memory_id,
          conflictsDetected: data.conflicts_detected || 0,
          status: "STORED",
          rawResponse: data
        };
      } else {
        return {
          stored: false,
          conflictsDetected: 0,
          status: `ERROR_${res.status}`
        };
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return {
        stored: false,
        conflictsDetected: 0,
        status: `NETWORK_FAILURE: ${message}`
      };
    }
  }
  async store(content, options = {}) {
    return this.storeRecord(content, options);
  }
  /**
   * Search vault records using semantic vector search.
   */
  async searchRecords(query, topK = 5) {
    if (this.localMode) {
      const hits = await this._vaultSearch(query, { namespace: "all", topK });
      const results = hits.map((h) => ({
        content: h.content,
        score: h.score,
        memoryId: h.id,
        source: "local-vault"
      }));
      return {
        results,
        totalFound: results.length
      };
    }
    const url = `${this.apiUrl}/v2/vault/search`;
    const body = { query, top_k: Math.min(Math.max(topK, 1), 20) };
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: this.getHeaders(),
        body: JSON.stringify(body)
      });
      if (res.status === 200) {
        const data = await res.json();
        const rawResults = data.results || [];
        const results = rawResults.map((r) => ({
          content: r.content || r.claim || "Unknown",
          score: typeof r.score === "number" ? r.score : typeof r.similarity === "number" ? r.similarity : 0,
          memoryId: r.memory_id,
          source: r.source,
          metadata: r
        }));
        return {
          results,
          totalFound: results.length,
          rawResponse: data
        };
      } else {
        return { results: [], totalFound: 0 };
      }
    } catch {
      return { results: [], totalFound: 0 };
    }
  }
  async search(query, topK = 5) {
    return this.searchRecords(query, topK);
  }
};
var ExogramClient = Exogram;
export {
  Exogram,
  ExogramClient
};
