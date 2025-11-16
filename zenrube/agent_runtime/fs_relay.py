# zenrube/agent_runtime/fs_relay.py

from __future__ import annotations

from typing import Any, Dict

from zenrube.experts.chatgpt_fs_agent import ChatGPTFsAgent, MCPFilesystemClient


def execute_fs_plan_locally(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a filesystem plan locally using the existing ChatGPTFsAgent.
    
    This serves as a bridge between the autonomous loop and the actual
    filesystem operations, providing a consistent interface.
    
    Args:
        plan: Dictionary with "tasks" and "meta" keys, matching the FS agent format
        
    Returns:
        Execution result from the ChatGPTFsAgent
    """
    # Create a filesystem client and agent
    client = MCPFilesystemClient()
    agent = ChatGPTFsAgent(
        client=client,
        root="/workspaces/ZenRube",
        allow_delete=True,  # Allow deletes in autonomous mode
        allow_move=True,    # Allow moves
    )
    
    # Execute the plan
    return agent.handle_plan(plan["tasks"], plan_meta=plan.get("meta", {}))