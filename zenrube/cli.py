"""
Zenrube CLI Control Plane

This module provides a comprehensive command-line interface for managing and publishing
Zenrube experts. It serves as the central hub for interacting with the expert system,
including discovery, execution, publishing, and version management.

Author: vladinc@gmail.com
"""

import argparse
import json
import os
import sys
import importlib
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import required modules
import sys
import os

# Add the src directory to Python path for imports
src_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.abspath(src_dir))

from zenrube.experts.expert_registry import ExpertRegistry
from zenrube.experts.autopublisher import AutoPublisherExpert
from zenrube.experts.version_manager import VersionManagerExpert


# CLI metadata
CLI_METADATA = {
    "name": "zenrube",
    "version": "1.0",
    "description": "Command-line interface for managing and publishing Zenrube experts.",
    "author": "vladinc@gmail.com"
}


def list_experts() -> None:
    """
    Display all available experts discovered by ExpertRegistry.
    
    Lists all discovered experts with their names, descriptions, and versions
    in a human-readable format.
    """
    try:
        registry = ExpertRegistry()
        discovered_experts = registry.discover_experts()
        
        if not discovered_experts:
            print("No experts found.")
            return
        
        print(f"Available Experts ({len(discovered_experts)}):")
        print("-" * 60)
        
        for expert_name in sorted(discovered_experts.keys()):
            expert_info = registry.get_expert_info(expert_name)
            if expert_info:
                print(f"• {expert_info['name']}")
                print(f"  Version: {expert_info['version']}")
                print(f"  Description: {expert_info['description']}")
                print(f"  Author: {expert_info['author']}")
                print()
            else:
                print(f"• {expert_name} (info unavailable)")
                print()
                
    except Exception as e:
        print(f"Error listing experts: {e}")
        sys.exit(1)


def run_expert(expert_name: str, input_data: str) -> None:
    """
    Execute a specific expert with input data.
    
    Dynamically loads and runs the specified expert using its run() method.
    Handles different expert types and formats output appropriately.
    
    Args:
        expert_name: Name of the expert to run
        input_data: Input data to pass to the expert
    """
    try:
        registry = ExpertRegistry()
        expert_instance = registry.load_expert(expert_name)
        
        print(f"Running expert '{expert_name}'...")
        print(f"Input: {input_data}")
        print("-" * 40)
        
        # Run the expert
        result = expert_instance.run(input_data)
        
        # Format and display the result based on type
        if isinstance(result, dict):
            print("Result (dict):")
            for key, value in result.items():
                print(f"  {key}: {value}")
        elif isinstance(result, list):
            print("Result (list):")
            for i, item in enumerate(result):
                print(f"  {i}: {item}")
        else:
            print(f"Result: {result}")
            
    except ModuleNotFoundError as e:
        print(f"Expert '{expert_name}' not found: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running expert '{expert_name}': {e}")
        sys.exit(1)


def autopublish() -> None:
    """
    Trigger AutoPublisherExpert.run_autopublish().
    
    Executes the automated publishing workflow and displays a summary
    of the publication results.
    """
    try:
        print("Starting automated publishing workflow...")
        autopublisher = AutoPublisherExpert()
        result = autopublisher.run_autopublish()
        
        print("Publication Results:")
        print("-" * 40)
        
        if result.get('status') == 'skipped':
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
        elif result.get('status') == 'success':
            print(f"Status: {result['status']}")
            print(f"Manifest ID: {result.get('manifest_id', 'N/A')}")
            print(f"Experts Published: {result.get('experts_published', 0)}")
            if 'message' in result:
                print(f"Message: {result['message']}")
        else:
            print(f"Status: {result.get('status', 'unknown')}")
            if 'message' in result:
                print(f"Message: {result['message']}")
                
    except Exception as e:
        print(f"Error during autopublish: {e}")
        sys.exit(1)


def view_changelog(limit: int = 10) -> None:
    """
    View recent changelog entries.
    
    Reads ./zenrube_changelog.json and displays recent entries with
    timestamps, expert names, versions, and change summaries.
    
    Args:
        limit: Maximum number of entries to display (default: 10)
    """
    changelog_file = "./zenrube_changelog.json"
    
    if not os.path.exists(changelog_file):
        print("Changelog file not found. No changes have been recorded yet.")
        return
    
    try:
        with open(changelog_file, 'r', encoding='utf-8') as f:
            changelog_data = json.load(f)
        
        if not changelog_data:
            print("No changelog entries found.")
            return
        
        # Show most recent entries first
        recent_entries = changelog_data[-limit:] if len(changelog_data) > limit else changelog_data
        
        print(f"Recent Changelog Entries ({len(recent_entries)} of {len(changelog_data)} total):")
        print("-" * 80)
        
        for entry in reversed(recent_entries):  # Show most recent first
            timestamp = entry.get('timestamp', 'Unknown')
            expert_name = entry.get('expert_name', 'Unknown')
            old_version = entry.get('old_version', 'N/A')
            new_version = entry.get('new_version', 'N/A')
            change_summary = entry.get('change_summary', 'No summary')
            author = entry.get('author', 'Unknown')
            
            print(f"Timestamp: {timestamp}")
            print(f"Expert: {expert_name}")
            print(f"Version: {old_version} → {new_version}")
            print(f"Change: {change_summary}")
            print(f"Author: {author}")
            print("-" * 40)
            
    except json.JSONDecodeError as e:
        print(f"Error reading changelog file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error viewing changelog: {e}")
        sys.exit(1)


def show_versions() -> None:
    """
    Display Zenrube core and expert versions.
    
    Shows the CLI version and each expert's version from their EXPERT_METADATA.
    """
    try:
        print(f"Zenrube CLI v{CLI_METADATA['version']}")
        print("=" * 50)
        
        # Get expert versions
        registry = ExpertRegistry()
        discovered_experts = registry.discover_experts()
        
        if not discovered_experts:
            print("No experts found.")
            return
        
        print("Expert Versions:")
        print("-" * 30)
        
        for expert_name in sorted(discovered_experts.keys()):
            expert_info = registry.get_expert_info(expert_name)
            if expert_info:
                print(f"  {expert_info['name']}: v{expert_info['version']}")
            else:
                print(f"  {expert_name}: version info unavailable")
        
        # Also show Zenrube core version if available
        try:
            import zenrube
            print(f"  zenrube-core: v0.1.0")  # Assuming this is the core version
        except ImportError:
            pass  # Core version not available
            
    except Exception as e:
        print(f"Error showing versions: {e}")
        sys.exit(1)


def main() -> int:
    """
    Main CLI entry point using argparse.
    
    Sets up the argument parser with all required subcommands and
    dispatches to the appropriate handler functions.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description=CLI_METADATA['description'],
        prog='zenrube-cli'
    )
    parser.add_argument(
        '--version', 
        action='version', 
        version=f"{CLI_METADATA['name']} v{CLI_METADATA['version']}"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # list subcommand
    list_parser = subparsers.add_parser('list', help='List all available experts')
    
    # run subcommand
    run_parser = subparsers.add_parser('run', help='Run a specific expert')
    run_parser.add_argument('--expert', required=True, help='Name of the expert to run')
    run_parser.add_argument('--input', required=True, help='Input data for the expert')
    
    # autopublish subcommand
    autopublish_parser = subparsers.add_parser('autopublish', help='Run automated publishing')
    
    # changelog subcommand
    changelog_parser = subparsers.add_parser('changelog', help='View recent changelog entries')
    changelog_parser.add_argument('--limit', type=int, default=10, 
                                help='Maximum number of entries to show (default: 10)')
    
    # version subcommand
    version_parser = subparsers.add_parser('version', help='Show version information')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # Dispatch to appropriate handler
        if args.command == 'list':
            list_experts()
        elif args.command == 'run':
            run_expert(args.expert, args.input)
        elif args.command == 'autopublish':
            autopublish()
        elif args.command == 'changelog':
            view_changelog(args.limit)
        elif args.command == 'version':
            show_versions()
        else:
            print(f"Unknown command: {args.command}")
            return 1
            
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())