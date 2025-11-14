# server.py
from mcp.server import FastMCP
from pydantic import BaseModel
import importlib

# Initialize MCP server
server = FastMCP(name="zenrube")

# Load actual ZenRube modules
from zenrube.experts.semantic_router import SemanticRouterExpert
from zenrube.experts_module import get_expert
from zenrube.experts.expert_registry import ExpertRegistry

# Initialize experts
semantic_router = SemanticRouterExpert()
expert_registry = ExpertRegistry()

@server.tool()
def route(prompt: str) -> list[str]:
    """Return the expert sequence from the real ZenRube semantic router."""
    result = semantic_router.run(prompt)
    # Extract route from the result
    return [result.get("route", "general_handler")]

@server.tool()
def run(expert: str, prompt: str) -> str:
    """Execute a single ZenRube expert."""
    try:
        expert_definition = get_expert(expert)
        return expert_definition.build_prompt(prompt)
    except KeyError:
        return f"Error: Expert '{expert}' not found."

# export app for FastMCP
app = server.streamable_http_app
