"""
Zenrube experts module.

This module contains expert classes that handle specific types of tasks
within the Zenrube MCP system.
"""

# Import all available experts from the experts subdirectory
from .semantic_router import SemanticRouterExpert, EXPERT_METADATA as SEMANTIC_ROUTER_METADATA
from .data_cleaner import DataCleanerExpert, EXPERT_METADATA as DATA_CLEANER_METADATA
from .summarizer import SummarizerExpert, EXPERT_METADATA as SUMMARIZER_METADATA
from .publisher import PublisherExpert, EXPERT_METADATA as PUBLISHER_METADATA
from .rube_adapter import RubeAdapterExpert, EXPERT_METADATA as RUBE_ADAPTER_METADATA
from .version_manager import VersionManagerExpert, EXPERT_METADATA as VERSION_MANAGER_METADATA

__all__ = [
    "SemanticRouterExpert",
    "DataCleanerExpert",
    "SummarizerExpert",
    "PublisherExpert",
    "RubeAdapterExpert",
    "VersionManagerExpert",
    "SEMANTIC_ROUTER_METADATA",
    "DATA_CLEANER_METADATA",
    "SUMMARIZER_METADATA",
    "PUBLISHER_METADATA",
    "RUBE_ADAPTER_METADATA",
    "VERSION_MANAGER_METADATA"
]