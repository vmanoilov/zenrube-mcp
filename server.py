# server.py
from fastmcp import FastMCP
from zenrube.experts.semantic_router import SemanticRouterExpert
from zenrube.experts_module import get_expert
from zenrube.experts.expert_registry import ExpertRegistry

mcp = FastMCP("ZenRube")

semantic_router = SemanticRouterExpert()
expert_registry = ExpertRegistry()

@mcp.tool
def route(prompt: str) -> list[str]:
    try:
        result = semantic_router.run(prompt)
        if isinstance(result, dict):
            route_target = result.get("route", "general_handler")
            return [route_target]
        return ["general_handler"]
    except Exception as e:
        return [f"router_error: {str(e)}"]

@mcp.tool
def run(expert: str, prompt: str) -> str:
    try:
        expert_instance = expert_registry.load_expert(expert)
        return str(expert_instance.run(prompt))
    except Exception:
        try:
            expert_def = get_expert(expert)
            return expert_def.build_prompt(prompt)
        except Exception as e:
            return f"expert_error: {str(e)}"

@mcp.tool
def list_experts() -> list[str]:
    try:
        registry_list = list(expert_registry.list_available_experts())
        from zenrube.experts_module import list_experts as core_list
        core = list(core_list())
        return sorted(set(registry_list + core))
    except Exception as e:
        return [f"list_error: {str(e)}"]

# FastMCP export
app = mcp.app
