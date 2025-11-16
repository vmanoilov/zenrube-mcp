# server.py
import os
from fastmcp import FastMCP
from zenrube.experts.semantic_router import SemanticRouterExpert
from zenrube.experts_module import get_expert
from zenrube.experts.expert_registry import ExpertRegistry

mcp = FastMCP("ZenRube")

semantic_router = SemanticRouterExpert()
expert_registry = ExpertRegistry()

# ---------------------------------------------------------------------
# Filesystem MCP Tools
# ---------------------------------------------------------------------

@mcp.tool
def list_directory(path: str) -> dict:
    """List directory contents with metadata."""
    try:
        if not os.path.exists(path):
            return {"error": f"Path does not exist: {path}"}
        if not os.path.isdir(path):
            return {"error": f"Path is not a directory: {path}"}
            
        items = []
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            stat = os.stat(full_path)
            items.append({
                "name": item,
                "path": full_path,
                "is_dir": os.path.isdir(full_path),
                "size": stat.st_size,
                "mtime": stat.st_mtime
            })
        
        return {"ok": True, "path": path, "items": items}
    except Exception as e:
        return {"error": f"Failed to list directory: {str(e)}"}

@mcp.tool
def read_text_file(path: str, head: int = None, tail: int = None) -> dict:
    """Read text file content with optional line limiting."""
    try:
        if not os.path.exists(path):
            return {"error": f"File does not exist: {path}"}
        if not os.path.isfile(path):
            return {"error": f"Path is not a file: {path}"}
            
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        content_lines = lines
        if head is not None:
            content_lines = content_lines[:head]
        if tail is not None:
            content_lines = content_lines[-tail:]
            
        content = ''.join(content_lines)
        return {
            "ok": True,
            "path": path,
            "content": content,
            "lines_total": len(lines),
            "lines_returned": len(content_lines)
        }
    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}

@mcp.tool
def write_text_file(path: str, content: str, create: bool = True, overwrite: bool = False) -> dict:
    """Write text file with create and overwrite options."""
    try:
        if not overwrite and os.path.exists(path):
            return {"error": f"File already exists: {path}"}
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return {"ok": True, "path": path, "bytes_written": len(content)}
    except Exception as e:
        return {"error": f"Failed to write file: {str(e)}"}

@mcp.tool
def delete_path(path: str) -> dict:
    """Delete file or directory (recursive)."""
    try:
        if not os.path.exists(path):
            return {"error": f"Path does not exist: {path}"}
            
        if os.path.isdir(path):
            import shutil
            shutil.rmtree(path)
            return {"ok": True, "path": path, "action": "directory_deleted"}
        else:
            os.remove(path)
            return {"ok": True, "path": path, "action": "file_deleted"}
    except Exception as e:
        return {"error": f"Failed to delete path: {str(e)}"}

@mcp.tool
def move_path(src: str, dest: str) -> dict:
    """Move/rename file or directory."""
    try:
        if not os.path.exists(src):
            return {"error": f"Source path does not exist: {src}"}
        if os.path.exists(dest):
            return {"error": f"Destination path already exists: {dest}"}
            
        # Ensure destination directory exists
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        
        os.rename(src, dest)
        return {"ok": True, "src": src, "dest": dest, "action": "moved"}
    except Exception as e:
        return {"error": f"Failed to move path: {str(e)}"}

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

@mcp.tool
def configure_llm(provider: str, model: str, api_key: str, endpoint: str = "") -> str:
    """
    Configure LLM provider settings for the LLM Connector Expert.
    
    Args:
        provider (str): LLM provider name (openai, qwen, grok, claude, gemini)
        model (str): Model name to use
        api_key (str): API key for the provider
        endpoint (str, optional): Custom API endpoint URL
        
    Returns:
        str: Success or error message
    """
    try:
        from zenrube.config.llm_config_loader import save_llm_config
        
        config = {
            "provider": provider,
            "model": model,
            "api_key": api_key,
            "endpoint": endpoint
        }
        
        if save_llm_config(config):
            return f"LLM configuration saved successfully for provider: {provider}"
        else:
            return "Failed to save LLM configuration"
            
    except Exception as e:
        return f"Configuration error: {str(e)}"
# FastMCP export
app = mcp
