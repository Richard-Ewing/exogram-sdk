<div align="center">

# Exogram SDK & MCP Runtime

### Personal Neural Network · 7-Lab Specialist Swarm · Interactive Living Tiles · 0.07ms Action Governance

[![Production](https://img.shields.io/badge/Live_Workspace-exogram.ai%2Fdashboard%2Fchat-6d28d9?style=for-the-badge)](https://exogram.ai/dashboard/chat)
[![Version](https://img.shields.io/badge/Version-3.3.0-059669?style=for-the-badge)](https://exogram.ai/changelog)
[![Protocol](https://img.shields.io/badge/Specification-Exogram_Protocol_RFC-2563eb?style=for-the-badge)](https://github.com/Richard-Ewing/exogram-protocol-rfc)
[![AWS Showcase](https://img.shields.io/badge/AWS-Startup_Showcase-f97316?style=for-the-badge)](https://aws.amazon.com/startups/showcase/startup-details/3340d267-ae86-4467-8775-4f0e60a3edc5)

[Live Workspace](https://exogram.ai/dashboard/chat) · [Documentation](https://exogram.ai/docs) · [Protocol RFC](https://github.com/Richard-Ewing/exogram-protocol-rfc) · [Architecture](https://exogram.ai/architecture/runtime-governance)

</div>

---

## Why Exogram Exists

Standard LLM wrappers and agent frameworks fail in production for three structural reasons:
1. **Cross-Session Amnesia & Context Noise**: Traditional RAG dumps raw vector chunks into the prompt, repeating duplicate facts and leaking irrelevant clauses.
2. **Dead Text Instead of Interactive Work**: Most assistants output walls of Markdown instead of interactive, stateful UI deliverables or governed outbound actions.
3. **Unverified Tool Execution & Single-Provider Fragility**: Probabilistic agents execute consequential actions without state-hash verification and fail whenever a single model provider hits HTTP 429.

**Exogram** solves all three inside a single closed-loop runtime:

```text
┌───────────────────────────────────────────────────────────────────────────────────┐
│ 1. PERSONAL NEURAL NETWORK (Work · People · Life Spheres)                         │
│    • OpenViking L0/L1/L2 Progressive Clause Pruning & Entity Deduplication        │
│    • HippoRAG 2 Spectral Personalized PageRank (D⁻¹/² A D⁻¹/²) Hub-Node Damping   │
│    • 4-Way Reciprocal Rank Fusion (Pinecone Vectors + Lexical + Layer-2 Graph)    │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │ Privacy-Minimized Context Packets
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│ 2. 7-LAB SPECIALIST SWARM & ROUTELLM CAPABILITY POOL                              │
│    • Dots (Graph Walker) · Claude (Strategy/Red-Team) · GrokBot (Counter-Audit)   │
│    • OpenClaw (Live URL) · Perplexity (Citations)     · Hermes (Action Staging)   │
│    • RouteLLM Capability Gating across Gemini, Groq, Cerebras, SambaNova, NIM     │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │ Dual-Track SSE Stream + Turn Blackboard
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│ 3. AG-UI LIVING TILES & EAAP CRYPTOGRAPHIC GOVERNANCE (0.07ms)                    │
│    • Living Tiles: action_draft · checklist · decision_matrix · places_court      │
│    • SHA-256 State-Hash Verification + Replay-Proof Execution Tokens              │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Capabilities

| Capability | Architectural Primitive | Production Guarantee |
| :--- | :--- | :--- |
| **3-Sphere Personal Neural Network** | OpenViking L0/L1/L2 + HippoRAG 2 Spectral PPR | Consolidates duplicate entity cards, prunes unrelated composite clauses, and damps high-degree hub nodes (`1 / sqrt((1+deg(u))(1+deg(v)))`). |
| **Per-Agent Privacy Minimization** | Context Privacy Classifier (`PUBLIC` to `RESTRICTED_PII_HEALTH`) | Web-research agents (`OpenClaw`, `Perplexity`) never receive private family or sensitive vault records. |
| **7-Specialist Agent Swarm** | Parallel Structured Briefing Router | Concurrent execution of `Dots`, `Claude`, `GrokBot`, `OpenClaw`, `Perplexity`, `Kimi`, and `Hermes` with post-response `Used` vs. `Available` reconciliation. |
| **Multi-Lab Capability Router** | RouteLLM Task Gating + Cooldown Registry | Automatic 429/503 slot cooldowns and task-profile filtering across Gemini, Anthropic, OpenAI, Grok, GitHub Models, Groq, Cerebras, SambaNova, NVIDIA NIM, and OpenRouter. |
| **AG-UI Turn Blackboard & Living Tiles** | Dual-Track SSE + Deterministic Tile Compiler | Guarantees schema-validated interactive tiles (`action_draft`, `checklist`, `decision_matrix`, `places_court`) without leaking raw widget JSON into prose. |
| **EAAP Execution Kernel** | 0.07ms SHA-256 State-Hash Gate | Binds consequential actions to a cryptographic state hash and halts on parameter tampering or token replay. |

---

## Quickstart: Model Context Protocol (MCP) & SDK Usage

### 1. Connect Exogram MCP to Claude Desktop, Cursor, or Windsurf

Add the Exogram MCP server to your `claude_desktop_config.json` or `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "exogram": {
      "command": "npx",
      "args": ["-y", "mcp-server-exogram"],
      "env": {
        "EXOGRAM_API_KEY": "exo_live_..."
      }
    }
  }
}
```

### 2. Evaluate & Authorize Consequential Agent Actions (Python SDK)

```python
from exogram import ExogramClient

client = ExogramClient(api_key="exo_live_...")

# 1. Retrieve sphere-classified, HippoRAG-ranked context for the current turn
context = client.neural_network.retrieve(
    query="Draft a reply to James at ZestifyApp regarding partnership",
    spheres=["Work", "People"],
)

# 2. Verify action admissibility via the 0.07ms EAAP deterministic kernel
judgment = client.governance.evaluate_action(
    agent_id="hermes",
    action_type="email.send",
    parameters={
        "recipient": "James <james@zestifyapp.com>",
        "subject": "Re: ZestifyApp Partnership Inquiry",
    },
    state_hash=context.state_hash,
)

if judgment.permitted:
    client.actions.execute(judgment.execution_token)
```

---

## Ecosystem Integrations

| Surface / Framework | Status | Description |
| :--- | :--- | :--- |
| **[Exogram AI Workspace](https://exogram.ai/dashboard/chat)** | ✅ Production | Full conversational workspace with Living Tiles, 7-Agent Swarm, and Context Inspector |
| **Model Context Protocol (MCP)** | ✅ Production | Native MCP server for Claude Desktop, Cursor, Windsurf, and Antigravity |
| **LangChain / LangGraph** | ✅ Production | Drop-in memory retriever and EAAP tool-execution guard ([Docs](https://exogram.ai/docs/sdk/langchain)) |
| **REST & SSE Streaming API** | ✅ Production | Dual-track SSE streaming (`token`, `thinking_step`, `context_packet`, `agent_evidence`, `live_widget`) |

---

## Security & Sovereignty

* **AES-256 Vault Encryption**: Encrypted ledger persistence across Supabase Postgres and local SQLite WAL.
* **SHA-256 Hash-Linked Audit Ledger**: Tamper-evident verification for every tool call and memory mutation.
* **Zero Data Retention (ZDR) Routing**: Automatically filters out untrusted model pools whenever private vault context is active in a turn.
* **Session-Only vs. Durable Memory Governance**: Rejects API keys/secrets from ever entering memory and keeps temporary tone/slider calibration session-scoped unless explicitly saved.

---

<div align="center">

Built by **[Richard Ewing](https://github.com/Richard-Ewing)** · **[exogram.ai](https://exogram.ai)**

</div>
