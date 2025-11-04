# zenrube-mcp

**Zen-Inspired Consensus for Rube Workflows**

*Multi-model AI orchestration adapted from [Zen MCP](https://github.com/BeehiveInnovations/zen-mcp-server), built natively for the [Rube](https://rube.composio.dev) automation platform*

---

## 🎯 What is This?

**zenrube-mcp** brings the multi-model AI consensus patterns from Zen MCP to Rube's cloud automation platform. Instead of being limited to one AI model, you can now orchestrate multiple AI experts to:

- ✅ Get diverse perspectives on complex decisions
- ✅ Reduce AI bias and groupthink
- ✅ Synthesize expert opinions into actionable recommendations
- ✅ Integrate with Rube's 500+ app connections

## 🧠 The Concept

**Original Idea:** [@vmanoilov](https://github.com/vmanoilov)  
**Inspired By:** [Zen MCP](https://github.com/BeehiveInnovations/zen-mcp-server) by BeehiveInnovations  
**Platform:** [Rube](https://rube.composio.dev) by Composio

### How It Works

```
Question → Multiple AI Experts → Individual Analyses → Synthesized Consensus
```

Each expert analyzes the problem from a different perspective:
- **Expert 1:** Pragmatic engineering (practical trade-offs, real-world constraints)
- **Expert 2:** Systems architecture (scalability, maintainability, patterns)
- **Expert 3:** Security focus (vulnerabilities, best practices, compliance)

The system then synthesizes all perspectives into a balanced recommendation with confidence scoring.

---

## 📊 Example

**Question:** "Should we use Redis or Memcached for session caching?"

**Result:**
- 3 detailed expert analyses from different perspectives
- Synthesized consensus highlighting agreements and disagreements
- Clear recommendation with HIGH confidence
- Actionable operational checklist

---

## 🚀 Quick Start

In Rube's REMOTE_WORKBENCH:

```python
from zenrube import zen_consensus

result = zen_consensus(
    question="Your complex decision here",
    models=["expert_1", "expert_2", "expert_3"],
    synthesis_style="balanced"
)

print(result['consensus'])
```

---

## 🏗️ Architecture

Adapted from Zen MCP's core patterns:

| Zen MCP Feature | Rube Equivalent | Status |
|----------------|-----------------|--------|
| Multi-model orchestration | `invoke_llm` with prompts | ✅ Works |
| Conversation threading | Workbench state | ✅ Works |
| Synthesis pattern | LLM combining responses | ✅ Works |
| Structured output | JSON results | ✅ Works |

---

## 🤝 Contributing

Contributions welcome! This is experimental - help make it better.

---

## 📄 License

Apache License 2.0 (matches Zen MCP)

---

## 🙏 Acknowledgments

- **Original Concept:** [@vmanoilov](https://github.com/vmanoilov)
- **Inspired By:** [Zen MCP](https://github.com/BeehiveInnovations/zen-mcp-server)
- **Platform:** [Rube](https://rube.composio.dev) by Composio

---

**Built with ❤️ by [@vmanoilov](https://github.com/vmanoilov)**

*"Many Models. One Mind."*
