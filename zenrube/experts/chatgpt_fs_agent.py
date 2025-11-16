"""
ChatGPT FS Agent

Acts as a safe proxy between high-level LLM instructions and the
filesystem MCP server. It does NOT talk to MCP directly; instead it
wraps a filesystem client that already knows how to call MCP tools.

Workflow:

1) ChatGPT produces a list of structured tasks, for example:
   [
       {"op": "read", "path": "zenrube/profiles/personality_presets.py"},
       {
           "op": "write",
           "path": "notes/fs_agent.md",
           "content": "# Notes..."
       }
   ]

2) ChatGPTFsAgent receives these tasks and executes them through a
   FilesystemClient, enforcing basic safety rules.

3) Results are returned as structured JSON that can be shown back to
   ChatGPT or logged by ZenRube.

This keeps all real file I/O local and under your control.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    Literal,
)


EXPERT_METADATA: Dict[str, Any] = {
    "name": "chatgpt_fs_agent",
    "version": 1,
    "description": (
        "Proxy agent that executes structured filesystem operations on "
        "behalf of ChatGPT using a sandboxed MCP filesystem server."
    ),
    "author": "vladinc@gmail.com",
}


# ---------------------------------------------------------------------
# Filesystem client protocol (your MCP bridge implements this)
# ---------------------------------------------------------------------


class FilesystemClient(Protocol):
    """
    Minimal protocol for the MCP filesystem bridge.

    Implement this against your MCP calls (list_directory, read_text_file,
    write_text_file, delete, move, etc.). The agent does not care *how*
    you talk to MCP, only that these methods exist.
    """

    def list_directory(self, path: str) -> Dict[str, Any]:
        ...

    def read_text_file(
        self,
        path: str,
        head: Optional[int] = None,
        tail: Optional[int] = None,
    ) -> Dict[str, Any]:
        ...

    def write_text_file(
        self,
        path: str,
        content: str,
        create: bool = True,
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        ...

    def delete_path(self, path: str) -> Dict[str, Any]:
        ...

    def move_path(self, src: str, dest: str) -> Dict[str, Any]:
        ...


# ---------------------------------------------------------------------
# Implementation of FilesystemClient that bridges to MCP tools
# ---------------------------------------------------------------------


class MCPFilesystemClient(FilesystemClient):
    """
    FilesystemClient implementation that calls the MCP filesystem tools.
    
    This implementation bridges to the MCP tools defined in server.py:
    - list_directory
    - read_text_file
    - write_text_file
    - delete_path
    - move_path
    
    In a production environment, this would make actual MCP protocol calls.
    For now, it directly implements the filesystem operations in a way
    that's compatible with the MCP tool signatures.
    """

    def list_directory(self, path: str) -> Dict[str, Any]:
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

    def read_text_file(
        self,
        path: str,
        head: Optional[int] = None,
        tail: Optional[int] = None,
    ) -> Dict[str, Any]:
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

    def write_text_file(
        self,
        path: str,
        content: str,
        create: bool = True,
        overwrite: bool = False,
    ) -> Dict[str, Any]:
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

    def delete_path(self, path: str) -> Dict[str, Any]:
        """Delete file or directory (recursive)."""
        try:
            if not os.path.exists(path):
                return {"error": f"Path does not exist: {path}"}
                
            if os.path.isdir(path):
                shutil.rmtree(path)
                return {"ok": True, "path": path, "action": "directory_deleted"}
            else:
                os.remove(path)
                return {"ok": True, "path": path, "action": "file_deleted"}
        except Exception as e:
            return {"error": f"Failed to delete path: {str(e)}"}

    def move_path(self, src: str, dest: str) -> Dict[str, Any]:
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


# ---------------------------------------------------------------------
# Task model
# ---------------------------------------------------------------------

FsOp = Literal["list", "read", "write", "delete", "move"]


@dataclass
class FsTask:
    """
    One atomic filesystem operation.

    All fields are intentionally simple so ChatGPT can generate them in
    JSON easily and you can log/inspect them.
    """

    op: FsOp
    path: str
    dest_path: Optional[str] = None
    content: Optional[str] = None
    head: Optional[int] = None
    tail: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FsTask":
        return cls(
            op=data["op"],
            path=data["path"],
            dest_path=data.get("dest_path"),
            content=data.get("content"),
            head=data.get("head"),
            tail=data.get("tail"),
        )

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "op": self.op,
            "path": self.path,
        }
        if self.dest_path is not None:
            out["dest_path"] = self.dest_path
        if self.content is not None:
            out["content"] = self.content
        if self.head is not None:
            out["head"] = self.head
        if self.tail is not None:
            out["tail"] = self.tail
        return out


# ---------------------------------------------------------------------
# Core agent
# ---------------------------------------------------------------------


class ChatGPTFsAgent:
    """
    Safe executor for structured filesystem tasks on behalf of ChatGPT.

    Responsibilities:
    - Enforce path sandboxing under a configured root directory.
    - Execute a list of FsTask operations via a FilesystemClient.
    - Return structured results with per-task status.
    - Provide a single 'handle_plan' entrypoint that can be called
      by ZenRube orchestration.

    This agent does NOT:
    - Parse natural language.
    - Call LLMs.
    - Talk directly to MCP.
    """

    def __init__(
        self,
        client: FilesystemClient,
        root: str = "/workspaces/ZenRube",
        allow_delete: bool = False,
        allow_move: bool = True,
    ) -> None:
        self._client = client
        self._root = root.rstrip("/")
        self._allow_delete = allow_delete
        self._allow_move = allow_move

    # ---------------- safety helpers ----------------

    def _normalize_path(self, path: str) -> str:
        """
        Ensure path stays inside the configured root.

        We do a simple, explicit check rather than clever path
        resolution to keep behavior transparent.
        """
        if path.startswith("/"):
            full = path
        else:
            full = f"{self._root}/{path}"

        # crude but effective: block parent traversal attempts
        if ".." in full:
            raise ValueError(f"Unsafe path blocked: {path!r}")

        if not full.startswith(self._root):
            raise ValueError(f"Path escapes root sandbox: {path!r}")

        return full

    def _check_op_allowed(self, task: FsTask) -> None:
        if task.op == "delete" and not self._allow_delete:
            raise PermissionError("Delete operations are disabled")
        if task.op == "move" and not self._allow_move:
            raise PermissionError("Move operations are disabled")

    # ---------------- execution ----------------

    def execute_task(self, task: FsTask) -> Dict[str, Any]:
        """
        Execute a single FsTask through the underlying filesystem client.
        Returns a structured result payload.
        """
        self._check_op_allowed(task)
        safe_path = self._normalize_path(task.path)

        if task.op == "list":
            result = self._client.list_directory(safe_path)
        elif task.op == "read":
            result = self._client.read_text_file(
                safe_path,
                head=task.head,
                tail=task.tail,
            )
        elif task.op == "write":
            if task.content is None:
                raise ValueError("write operation requires 'content'")
            result = self._client.write_text_file(
                safe_path,
                content=task.content,
                create=True,
                overwrite=True,
            )
        elif task.op == "delete":
            result = self._client.delete_path(safe_path)
        elif task.op == "move":
            if not task.dest_path:
                raise ValueError("move operation requires 'dest_path'")
            dest = self._normalize_path(task.dest_path)
            result = self._client.move_path(safe_path, dest)
        else:
            raise ValueError(f"Unsupported op: {task.op!r}")

        # Check if the client operation failed
        if isinstance(result, dict) and "error" in result:
            raise RuntimeError(result["error"])

        return {
            "ok": True,
            "op": task.op,
            "path": task.path,
            "result": result,
        }

    def handle_plan(
        self,
        tasks: List[Dict[str, Any]],
        plan_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a list of filesystem tasks.

        Parameters:
            tasks: list of dicts that can be turned into FsTask
            plan_meta: optional metadata from ChatGPT
                       (for logging, traceability)

        Returns:
            {
              "ok": bool,
              "tasks": [... per-task results ...],
              "errors": [...],
              "meta": {...},
            }
        """
        results: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        for raw in tasks:
            try:
                task = FsTask.from_dict(raw)
                res = self.execute_task(task)
                results.append(res)
            except Exception as exc:  # noqa: BLE001
                errors.append(
                    {
                        "task": raw,
                        "error": type(exc).__name__,
                        "message": str(exc),
                    }
                )

        ok = len(errors) == 0

        return {
            "ok": ok,
            "tasks": results,
            "errors": errors,
            "meta": plan_meta or {},
        }