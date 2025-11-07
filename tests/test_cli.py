"""
Test suite for Zenrube CLI Control Plane module.

This test file validates the complete functionality of the CLI tool including
all subcommands, expert execution, error handling, and output verification.

Author: vladinc@gmail.com
"""

import pytest
import sys
import os
import json
import tempfile
from unittest.mock import Mock, patch, mock_open
from io import StringIO

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zenrube.cli import (
    CLI_METADATA, 
    list_experts, 
    run_expert, 
    autopublish, 
    view_changelog, 
    show_versions, 
    main
)


class TestZenrubeCLI:
    """Test class for Zenrube CLI functionality."""

    def test_list_command_displays_experts(self, capsys):
        """Test that list command displays all experts with metadata."""
        # Mock ExpertRegistry to return known experts
        mock_experts = {
            'test_expert1': 'zenrube.experts.test_expert1',
            'test_expert2': 'zenrube.experts.test_expert2'
        }
        mock_expert_info_map = {
            'test_expert1': {
                'name': 'test_expert1',
                'version': '1.0.0',
                'description': 'Test expert 1 description',
                'author': 'test1@example.com'
            },
            'test_expert2': {
                'name': 'test_expert2',
                'version': '2.0.0',
                'description': 'Test expert 2 description',
                'author': 'test2@example.com'
            }
        }
        
        with patch('zenrube.cli.ExpertRegistry') as mock_registry_class:
            mock_registry = Mock()
            mock_registry.discover_experts.return_value = mock_experts
            
            def get_expert_info_side_effect(name):
                return mock_expert_info_map.get(name)
            
            mock_registry.get_expert_info.side_effect = get_expert_info_side_effect
            mock_registry_class.return_value = mock_registry
            
            # Run the list command
            list_experts()
            
            # Capture output
            captured = capsys.readouterr()
            
            # Verify output contains expected content
            assert 'Available Experts' in captured.out
            assert 'test_expert1' in captured.out
            assert 'test_expert2' in captured.out
            assert '1.0.0' in captured.out
            assert '2.0.0' in captured.out
            assert 'Test expert 1 description' in captured.out
            assert 'Test expert 2 description' in captured.out
            assert 'test1@example.com' in captured.out
            assert 'test2@example.com' in captured.out

    def test_run_command_executes_expert(self, capsys):
        """Test that run command executes expert and prints output."""
        # Mock ExpertRegistry
        with patch('zenrube.cli.ExpertRegistry') as mock_registry_class:
            mock_registry = Mock()
            mock_expert_instance = Mock()
            mock_expert_instance.run.return_value = "cleaned text"
            mock_registry.load_expert.return_value = mock_expert_instance
            mock_registry_class.return_value = mock_registry
            
            # Run the run command
            run_expert("data_cleaner", " messy text ")
            
            # Capture output
            captured = capsys.readouterr()
            
            # Verify expert was loaded and executed
            mock_registry.load_expert.assert_called_once_with("data_cleaner")
            mock_expert_instance.run.assert_called_once_with(" messy text ")
            
            # Verify output contains expected content
            assert "Running expert 'data_cleaner'" in captured.out
            assert "Input:  messy text " in captured.out
            assert "Result: cleaned text" in captured.out

    def test_run_command_invalid_expert(self, capsys):
        """Test that run command handles non-existent expert gracefully."""
        # Mock ExpertRegistry to raise ModuleNotFoundError
        with patch('zenrube.cli.ExpertRegistry') as mock_registry_class:
            mock_registry = Mock()
            mock_registry.load_expert.side_effect = ModuleNotFoundError("Expert 'nonexistent' not found")
            mock_registry_class.return_value = mock_registry
            
            # Run the run command and expect SystemExit
            with pytest.raises(SystemExit) as exc_info:
                run_expert("nonexistent", "test input")
            
            # Verify exit code is 1 (error)
            assert exc_info.value.code == 1
            
            # Capture output
            captured = capsys.readouterr()
            
            # Verify error message is printed
            assert "Expert 'nonexistent' not found" in captured.out

    def test_autopublish_command_triggers_workflow(self, capsys):
        """Test that autopublish command calls AutoPublisherExpert and prints results."""
        # Mock AutoPublisherExpert
        with patch('zenrube.cli.AutoPublisherExpert') as mock_autopublisher_class:
            mock_autopublisher = Mock()
            mock_response = {
                'status': 'success',
                'manifest_id': 'test_manifest_123',
                'experts_published': 5
            }
            mock_autopublisher.run_autopublish.return_value = mock_response
            mock_autopublisher_class.return_value = mock_autopublisher
            
            # Run the autopublish command
            autopublish()
            
            # Capture output
            captured = capsys.readouterr()
            
            # Verify AutoPublisherExpert was called
            mock_autopublisher.run_autopublish.assert_called_once()
            
            # Verify output contains expected content
            assert "Starting automated publishing workflow" in captured.out
            assert "Publication Results:" in captured.out
            assert "Status: success" in captured.out
            assert "Manifest ID: test_manifest_123" in captured.out
            assert "Experts Published: 5" in captured.out

    def test_changelog_command_prints_entries(self, capsys):
        """Test that changelog command prints entries from changelog file."""
        # Create test changelog data
        test_changelog = [
            {
                "timestamp": "2025-11-07T10:00:00.000Z",
                "expert_name": "test_expert",
                "old_version": "1.0.0",
                "new_version": "1.1.0",
                "change_summary": "Added new features",
                "author": "test@example.com"
            },
            {
                "timestamp": "2025-11-07T09:00:00.000Z",
                "expert_name": "another_expert",
                "old_version": "2.0.0",
                "new_version": "2.0.1",
                "change_summary": "Bug fixes",
                "author": "dev@example.com"
            }
        ]
        
        # Mock file operations
        with patch('builtins.open', mock_open(read_data=json.dumps(test_changelog))), \
             patch('zenrube.cli.os.path.exists', return_value=True):
            
            # Run the changelog command with default limit
            view_changelog()
            
            # Capture output
            captured = capsys.readouterr()
            
            # Verify output contains expected content
            assert "Recent Changelog Entries" in captured.out
            assert "test_expert" in captured.out
            assert "another_expert" in captured.out
            assert "1.0.0 → 1.1.0" in captured.out
            assert "2.0.0 → 2.0.1" in captured.out
            assert "Added new features" in captured.out
            assert "Bug fixes" in captured.out
            assert "test@example.com" in captured.out

    def test_changelog_limit_parameter(self, capsys):
        """Test that changelog command respects limit parameter."""
        # Create test changelog data (chronological order, newest last)
        test_changelog = [
            {
                "timestamp": "2025-11-07T08:00:00.000Z",
                "expert_name": "expert3",
                "old_version": "3.0.0",
                "new_version": "3.1.0",
                "change_summary": "Update 3",
                "author": "test@example.com"
            },
            {
                "timestamp": "2025-11-07T09:00:00.000Z",
                "expert_name": "expert2",
                "old_version": "2.0.0",
                "new_version": "2.1.0",
                "change_summary": "Update 2",
                "author": "test@example.com"
            },
            {
                "timestamp": "2025-11-07T10:00:00.000Z",
                "expert_name": "expert1",
                "old_version": "1.0.0",
                "new_version": "1.1.0",
                "change_summary": "Update 1",
                "author": "test@example.com"
            }
        ]
        
        # Mock file operations
        with patch('builtins.open', mock_open(read_data=json.dumps(test_changelog))), \
             patch('zenrube.cli.os.path.exists', return_value=True):
            
            # Run the changelog command with limit of 2
            view_changelog(limit=2)
            
            # Capture output
            captured = capsys.readouterr()
            
            # Verify output contains only the most recent 2 entries (expert1 and expert2)
            assert "expert1" in captured.out  # Most recent
            assert "expert2" in captured.out  # Second most recent
            assert "expert3" not in captured.out  # Should not appear
            assert "(2 of 3 total)" in captured.out

    def test_version_command_displays_versions(self, capsys):
        """Test that version command displays framework and expert versions."""
        # Mock ExpertRegistry
        mock_experts = {
            'test_expert1': 'zenrube.experts.test_expert1',
            'test_expert2': 'zenrube.experts.test_expert2'
        }
        mock_expert_info_map = {
            'test_expert1': {
                'name': 'test_expert1',
                'version': '1.5.0',
                'description': 'Test expert 1',
                'author': 'test1@example.com'
            },
            'test_expert2': {
                'name': 'test_expert2',
                'version': '2.5.0',
                'description': 'Test expert 2',
                'author': 'test2@example.com'
            }
        }
        
        with patch('zenrube.cli.ExpertRegistry') as mock_registry_class:
            mock_registry = Mock()
            mock_registry.discover_experts.return_value = mock_experts
            
            def get_expert_info_side_effect(name):
                return mock_expert_info_map.get(name)
            
            mock_registry.get_expert_info.side_effect = get_expert_info_side_effect
            mock_registry_class.return_value = mock_registry
            
            # Run the version command
            show_versions()
            
            # Capture output
            captured = capsys.readouterr()
            
            # Verify output contains expected content
            assert f"Zenrube CLI v{CLI_METADATA['version']}" in captured.out
            assert "Expert Versions:" in captured.out
            assert "test_expert1: v1.5.0" in captured.out
            assert "test_expert2: v2.5.0" in captured.out

    def test_invalid_command_shows_help(self, capsys):
        """Test that unknown subcommand shows help and returns exit code 2."""
        # Mock sys.argv for the test
        with patch.object(sys, 'argv', ['zenrube-cli', 'invalid_command']):
            # Run main function and expect SystemExit
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # Verify exit code is 2 (argparse error)
            assert exc_info.value.code == 2
            
            # Capture output
            captured = capsys.readouterr()
            
            # Verify help message is shown (argparse errors go to stderr)
            assert "usage:" in captured.err
            assert "invalid choice" in captured.err
            assert "{list,run,autopublish,changelog,version}" in captured.err

    def test_cli_metadata_contains_required_keys(self):
        """Test that CLI_METADATA contains all required keys."""
        required_keys = ['name', 'version', 'description', 'author']
        
        for key in required_keys:
            assert key in CLI_METADATA, f"Missing required key: {key}"
        
        # Verify values are non-empty strings
        assert isinstance(CLI_METADATA['name'], str)
        assert isinstance(CLI_METADATA['version'], str)
        assert isinstance(CLI_METADATA['description'], str)
        assert isinstance(CLI_METADATA['author'], str)
        
        # Verify expected values
        assert CLI_METADATA['name'] == 'zenrube'
        assert CLI_METADATA['version'] == '1.0'
        assert 'managing and publishing Zenrube experts' in CLI_METADATA['description']
        assert CLI_METADATA['author'] == 'vladinc@gmail.com'

    def test_missing_changelog_file_handled_gracefully(self, capsys):
        """Test that missing changelog file is handled gracefully."""
        # Mock os.path.exists to return False (file doesn't exist)
        with patch('zenrube.cli.os.path.exists', return_value=False):
            # Run the changelog command
            view_changelog()
            
            # Capture output
            captured = capsys.readouterr()
            
            # Verify graceful warning message is shown
            assert "Changelog file not found" in captured.out
            assert "No changes have been recorded yet" in captured.out

    def test_run_command_with_dict_result(self, capsys):
        """Test that run command formats dict results properly."""
        # Mock ExpertRegistry
        with patch('zenrube.cli.ExpertRegistry') as mock_registry_class:
            mock_registry = Mock()
            mock_expert_instance = Mock()
            mock_expert_instance.run.return_value = {"key1": "value1", "key2": "value2"}
            mock_registry.load_expert.return_value = mock_expert_instance
            mock_registry_class.return_value = mock_registry
            
            # Run the run command
            run_expert("test_expert", "test input")
            
            # Capture output
            captured = capsys.readouterr()
            
            # Verify dict formatting
            assert "Result (dict):" in captured.out
            assert "key1: value1" in captured.out
            assert "key2: value2" in captured.out

    def test_run_command_with_list_result(self, capsys):
        """Test that run command formats list results properly."""
        # Mock ExpertRegistry
        with patch('zenrube.cli.ExpertRegistry') as mock_registry_class:
            mock_registry = Mock()
            mock_expert_instance = Mock()
            mock_expert_instance.run.return_value = ["item1", "item2", "item3"]
            mock_registry.load_expert.return_value = mock_expert_instance
            mock_registry_class.return_value = mock_registry
            
            # Run the run command
            run_expert("test_expert", "test input")
            
            # Capture output
            captured = capsys.readouterr()
            
            # Verify list formatting
            assert "Result (list):" in captured.out
            assert "0: item1" in captured.out
            assert "1: item2" in captured.out
            assert "2: item3" in captured.out

    def test_autopublish_with_skipped_status(self, capsys):
        """Test autopublish command with skipped status."""
        # Mock AutoPublisherExpert
        with patch('zenrube.cli.AutoPublisherExpert') as mock_autopublisher_class:
            mock_autopublisher = Mock()
            mock_response = {
                'status': 'skipped',
                'message': 'No version updates detected - publication skipped'
            }
            mock_autopublisher.run_autopublish.return_value = mock_response
            mock_autopublisher_class.return_value = mock_autopublisher
            
            # Run the autopublish command
            autopublish()
            
            # Capture output
            captured = capsys.readouterr()
            
            # Verify skipped status handling
            assert "Status: skipped" in captured.out
            assert "No version updates detected" in captured.out

    def test_main_function_help_option(self, capsys):
        """Test that main function handles --help option correctly."""
        # Mock sys.argv with help option
        with patch.object(sys, 'argv', ['zenrube-cli', '--help']):
            # Run main function and expect SystemExit with code 0
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # Verify exit code is 0 (help shown successfully)
            assert exc_info.value.code == 0
            
            # Capture output
            captured = capsys.readouterr()
            
            # Verify help content is shown
            assert "usage:" in captured.out
            assert "Command-line interface for managing and publishing Zenrube experts" in captured.out

    def test_main_function_version_option(self, capsys):
        """Test that main function handles --version option correctly."""
        # Mock sys.argv with version option
        with patch.object(sys, 'argv', ['zenrube-cli', '--version']):
            # Run main function and expect SystemExit with code 0
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # Verify exit code is 0 (version shown successfully)
            assert exc_info.value.code == 0
            
            # Capture output
            captured = capsys.readouterr()
            
            # Verify version is shown
            assert f"zenrube v{CLI_METADATA['version']}" in captured.out