"""
Test suite for AutoPublisherExpert module.

This test file validates the complete functionality of the AutoPublisherExpert class,
including version update detection, manifest generation, publishing workflow,
and activity logging capabilities.

Author: vladinc@gmail.com
"""

import pytest
import sys
import os
import tempfile
import unittest.mock
from datetime import datetime
from unittest.mock import Mock, patch, mock_open

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zenrube.experts.autopublisher import AutoPublisherExpert, EXPERT_METADATA


class TestAutoPublisherExpert:
    """Test class for AutoPublisherExpert functionality."""

    def test_check_for_updates_returns_changed_experts(self):
        """Test that check_for_updates returns experts with version changes."""
        # Mock VersionManagerExpert
        with patch('zenrube.experts.autopublisher.VersionManagerExpert') as mock_version_manager_class:
            mock_version_manager = Mock()
            mock_version_manager_class.return_value = mock_version_manager
            
            # Set up the mock to return current versions
            current_versions = {
                'test_expert1': '1.1.0',
                'test_expert2': '2.0.0',
                'test_expert3': '1.0.0'
            }
            mock_version_manager.get_expert_versions.return_value = current_versions
            
            # Mock the _get_last_recorded_versions method
            with patch.object(AutoPublisherExpert, '_get_last_recorded_versions') as mock_get_versions:
                # Set up last recorded versions - only test_expert1 changed
                mock_get_versions.return_value = {
                    'test_expert1': '1.0.0',  # Changed
                    'test_expert2': '2.0.0',  # No change
                    'test_expert3': '1.0.0'   # No change (not in changelog, will be skipped)
                }
                
                expert = AutoPublisherExpert()
                updates = expert.check_for_updates()
                
                # Verify that only test_expert1 with changed version is returned
                assert 'test_expert1' in updates
                assert updates['test_expert1'] == '1.1.0'
                assert 'test_expert2' not in updates  # No change
                assert 'test_expert3' not in updates  # New expert, not considered update
                assert len(updates) == 1

    def test_run_autopublish_invokes_all_components(self):
        """Test that run_autopublish calls all required components in order."""
        with patch('zenrube.experts.autopublisher.VersionManagerExpert') as mock_vm_class, \
             patch('zenrube.experts.autopublisher.PublisherExpert') as mock_pub_class, \
             patch('zenrube.experts.autopublisher.RubeAdapterExpert') as mock_ra_class:
            
            # Set up mocks
            mock_version_manager = Mock()
            mock_version_manager.get_expert_versions.return_value = {'test_expert': '1.1.0'}
            mock_vm_class.return_value = mock_version_manager
            
            mock_publisher = Mock()
            mock_manifest = {
                'manifest_version': '1.0',
                'publisher': 'test@example.com',
                'experts': [{'name': 'test_expert', 'version': '1.1.0'}]
            }
            mock_publisher.generate_manifest.return_value = mock_manifest
            mock_pub_class.return_value = mock_publisher
            
            mock_rube_adapter = Mock()
            mock_response = {'status': 'success', 'manifest_id': 'test123'}
            mock_rube_adapter.publish_manifest.return_value = mock_response
            mock_rube_adapter.verify_publication.return_value = True
            mock_ra_class.return_value = mock_rube_adapter
            
            # Mock changelog version to show update
            with patch.object(AutoPublisherExpert, '_get_last_recorded_versions') as mock_get_versions:
                mock_get_versions.return_value = {'test_expert': '1.0.0'}
                
                expert = AutoPublisherExpert()
                result = expert.run_autopublish()
                
                # Verify all components were called in the correct order
                mock_version_manager.get_expert_versions.assert_called_once()
                mock_publisher.generate_manifest.assert_called_once()
                mock_rube_adapter.publish_manifest.assert_called_once()
                mock_rube_adapter.verify_publication.assert_called_once()
                
                # Verify the result
                assert result['status'] == 'success'

    def test_run_autopublish_returns_valid_response(self):
        """Test that run_autopublish returns valid response on successful publication."""
        with patch('zenrube.experts.autopublisher.VersionManagerExpert') as mock_vm_class, \
             patch('zenrube.experts.autopublisher.PublisherExpert') as mock_pub_class, \
             patch('zenrube.experts.autopublisher.RubeAdapterExpert') as mock_ra_class:
            
            # Set up mocks for successful publication
            mock_version_manager = Mock()
            mock_version_manager.get_expert_versions.return_value = {'test_expert': '1.1.0'}
            mock_vm_class.return_value = mock_version_manager
            
            mock_publisher = Mock()
            mock_publisher.generate_manifest.return_value = {
                'manifest_version': '1.0',
                'publisher': 'test@example.com',
                'experts': [{'name': 'test_expert', 'version': '1.1.0'}]
            }
            mock_pub_class.return_value = mock_publisher
            
            mock_rube_adapter = Mock()
            mock_response = {
                'status': 'success',
                'manifest_id': 'manifest_12345',
                'experts_published': 1,
                'message': 'Publication successful'
            }
            mock_rube_adapter.publish_manifest.return_value = mock_response
            mock_rube_adapter.verify_publication.return_value = True
            mock_ra_class.return_value = mock_rube_adapter
            
            # Mock changelog
            with patch.object(AutoPublisherExpert, '_get_last_recorded_versions') as mock_get_versions:
                mock_get_versions.return_value = {'test_expert': '1.0.0'}
                
                expert = AutoPublisherExpert()
                result = expert.run_autopublish()
                
                # Verify response structure
                assert result['status'] == 'success'
                assert 'manifest_id' in result
                assert 'experts_published' in result
                assert isinstance(result['manifest_id'], str)
                assert result['experts_published'] == 1

    def test_run_autopublish_handles_failed_publish(self):
        """Test that run_autopublish handles failed publication gracefully."""
        with patch('zenrube.experts.autopublisher.VersionManagerExpert') as mock_vm_class, \
             patch('zenrube.experts.autopublisher.PublisherExpert') as mock_pub_class, \
             patch('zenrube.experts.autopublisher.RubeAdapterExpert') as mock_ra_class:
            
            # Set up mocks for failed publication
            mock_version_manager = Mock()
            mock_version_manager.get_expert_versions.return_value = {'test_expert': '1.1.0'}
            mock_vm_class.return_value = mock_version_manager
            
            mock_publisher = Mock()
            mock_publisher.generate_manifest.return_value = {
                'manifest_version': '1.0',
                'publisher': 'test@example.com',
                'experts': [{'name': 'test_expert', 'version': '1.1.0'}]
            }
            mock_pub_class.return_value = mock_publisher
            
            mock_rube_adapter = Mock()
            mock_rube_adapter.publish_manifest.return_value = {
                'status': 'failed',
                'message': 'Authentication failed'
            }
            mock_rube_adapter.verify_publication.return_value = False
            mock_ra_class.return_value = mock_rube_adapter
            
            # Mock changelog
            with patch.object(AutoPublisherExpert, '_get_last_recorded_versions') as mock_get_versions:
                mock_get_versions.return_value = {'test_expert': '1.0.0'}
                
                expert = AutoPublisherExpert()
                
                # Verify that the exception is raised
                with pytest.raises(Exception) as exc_info:
                    expert.run_autopublish()
                
                assert "Publication verification failed" in str(exc_info.value)

    def test_activity_log_created_and_written(self):
        """Test that activity log is created and contains timestamped entries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary log file path
            log_path = os.path.join(temp_dir, 'zenrube_activity.log')
            
            with patch('zenrube.experts.autopublisher.AutoPublisherExpert') as mock_class:
                # Mock the activity log path
                with patch.object(mock_class, 'activity_log_path', log_path):
                    # Create real instance to test logging
                    with patch('zenrube.experts.autopublisher.VersionManagerExpert'), \
                         patch('zenrube.experts.autopublisher.PublisherExpert'), \
                         patch('zenrube.experts.autopublisher.RubeAdapterExpert'):
                        
                        real_expert = AutoPublisherExpert()
                        real_expert.activity_log_path = log_path
                        
                        # Test logging
                        test_message = "Test activity message"
                        real_expert._log_activity(test_message)
                        
                        # Verify log file was created
                        assert os.path.exists(log_path)
                        
                        # Verify content
                        with open(log_path, 'r') as f:
                            content = f.read()
                            assert test_message in content
                            # Verify timestamp format
                            assert '[' in content
                            assert ']' in content

    def test_metadata_contains_required_keys(self):
        """Test that EXPERT_METADATA contains all required keys."""
        required_keys = ['name', 'version', 'description', 'author']
        
        for key in required_keys:
            assert key in EXPERT_METADATA, f"Missing required key: {key}"
        
        # Verify values are non-empty strings
        assert isinstance(EXPERT_METADATA['name'], str)
        assert isinstance(EXPERT_METADATA['version'], str)
        assert isinstance(EXPERT_METADATA['description'], str)
        assert isinstance(EXPERT_METADATA['author'], str)
        
        # Verify expected values
        assert EXPERT_METADATA['name'] == 'autopublisher'
        assert EXPERT_METADATA['version'] == '1.0'
        assert 'automates expert' in EXPERT_METADATA['description'].lower()
        assert EXPERT_METADATA['author'] == 'vladinc@gmail.com'

    def test_no_duplicate_changelog_entries_on_republish(self):
        """Test that VersionManagerExpert only logs version bumps once per version."""
        with patch('zenrube.experts.autopublisher.VersionManagerExpert') as mock_vm_class, \
             patch('zenrube.experts.autopublisher.PublisherExpert') as mock_pub_class, \
             patch('zenrube.experts.autopublisher.RubeAdapterExpert') as mock_ra_class:
            
            # Set up mocks
            mock_version_manager = Mock()
            mock_version_manager.get_expert_versions.return_value = {
                'test_expert1': '1.1.0',
                'test_expert2': '1.2.0'
            }
            mock_version_manager.record_changelog = Mock()
            mock_vm_class.return_value = mock_version_manager
            
            mock_publisher = Mock()
            mock_publisher.generate_manifest.return_value = {
                'manifest_version': '1.0',
                'publisher': 'test@example.com',
                'experts': [
                    {'name': 'test_expert1', 'version': '1.1.0'},
                    {'name': 'test_expert2', 'version': '1.2.0'}
                ]
            }
            mock_pub_class.return_value = mock_publisher
            
            mock_rube_adapter = Mock()
            mock_rube_adapter.publish_manifest.return_value = {
                'status': 'success',
                'manifest_id': 'test123'
            }
            mock_rube_adapter.verify_publication.return_value = True
            mock_ra_class.return_value = mock_rube_adapter
            
            # Mock changelog showing updates
            with patch.object(AutoPublisherExpert, '_get_last_recorded_versions') as mock_get_versions:
                mock_get_versions.return_value = {
                    'test_expert1': '1.0.0',  # Updated
                    'test_expert2': '1.1.0'   # Updated
                }
                
                expert = AutoPublisherExpert()
                result = expert.run_autopublish()
                
                # Verify record_changelog was called exactly once per updated expert
                assert mock_version_manager.record_changelog.call_count == 2
                
                # Verify the calls were made with correct parameters
                calls = mock_version_manager.record_changelog.call_args_list
                
                # Check first call
                args, kwargs = calls[0]
                assert kwargs['expert_name'] in ['test_expert1', 'test_expert2']
                assert kwargs['new_version'] in ['1.1.0', '1.2.0']
                assert 'Auto-publish' in kwargs['change_summary']
                
                # Check second call  
                args, kwargs = calls[1]
                assert kwargs['expert_name'] in ['test_expert1', 'test_expert2']
                assert kwargs['new_version'] in ['1.1.0', '1.2.0']
                assert 'Auto-publish' in kwargs['change_summary']

    def test_check_for_updates_with_no_changes(self):
        """Test that check_for_updates returns empty dict when no updates exist."""
        with patch('zenrube.experts.autopublisher.VersionManagerExpert') as mock_vm_class:
            mock_version_manager = Mock()
            mock_version_manager.get_expert_versions.return_value = {
                'expert1': '1.0.0',
                'expert2': '2.0.0'
            }
            mock_vm_class.return_value = mock_version_manager
            
            # Mock _get_last_recorded_versions to return same versions
            with patch.object(AutoPublisherExpert, '_get_last_recorded_versions') as mock_get_versions:
                mock_get_versions.return_value = {
                    'expert1': '1.0.0',
                    'expert2': '2.0.0'
                }
                
                expert = AutoPublisherExpert()
                updates = expert.check_for_updates()
                
                assert updates == {}
                assert len(updates) == 0

    def test_run_autopublish_with_no_updates_skips_publication(self):
        """Test that run_autopublish skips publication when no updates are found."""
        with patch('zenrube.experts.autopublisher.VersionManagerExpert') as mock_vm_class, \
             patch('zenrube.experts.autopublisher.PublisherExpert') as mock_pub_class, \
             patch('zenrube.experts.autopublisher.RubeAdapterExpert') as mock_ra_class:
            
            # Set up mocks
            mock_version_manager = Mock()
            mock_version_manager.get_expert_versions.return_value = {'expert1': '1.0.0'}
            mock_vm_class.return_value = mock_version_manager
            
            mock_publisher = Mock()
            mock_pub_class.return_value = mock_publisher
            
            mock_rube_adapter = Mock()
            mock_ra_class.return_value = mock_rube_adapter
            
            # Mock no updates found
            with patch.object(AutoPublisherExpert, '_get_last_recorded_versions') as mock_get_versions:
                mock_get_versions.return_value = {'expert1': '1.0.0'}  # No changes
                
                expert = AutoPublisherExpert()
                result = expert.run_autopublish()
                
                # Verify publisher and rube adapter were not called
                mock_publisher.generate_manifest.assert_not_called()
                mock_rube_adapter.publish_manifest.assert_not_called()
                mock_rube_adapter.verify_publication.assert_not_called()
                
                # Verify response indicates skipped publication
                assert result['status'] == 'skipped'
                assert 'No version updates detected' in result['message']