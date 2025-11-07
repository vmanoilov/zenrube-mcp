#!/usr/bin/env python3
"""
Test script for VersionManagerExpert to verify functionality.
"""

import sys
import os
import json
from typing import Dict, Any

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from zenrube.experts.version_manager import VersionManagerExpert, EXPERT_METADATA
    print("✅ Successfully imported VersionManagerExpert")
    print(f"📊 Expert Metadata: {json.dumps(EXPERT_METADATA, indent=2)}")
    
    # Initialize the expert
    vm = VersionManagerExpert()
    print("✅ Successfully initialized VersionManagerExpert")
    
    # Test get_current_version
    version = vm.get_current_version("data_cleaner")
    print(f"🔢 Current version for 'data_cleaner': {version}")
    
    # Test bump_version
    new_version = vm.bump_version("data_cleaner", "patch")
    print(f"🔢 New version after patch bump: {new_version}")
    
    # Test get_current_version again
    current_version = vm.get_current_version("data_cleaner")
    print(f"🔢 Current version after bump: {current_version}")
    
    # Test the new convenience method
    new_version = vm.bump_version_and_record("data_cleaner", "minor", "Added new version tracking features")
    print(f"🔢 Version after minor bump with changelog: {new_version}")
    
    # Test version bumping at different levels
    vm.bump_version("semantic_router", "major")
    print("🔢 Semantic router bumped to major version")
    
    # Test record_changelog
    vm.record_changelog("data_cleaner", "Updated version management functionality")
    print("📝 Changelog recorded successfully")
    
    # Test update_manifest_versions
    test_manifest = {
        "experts": {
            "data_cleaner": {"version": "1.0.0"},
            "semantic_router": {"version": "1.0.0"},
            "version_manager": {"version": "1.0.0"}
        }
    }
    updated_manifest = vm.update_manifest_versions(test_manifest)
    print("📋 Manifest update test:")
    print(json.dumps(updated_manifest, indent=2))
    
    # Test get_expert_versions
    all_versions = vm.get_expert_versions()
    print(f"📈 All expert versions: {json.dumps(all_versions, indent=2)}")
    
    # Test error handling
    try:
        vm.bump_version("test_expert", "invalid_level")
    except ValueError as e:
        print(f"✅ Error handling test passed: {e}")
    
    print("\n🎉 All tests passed! VersionManagerExpert is working correctly.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Test failed: {e}")
    sys.exit(1)