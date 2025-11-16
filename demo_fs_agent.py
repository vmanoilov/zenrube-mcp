#!/usr/bin/env python3
"""
Demonstration of ChatGPT FS Agent with MCP FilesystemClient integration.

This script shows how to use the FilesystemClient with the ChatGPTFSAgent
to safely execute filesystem operations.
"""

import os
import sys
import tempfile

# Add the src directory to Python path
src_dir = os.path.join(os.path.dirname(__file__))
sys.path.insert(0, src_dir)

from zenrube.experts.chatgpt_fs_agent import MCPFilesystemClient, ChatGPTFsAgent


def demo_chatgpt_fs_agent():
    """Demonstrate the ChatGPT FS Agent functionality."""
    
    # Create a temporary directory for our demo
    demo_root = tempfile.mkdtemp(prefix="chatgpt_fs_demo_")
    print(f"Demo directory: {demo_root}")
    
    try:
        # Create the filesystem client
        client = MCPFilesystemClient()
        
        # Create the agent with safety settings
        agent = ChatGPTFsAgent(
            client=client,
            root=demo_root,
            allow_delete=False,  # Safe mode - no deletes
            allow_move=True,     # Allow moves
        )
        
        print("\n=== ChatGPT FS Agent Demonstration ===\n")
        
        # Demo 1: Read and List operations
        print("1. Creating and reading files...")
        
        # ChatGPT-like task list
        tasks = [
            {
                "op": "write",
                "path": "zenrube/profiles/personality_presets.py",
                "content": "# ZenRube Personality Presets\nclass Persona:\n    def __init__(self):\n        self.traits = []\n"
            },
            {
                "op": "write", 
                "path": "notes/fs_agent.md",
                "content": "# ChatGPT FS Agent Notes\nThis demonstrates safe filesystem operations.\n"
            },
            {
                "op": "list",
                "path": "."
            }
        ]
        
        # Execute the plan
        result = agent.handle_plan(tasks)
        
        print(f"Plan executed successfully: {result['ok']}")
        print(f"Tasks completed: {len(result['tasks'])}")
        print(f"Errors: {len(result['errors'])}")
        
        # Show the results
        for i, task_result in enumerate(result['tasks']):
            print(f"\nTask {i+1}: {task_result['op']}")
            if task_result['ok']:
                if task_result['op'] == 'list':
                    items = task_result['result']['items']
                    print(f"  Listed {len(items)} items:")
                    for item in items:
                        print(f"    - {item['name']} ({'dir' if item['is_dir'] else 'file'})")
                elif task_result['op'] == 'write':
                    print(f"  Written to: {task_result['path']}")
            else:
                print(f"  Failed: {task_result.get('error', 'Unknown error')}")
        
        # Demo 2: Error handling and safety
        print("\n2. Testing safety and error handling...")
        
        unsafe_tasks = [
            {
                "op": "read",
                "path": "../etc/passwd"  # This should be blocked
            }
        ]
        
        unsafe_result = agent.handle_plan(unsafe_tasks)
        print(f"Unsafe path blocked: {not unsafe_result['ok']}")
        if unsafe_result['errors']:
            print(f"Safety error: {unsafe_result['errors'][0]['message']}")
        
        # Demo 3: Partial success with detailed results
        print("\n3. Testing partial success scenario...")
        
        mixed_tasks = [
            {
                "op": "read",
                "path": "zenrube/profiles/personality_presets.py"  # Should succeed
            },
            {
                "op": "read", 
                "path": "nonexistent_file.txt"  # Should fail
            },
            {
                "op": "write",
                "path": "output/result.json",
                "content": '{"status": "completed", "tasks": 3}'
            }
        ]
        
        mixed_result = agent.handle_plan(mixed_tasks)
        print(f"Mixed plan ok: {mixed_result['ok']}")
        print(f"Successful tasks: {len(mixed_result['tasks'])}")
        print(f"Errors: {len(mixed_result['errors'])}")
        
        # Show error details
        for error in mixed_result['errors']:
            print(f"  Error in {error['task']['op']}: {error['message']}")
        
        print("\n=== Demo Complete ===")
        
    finally:
        # Clean up
        import shutil
        shutil.rmtree(demo_root)
        print(f"Cleaned up demo directory")


def demo_filesystem_client_direct():
    """Demonstrate the FilesystemClient directly."""
    
    demo_root = tempfile.mkdtemp(prefix="fs_client_demo_")
    print(f"\nDirect FilesystemClient demo in: {demo_root}")
    
    try:
        client = MCPFilesystemClient()
        
        # Test all filesystem operations
        print("\n=== Direct FilesystemClient Test ===\n")
        
        # Create test files
        test_file = os.path.join(demo_root, "test.txt")
        nested_dir = os.path.join(demo_root, "nested")
        
        with open(test_file, 'w') as f:
            f.write("Line 1\nLine 2\nLine 3\n")
        os.makedirs(nested_dir)
        
        # Test list_directory
        print("1. List directory:")
        result = client.list_directory(demo_root)
        if result['ok']:
            for item in result['items']:
                print(f"  {item['name']}: {item['size']} bytes")
        
        # Test read_text_file with options
        print("\n2. Read file with head/tail:")
        result = client.read_text_file(test_file, head=2)
        if result['ok']:
            print(f"First 2 lines: {result['lines_returned']} lines")
        
        # Test write_text_file
        print("\n3. Write new file:")
        new_file = os.path.join(demo_root, "new_file.txt")
        result = client.write_text_file(new_file, "New content here")
        if result['ok']:
            print(f"Written {result['bytes_written']} bytes")
        
        # Test move_path
        print("\n4. Move file:")
        dest = os.path.join(demo_root, "moved_file.txt")
        result = client.move_path(test_file, dest)
        if result['ok']:
            print(f"Moved to {dest}")
        
        print("\n=== Direct Demo Complete ===")
        
    finally:
        import shutil
        shutil.rmtree(demo_root)
        print("Cleaned up direct demo directory")


if __name__ == "__main__":
    print("ChatGPT FS Agent with MCP FilesystemClient Integration Demo")
    print("=" * 60)
    
    demo_chatgpt_fs_agent()
    demo_filesystem_client_direct()
    
    print("\nAll demonstrations completed successfully!")