<div align="center">

# Exogram SDK

### The Execution Authority Layer for Autonomous AI

**AI Proposes. Exogram Decides.**

[![Production](https://img.shields.io/badge/status-production-brightgreen?style=flat-square)](https://exogram.ai)
[![Version](https://img.shields.io/badge/version-3.2.0-violet?style=flat-square)](https://exogram.ai/changelog)
[![License](https://img.shields.io/badge/license-proprietary-blue?style=flat-square)](https://exogram.ai/terms)
[![AWS Showcase](https://img.shields.io/badge/AWS-Startup%20Showcase-orange?style=flat-square)](https://aws.amazon.com/startups/showcase/startup-details/3340d267-ae86-4467-8775-4f0e60a3edc5)

[Website](https://exogram.ai) · [Docs](https://exogram.ai/docs) · [Changelog](https://exogram.ai/changelog) · [Protocol (EAAP)](https://github.com/Richard-Ewing/exogram-protocol-rfc)

</div>

---

## The Problem

Every major AI framework — LangChain, CrewAI, AutoGen, Claude MCP — lets agents call APIs, modify databases, and execute workflows based entirely on probabilistic output. **There is no enforcement layer between what the AI suggests and what the system executes.**

If the output looks structurally valid, it runs. No verification. No audit trail. No kill switch.

## The Solution

Exogram is a deterministic **runtime governance layer** that intercepts every AI agent action at the execution boundary. Before any proposed action reaches your production infrastructure, Exogram evaluates it against policy, verifies state integrity, and renders a cryptographically signed `PERMIT` or `DENY` judgment.

**Zero LLM inference in the decision path.** Same input → same output → every time.

---

## How It Works

```
┌─────────────────────────────────────────────────────┐
│  AI AGENT (GPT, Claude, Gemini, Llama, etc.)        │
│  Proposes an action                                 │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  EXOGRAM RUNTIME GOVERNANCE                         │
│                                                     │
│  L1  Semantic Environment Construction              │
│      Resolve conflicts, establish ground truth       │
│                                                     │
│  L2  Graph-Grounded Context Assembly                │
│      Deterministic context sub-graph, no guessing    │
│                                                     │
│  L3  Deterministic Policy Evaluation                │
│      7-gate judgment engine, zero probabilistic      │
│      interpretation                                  │
│                                                     │
│  L4  Cryptographic Commit & Audit Chain             │
│      SHA-256 hash-linked, append-only, immutable     │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
           PERMIT (signed token)
                  or
           DENY (with reason)
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| **0.07ms Latency** | Deterministic evaluation — no LLM in the decision path |
| **7-Gate Judgment Engine** | Multi-factor policy evaluation with cryptographic signing |
| **Interactive Knowledge Graph** | Force-directed visualization of your entire semantic trust network |
| **Behavioral Synthesis** | AI-powered cross-entry inference for behavioral patterns and insights |
| **Cryptographic Audit Chain** | SHA-256 hash-linked, append-only — every decision permanently provable |
| **Agent Identity Gating** | Per-agent permit/deny lists enforced before policy evaluation |
| **UUID-Hardened Identity** | Strict validation prevents spoofing and injection at every endpoint |
| **Model Agnostic** | Works with GPT, Claude, Gemini, Llama — any model, any framework |

---

## Integrations

| Platform | Status |
|----------|--------|
| **REST API** | ✅ Production |
| **Claude MCP** | ✅ Production |
| **ChatGPT (Custom GPT)** | ✅ Production |
| **Chrome Extension** | ✅ Production |
| **LangChain** | ✅ Production |
| **CrewAI** | ✅ Compatible |
| **AutoGen** | ✅ Compatible |

---

## Architecture

Exogram occupies **Layer 4** in the AI infrastructure stack — the missing execution authority between orchestration and production systems:

| Layer | Role | Examples |
|-------|------|----------|
| L1 — Models | Probabilistic reasoning | GPT, Claude, Gemini, Llama |
| L2 — Context | State and retrieval | RAG, vector stores, session state |
| L3 — Orchestration | Task coordination | LangChain, CrewAI, AutoGen |
| **L4 — Execution Authority** | **Deterministic governance** | **Exogram** |

---

## Getting Started

Visit [exogram.ai/docs](https://exogram.ai/docs) to get started.

---

## Use Cases

- **Prevent AI Double-Spend** — Idempotency enforcement for financial operations
- **Stop AI SQL Injection** — Block destructive queries before execution
- **SOC 2 Audit Trails** — Compliance-ready logging for every AI decision
- **HIPAA AI Constraints** — Healthcare-grade governance boundaries
- **Fix AutoGen Loops** — Circuit-breaker patterns for multi-agent systems

[All Use Cases →](https://exogram.ai/use-cases)

---

## Compare

[vs LangChain](https://exogram.ai/compare/exogram-vs-langchain) · [vs CrewAI](https://exogram.ai/compare/exogram-vs-crewai) · [vs Guardrails AI](https://exogram.ai/compare/exogram-vs-guardrails-ai) · [vs OpenAI](https://exogram.ai/compare/exogram-vs-openai) · [All Comparisons](https://exogram.ai/compare)

---

## Security & Compliance

- 🔒 AES-256 encryption at rest, TLS 1.3 in transit
- 🔗 SHA-256 cryptographic audit chain
- 🛡️ UUID-hardened identity at every boundary
- 📋 SOC 2 Type II (in progress)
- 🌐 GDPR compliant data export
- 🏥 HIPAA BAA available (Enterprise)

[Security & Compliance](https://exogram.ai/security)

---

## About

Built by [Richard Ewing](https://richardewing.io) — AI Economist, published in Foundry and Built In.

> *"The biggest problem we face is that we are giving AI the keys to the car without building the brakes."*

[About Exogram](https://exogram.ai/about) · [Manifesto](https://exogram.ai/manifesto)

---

<div align="center">

**[exogram.ai](https://exogram.ai)**

*Making autonomous intelligence persistent and verifiable.*

</div>
