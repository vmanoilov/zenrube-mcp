"""
Updated Profile Controller for Zenrube Dynamic Personality System

Now exposes primary_domain, secondary_domain, and roast_level for personality engine.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging

from .dynamic_profile_engine import DynamicProfileEngine
from .classification_engine import ClassificationEngine
from .compatibility_matrix import CompatibilityMatrix
from .profile_memory import ProfileMemory
from .profile_logs import ProfileLogger
from .personality_presets import RoastLevel
from .personality_engine import PersonalityEngine, SelectionCriteria


class ProfileController:
    """Central controller for profile management with personality integration"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Core components
        self.profile_engine = DynamicProfileEngine()
        self.classification_engine = ClassificationEngine()
        self.compatibility_matrix = CompatibilityMatrix()
        self.profile_memory = ProfileMemory()
        self.profile_logger = ProfileLogger()
        
        # Personality system integration
        from .personality_engine import personality_engine
        self.personality_engine = personality_engine
        
        # Safety integration
        from .personality_safety import safety_governor
        self.safety_governor = safety_governor
        
        # Cache for domain classification
        self.domain_cache = {}
        
        # Configuration
        self.cache_ttl_minutes = self.config.get("cache_ttl_minutes", 30)
    
    def process_request(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
        user_profile: Optional[Dict[str, Any]] = None,
        roast_level: Optional[RoastLevel] = None,
        team_composition: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Process request with personality-aware profile management"""
        
        # Classify domains for personality engine
        primary_domain, secondary_domain = self._classify_domains(request, context)
        
        # Prepare criteria for personality selection
        criteria = SelectionCriteria(
            task_type=self._determine_task_type(request, context),
            primary_domain=primary_domain,
            secondary_domain=secondary_domain,
            roast_level=roast_level,
            team_mood=context.get("team_mood") if context else None,
            risk_tolerance=context.get("risk_tolerance") if context else None,
            previous_modes=context.get("previous_modes") if context else None
        )
        
        # Get base profile
        base_profile = self.profile_engine.get_profile(
            request, user_profile, context
        )
        
        # Enhance with personality-aware expert selection
        personality_enhanced_profile = self._enhance_with_personality(
            base_profile, criteria, team_composition
        )
        
        # Log the personality-enhanced decision
        self.profile_logger.log_decision(
            request, personality_enhanced_profile, {
                "primary_domain": primary_domain,
                "secondary_domain": secondary_domain,
                "roast_level": roast_level.value if roast_level else 0,
                "personality_assignments": {
                    expert: mode.mode_id 
                    for expert, mode in personality_enhanced_profile.get("personality_assignments", {}).items()
                }
            }
        )
        
        return personality_enhanced_profile
    
    def _classify_domains(self, request: str, context: Optional[Dict[str, Any]]) -> tuple:
        """Classify request into primary and secondary domains"""
        
        # Check cache first
        cache_key = f"{request}:{str(context)}"
        if cache_key in self.domain_cache:
            cached_time, domains = self.domain_cache[cache_key]
            if datetime.now() - cached_time < timedelta(minutes=self.cache_ttl_minutes):
                return domains
        
        # Use classification engine
        classification_result = self.classification_engine.classify(request, context)
        
        primary_domain = classification_result.get("primary_domain", "general")
        secondary_domain = classification_result.get("secondary_domain", None)
        
        # Cache the result
        self.domain_cache[cache_key] = (datetime.now(), (primary_domain, secondary_domain))
        
        return primary_domain, secondary_domain
    
    def _determine_task_type(self, request: str, context: Optional[Dict[str, Any]]) -> str:
        """Determine the type of task for personality selection"""
        
        # Simple task type detection based on keywords
        request_lower = request.lower()
        
        task_indicators = {
            "analysis": ["analyze", "examine", "review", "assess", "investigate"],
            "creative": ["create", "design", "brainstorm", "generate", "invent"],
            "routine": ["process", "routine", "regular", "standard", "normal"],
            "debug": ["debug", "fix", "error", "problem", "issue", "troubleshoot"],
            "brainstorm": ["brainstorm", "ideas", "think", "suggest", "propose"],
            "review": ["review", "check", "verify", "validate", "test"]
        }
        
        for task_type, indicators in task_indicators.items():
            if any(indicator in request_lower for indicator in indicators):
                return task_type
        
        return "general"
    
    def _enhance_with_personality(
        self,
        base_profile: Dict[str, Any],
        criteria: SelectionCriteria,
        team_composition: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Enhance profile with personality-aware expert assignments"""
        
        expert_assignments = base_profile.get("expert_assignments", {})
        
        # Build expert assignments dict for personality engine
        expert_instances = {}
        for expert_name, assignment in expert_assignments.items():
            expert_instances[assignment["type"]] = assignment
        
        # Get personality assignments
        personality_assignments = self.personality_engine.assign_personalities(
            expert_instances, criteria
        )
        
        # Apply safety governor to all personality modes
        safe_assignments = {}
        safety_events = []
        
        for expert_type, mode in personality_assignments.items():
            safe_mode, was_modified, events = self.safety_governor.apply_safety_governor(
                mode, criteria, expert_type
            )
            safe_assignments[expert_type] = safe_mode
            safety_events.extend(events)
        
        # Build personality prefixes for LLM prompts
        personality_prefixes = {}
        for expert_type, mode in safe_assignments.items():
            prefix = self.personality_engine.build_personality_prefix(mode, context=criteria.to_dict())
            personality_prefixes[expert_type] = prefix
        
        # Build the final profile structure with required fields
        final_profile = {
            "experts": list(expert_assignments.keys()),
            "primary_domain": criteria.primary_domain,
            "secondary_domain": criteria.secondary_domain,
            "roast_level": criteria.roast_level.value if criteria.roast_level else 0,
            "task_type": criteria.task_type,
            "context": base_profile.get("context", {}),
            "personality_assignments": safe_assignments,
            "personality_prefixes": personality_prefixes,
            "safety_events": [event.to_dict() for event in safety_events],
            "team_diversity": self._calculate_team_diversity(safe_assignments)
        }
        
        return final_profile
    
    def _calculate_team_diversity(self, personality_assignments: Dict[str, Any]) -> float:
        """Calculate diversity score for the personality team"""
        if not personality_assignments:
            return 0.0
        
        # Analyze roast level distribution
        roast_levels = [mode.roast_level for mode in personality_assignments.values()]
        unique_roasts = len(set(roast_levels))
        total_experts = len(personality_assignments)
        
        diversity_score = unique_roasts / total_experts
        return min(1.0, diversity_score)
    
    def get_personality_status(self) -> Dict[str, Any]:
        """Get current personality system status"""
        return {
            "engine_analytics": self.personality_engine.get_selection_analytics(),
            "safety_status": self.safety_governor.get_safety_status(),
            "domain_cache_size": len(self.domain_cache),
            "recent_decisions": self.profile_logger.get_recent_decisions(limit=5)
        }
    
    def clear_caches(self):
        """Clear all caches"""
        self.domain_cache.clear()
        self.profile_engine.clear_cache()
        self.compatibility_matrix.clear_cache()
    
    def reset_personality_state(self, expert_type: Optional[str] = None):
        """Reset personality system state"""
        if expert_type:
            self.safety_governor.clear_expert_status(expert_type)
        else:
            # Reset all state would require accessing private attributes
            pass


# Global profile controller instance
profile_controller = ProfileController()