"""Tests for ChatGPT FS Agent and FilesystemClient implementation."""

import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the src directory to Python path for imports
src_dir = os.path.join(os.path.dirname(__file__), '..', '..')
import sys
sys.path.insert(0, os.path.abspath(src_dir))

from zenrube.experts.chatgpt_fs_agent import (
    MCPFilesystemClient,
    ChatGPTFsAgent,
    FsTask,
)


class TestMCPFilesystemClient:
    """Test the MCPFilesystemClient implementation."""

    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.client = MCPFilesystemClient()
        
        # Create test files and directories
        self.test_dir = os.path.join(self.temp_dir, "test")
        os.makedirs(self.test_dir)
        
        self.test_file = os.path.join(self.test_dir, "test.txt")
        with open(self.test_file, 'w') as f:
            f.write("Hello World\nLine 2\nLine 3\n")
        
        self.nested_dir = os.path.join(self.test_dir, "nested")
        os.makedirs(self.nested_dir)
        self.nested_file = os.path.join(self.nested_dir, "nested.txt")
        with open(self.nested_file, 'w') as f:
            f.write("Nested file content\n")

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_list_directory(self):
        """Test list_directory functionality."""
        result = self.client.list_directory(self.test_dir)
        
        assert result["ok"] is True
        assert "items" in result
        assert len(result["items"]) == 2  # test.txt, nested/ (direct children only)
        
        # Check that we have both file and directory
        items = {item["name"]: item for item in result["items"]}
        assert "test.txt" in items
        assert "nested" in items
        assert items["test.txt"]["is_dir"] is False
        assert items["nested"]["is_dir"] is True

    def test_list_directory_nonexistent(self):
        """Test list_directory with non-existent path."""
        result = self.client.list_directory("/nonexistent/path")
        
        assert "error" in result
        assert "does not exist" in result["error"]

    def test_read_text_file(self):
        """Test read_text_file functionality."""
        result = self.client.read_text_file(self.test_file)
        
        assert result["ok"] is True
        assert "content" in result
        assert "Hello World" in result["content"]
        assert result["lines_returned"] == 3
        assert result["lines_total"] == 3

    def test_read_text_file_with_head(self):
        """Test read_text_file with head parameter."""
        result = self.client.read_text_file(self.test_file, head=2)
        
        assert result["ok"] is True
        assert result["lines_returned"] == 2
        assert "Line 3" not in result["content"]

    def test_read_text_file_with_tail(self):
        """Test read_text_file with tail parameter."""
        result = self.client.read_text_file(self.test_file, tail=2)
        
        assert result["ok"] is True
        assert result["lines_returned"] == 2
        assert "Hello World" not in result["content"]

    def test_read_text_file_nonexistent(self):
        """Test read_text_file with non-existent file."""
        result = self.client.read_text_file("/nonexistent/file.txt")
        
        assert "error" in result
        assert "does not exist" in result["error"]

    def test_write_text_file_new(self):
        """Test write_text_file creating new file."""
        new_file = os.path.join(self.temp_dir, "new_file.txt")
        content = "New file content"
        
        result = self.client.write_text_file(new_file, content)
        
        assert result["ok"] is True
        assert result["bytes_written"] == len(content)
        
        # Verify file was created
        assert os.path.exists(new_file)
        with open(new_file, 'r') as f:
            assert f.read() == content

    def test_write_text_file_overwrite_false(self):
        """Test write_text_file with overwrite=False on existing file."""
        result = self.client.write_text_file(self.test_file, "new content", overwrite=False)
        
        assert "error" in result
        assert "already exists" in result["error"]

    def test_write_text_file_overwrite_true(self):
        """Test write_text_file with overwrite=True."""
        new_content = "Overwritten content"
        
        result = self.client.write_text_file(self.test_file, new_content, overwrite=True)
        
        assert result["ok"] is True
        assert result["bytes_written"] == len(new_content)
        
        with open(self.test_file, 'r') as f:
            assert f.read() == new_content

    def test_write_text_file_creates_directory(self):
        """Test write_text_file creates parent directories."""
        new_file = os.path.join(self.temp_dir, "new", "nested", "file.txt")
        content = "Content in nested directory"
        
        result = self.client.write_text_file(new_file, content)
        
        assert result["ok"] is True
        assert os.path.exists(new_file)

    def test_delete_path_file(self):
        """Test delete_path for file deletion."""
        result = self.client.delete_path(self.test_file)
        
        assert result["ok"] is True
        assert result["action"] == "file_deleted"
        assert not os.path.exists(self.test_file)

    def test_delete_path_directory(self):
        """Test delete_path for directory deletion."""
        result = self.client.delete_path(self.nested_dir)
        
        assert result["ok"] is True
        assert result["action"] == "directory_deleted"
        assert not os.path.exists(self.nested_dir)

    def test_delete_path_nonexistent(self):
        """Test delete_path with non-existent path."""
        result = self.client.delete_path("/nonexistent/path")
        
        assert "error" in result
        assert "does not exist" in result["error"]

    def test_move_path_file(self):
        """Test move_path for file movement."""
        dest = os.path.join(self.temp_dir, "moved_file.txt")
        
        result = self.client.move_path(self.test_file, dest)
        
        assert result["ok"] is True
        assert result["action"] == "moved"
        assert not os.path.exists(self.test_file)
        assert os.path.exists(dest)

    def test_move_path_directory(self):
        """Test move_path for directory movement."""
        dest = os.path.join(self.temp_dir, "moved_nested")
        
        result = self.client.move_path(self.nested_dir, dest)
        
        assert result["ok"] is True
        assert not os.path.exists(self.nested_dir)
        assert os.path.exists(dest)

    def test_move_path_dest_exists(self):
        """Test move_path when destination already exists."""
        dest = os.path.join(self.temp_dir, "existing_file.txt")
        
        # Create destination file
        with open(dest, 'w') as f:
            f.write("Existing content")
        
        result = self.client.move_path(self.test_file, dest)
        
        assert "error" in result
        assert "already exists" in result["error"]

    def test_move_path_nonexistent_src(self):
        """Test move_path with non-existent source."""
        result = self.client.move_path("/nonexistent/src", "/dest")
        
        assert "error" in result
        assert "does not exist" in result["error"]


class TestChatGPTFsAgent:
    """Test the ChatGPTFsAgent with safety features."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.client = MCPFilesystemClient()
        self.agent = ChatGPTFsAgent(
            client=self.client,
            root=self.temp_dir,
            allow_delete=False,
            allow_move=True,
        )
        
        # Create test file
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        with open(self.test_file, 'w') as f:
            f.write("Test content")

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_normalize_path_relative(self):
        """Test path normalization for relative paths."""
        safe_path = self.agent._normalize_path("test.txt")
        expected = os.path.join(self.temp_dir, "test.txt")
        assert safe_path == expected

    def test_normalize_path_absolute(self):
        """Test path normalization for absolute paths."""
        safe_path = self.agent._normalize_path(self.test_file)
        assert safe_path == self.test_file

    def test_normalize_path_parent_traversal_blocked(self):
        """Test that parent directory traversal is blocked."""
        with pytest.raises(ValueError, match="Unsafe path blocked"):
            self.agent._normalize_path("../etc/passwd")

    def test_normalize_path_outside_root_blocked(self):
        """Test that paths outside root are blocked."""
        with pytest.raises(ValueError, match="Path escapes root sandbox"):
            self.agent._normalize_path("/etc/passwd")

    def test_check_op_allowed_delete_disabled(self):
        """Test that delete operations are blocked when disabled."""
        task = FsTask(op="delete", path="test.txt")
        
        with pytest.raises(PermissionError, match="Delete operations are disabled"):
            self.agent._check_op_allowed(task)

    def test_check_op_allowed_delete_enabled(self):
        """Test that delete operations work when enabled."""
        agent_with_delete = ChatGPTFsAgent(
            client=self.client,
            root=self.temp_dir,
            allow_delete=True,
            allow_move=True,
        )
        
        task = FsTask(op="delete", path="test.txt")
        agent_with_delete._check_op_allowed(task)  # Should not raise

    def test_check_op_allowed_move_disabled(self):
        """Test that move operations are blocked when disabled."""
        task = FsTask(op="move", path="test.txt", dest_path="dest.txt")
        
        agent_no_move = ChatGPTFsAgent(
            client=self.client,
            root=self.temp_dir,
            allow_delete=True,
            allow_move=False,
        )
        
        with pytest.raises(PermissionError, match="Move operations are disabled"):
            agent_no_move._check_op_allowed(task)

    def test_execute_task_list(self):
        """Test executing a list operation."""
        task_dict = {"op": "list", "path": "."}
        
        result = self.agent.execute_task(FsTask.from_dict(task_dict))
        
        assert result["ok"] is True
        assert result["op"] == "list"
        assert "result" in result
        assert "items" in result["result"]

    def test_execute_task_read(self):
        """Test executing a read operation."""
        task_dict = {"op": "read", "path": "test.txt"}
        
        result = self.agent.execute_task(FsTask.from_dict(task_dict))
        
        assert result["ok"] is True
        assert result["op"] == "read"
        assert "Test content" in result["result"]["content"]

    def test_execute_task_write(self):
        """Test executing a write operation."""
        new_file = "new_file.txt"
        content = "New file content"
        task_dict = {
            "op": "write",
            "path": new_file,
            "content": content,
        }
        
        result = self.agent.execute_task(FsTask.from_dict(task_dict))
        
        assert result["ok"] is True
        assert result["op"] == "write"
        
        # Verify file was created
        expected_path = os.path.join(self.temp_dir, new_file)
        assert os.path.exists(expected_path)
        with open(expected_path, 'r') as f:
            assert f.read() == content

    def test_execute_task_move(self):
        """Test executing a move operation."""
        # Create a source file
        src_file = "src_file.txt"
        with open(os.path.join(self.temp_dir, src_file), 'w') as f:
            f.write("Source content")
        
        dest_file = "dest_file.txt"
        task_dict = {
            "op": "move",
            "path": src_file,
            "dest_path": dest_file,
        }
        
        result = self.agent.execute_task(FsTask.from_dict(task_dict))
        
        assert result["ok"] is True
        assert result["op"] == "move"
        
        # Verify move worked
        src_path = os.path.join(self.temp_dir, src_file)
        dest_path = os.path.join(self.temp_dir, dest_file)
        assert not os.path.exists(src_path)
        assert os.path.exists(dest_path)

    def test_handle_plan_success(self):
        """Test executing a successful plan."""
        tasks = [
            {"op": "read", "path": "test.txt"},
            {"op": "write", "path": "new_file.txt", "content": "New content"},
        ]
        
        result = self.agent.handle_plan(tasks)
        
        assert result["ok"] is True
        assert len(result["tasks"]) == 2
        assert len(result["errors"]) == 0
        assert result["tasks"][0]["ok"] is True
        assert result["tasks"][1]["ok"] is True

    def test_handle_plan_with_errors(self):
        """Test executing a plan with some failures."""
        tasks = [
            {"op": "read", "path": "test.txt"},  # This should succeed
            {"op": "read", "path": "nonexistent.txt"},  # This should fail
        ]
        
        result = self.agent.handle_plan(tasks)
        
        assert result["ok"] is False  # Some tasks failed
        assert len(result["tasks"]) == 1  # Only successful tasks
        assert len(result["errors"]) == 1  # One failed task
        assert "does not exist" in result["errors"][0]["message"]
        assert result["tasks"][0]["ok"] is True  # First task succeeded
        assert result["errors"][0]["task"]["path"] == "nonexistent.txt"  # Second task failed

    def test_handle_plan_with_plan_meta(self):
        """Test plan execution with metadata."""
        tasks = [{"op": "read", "path": "test.txt"}]
        plan_meta = {"user": "test_user", "source": "chatgpt"}
        
        result = self.agent.handle_plan(tasks, plan_meta)
        
        assert result["meta"] == plan_meta

    def test_handle_plan_delete_blocked(self):
        """Test that delete operations are blocked in safe mode."""
        tasks = [{"op": "delete", "path": "test.txt"}]
        
        result = self.agent.handle_plan(tasks)
        
        assert result["ok"] is False
        assert len(result["errors"]) == 1
        assert "Delete operations are disabled" in result["errors"][0]["message"]

    def test_handle_plan_safety_violation(self):
        """Test that safety violations are caught."""
        tasks = [{"op": "read", "path": "../etc/passwd"}]
        
        result = self.agent.handle_plan(tasks)
        
        assert result["ok"] is False
        assert len(result["errors"]) == 1
        assert "Unsafe path blocked" in result["errors"][0]["message"]


class TestFsTask:
    """Test the FsTask data model."""

    def test_from_dict(self):
        """Test creating FsTask from dictionary."""
        data = {
            "op": "read",
            "path": "test.txt",
            "head": 10,
            "tail": 5,
        }
        
        task = FsTask.from_dict(data)
        
        assert task.op == "read"
        assert task.path == "test.txt"
        assert task.head == 10
        assert task.tail == 5
        assert task.dest_path is None
        assert task.content is None

    def test_from_dict_minimal(self):
        """Test creating FsTask with minimal data."""
        data = {"op": "list", "path": "."}
        
        task = FsTask.from_dict(data)
        
        assert task.op == "list"
        assert task.path == "."
        assert task.dest_path is None
        assert task.content is None
        assert task.head is None
        assert task.tail is None

    def test_to_dict(self):
        """Test converting FsTask to dictionary."""
        task = FsTask(
            op="write",
            path="test.txt",
            dest_path=None,
            content="content",
            head=None,
            tail=None,
        )
        
        result = task.to_dict()
        
        expected = {
            "op": "write",
            "path": "test.txt",
            "content": "content",
        }
        
        assert result == expected

    def test_to_dict_with_optional_fields(self):
        """Test converting FsTask with optional fields to dictionary."""
        task = FsTask(
            op="move",
            path="src.txt",
            dest_path="dest.txt",
            content=None,
            head=5,
            tail=10,
        )
        
        result = task.to_dict()
        
        expected = {
            "op": "move",
            "path": "src.txt",
            "dest_path": "dest.txt",
            "head": 5,
            "tail": 10,
        }
        
        assert result == expected