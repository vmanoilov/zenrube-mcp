"""
Updated Council Runner for Zenrube Dynamic Personality System

Integrates personality assignment, safety governor, and personality prefixes
into the team council execution pipeline.
"""

from typing import Dict, List, Optional, Any, Union
import asyncio
import logging
from datetime import datetime

from zenrube.experts.team_council import TeamCouncil
from zenrube.profiles.profile_controller import profile_controller
from zenrube.profiles.personality_presets import RoastLevel
from zenrube.profiles.personality_engine import assign_personalities, build_personality_prefix
from zenrube.profiles.personality_safety import apply_safety_governor


class CouncilRunner:
    """Council runner with integrated personality system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.team_council = TeamCouncil(config.get("team_council_config", {}))
        self.profile_controller = profile_controller
    
    async def run_council(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        user_profile: Optional[Dict[str, Any]] = None,
        roast_level: Optional[RoastLevel] = None,
        max_iterations: int = 3,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Run council with personality system integration"""
        
        # Set default roast level if none provided
        if roast_level is None:
            roast_level = RoastLevel.MODERATE
        
        # Process request through profile controller
        profile = self.profile_controller.process_request(
            request=query,
            context=context,
            user_profile=user_profile,
            roast_level=roast_level,
            team_composition=context.get("team_composition") if context else None
        )
        
        # Extract personality data from profile
        primary_domain = profile.get("primary_domain", "general")
        secondary_domain = profile.get("secondary_domain")
        roast_level_value = profile.get("roast_level", 0)
        task_type = profile.get("task_type", "general")
        
        # Call assign_personalities
        personalities = assign_personalities(
            profile=profile,
            domain=primary_domain,
            roast_level=roast_level_value
        )
        
        # Apply safety governor
        adjusted_personalities, safety_summary = apply_safety_governor(
            domain=primary_domain,
            roast_level=roast_level_value,
            task_type=task_type,
            personalities=personalities
        )
        
        # Generate per-brain prefixes
        prefix_map = {
            brain: build_personality_prefix(brain, cfg, task_type)
            for brain, cfg in adjusted_personalities.items()
        }
        
        # Prepare council configuration with personality prefixes
        council_config = context.copy() if context else {}
        council_config.update({
            "personality_prefixes": prefix_map,
            "personality_assignments": adjusted_personalities,
            "primary_domain": primary_domain,
            "secondary_domain": secondary_domain,
            "roast_level": roast_level_value,
            "task_type": task_type
        })
        
        # Execute council with personality prefixes
        if timeout:
            result = await asyncio.wait_for(
                self.team_council.process_request(query, council_config),
                timeout=timeout
            )
        else:
            result = await self.team_council.process_request(query, council_config)
        
        # Attach personality data to final council output
        result["personalities_used"] = adjusted_personalities
        result["personality_safety_summary"] = safety_summary
        
        return result


# Global council runner instance
council_runner = CouncilRunner()