mcp-name: io.github.Richard-Ewing/exogram
<!-- mcp-name: io.github.Richard-Ewing/exogram -->

# Exogram FastMCP Server (`v0.2.0`)

[![PyPI](https://img.shields.io/pypi/v/mcp-server-exogram)](https://pypi.org/project/mcp-server-exogram/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Universal Model Context Protocol (MCP) server for **Exogram** — giving Claude Desktop, Cursor, Google Antigravity, and OpenAI Agents direct access to your Personal Neural Network (`Work · People · Life`), Encrypted Memory Vault, 12 A2UI Composable Living Tiles, and Deterministic `0.07ms` Instinct Action Governance.

Runs out-of-the-box in **Zero-Signup Local SQLite WAL Mode** (`~/.exogram/vault.db`) when no API key is set, or connects to **Exogram Cloud** (`https://exogram.ai/api/mcp`) when `EXOGRAM_API_KEY` is provided.

## 30-Second Zero-Signup Quickstart

```bash
uvx mcp-server-exogram --local
```

### Claude Desktop / Cursor / Antigravity Config (Zero-Signup Local Mode)

```json
{
  "mcpServers": {
    "exogram": {
      "command": "uvx",
      "args": ["mcp-server-exogram", "--local"]
    }
  }
}
```

### Cloud Mode Config (`https://exogram.ai/api/mcp`)

```json
{
  "mcpServers": {
    "exogram": {
      "command": "uvx",
      "args": ["mcp-server-exogram"],
      "env": {
        "EXOGRAM_API_KEY": "exo_live_your_api_key",
        "EXOGRAM_API_URL": "https://api.exogram.ai"
      }
    }
  }
}
```

## Exposed MCP Tools

| Tool | Description |
|------|-------------|
| `search_memory_vault` | Hybrid RRF semantic + lexical search across `Work`, `People`, and `Life` spheres |
| `update_memory_vault` | Persist salient facts with 3-Horizon Episodic Lifecycle & Instinct Pre-Mutation gating |
| `traverse_neural_graph` | Infinite-Hop Spreading Activation + HippoRAG 2 Spectral PPR traversal |
| `evaluate_instinct_action_gate` | Deterministic `0.07ms` state-hash verification & Instinct action gate |
| `render_live_widget` | Emit validated A2UI Composable Living Tiles (`living-tiles-v5.schema.json`) |
| `exogram_evaluate_action` | Request cryptographic action authorization token |
| `exogram_commit_action` | Commit executed action token to the SHA-256 audit hash chain |
| `exogram_store_record` | Store a record in the Exogram Vault |
| `exogram_search_records` | Search stored records in the Exogram Vault |

## License

MIT — see [LICENSE](LICENSE) for details.
