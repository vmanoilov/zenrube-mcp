# personality_safety.py
"""
Personality Safety Governor Module (Phase 3A)
Implements safety constraints and overrides for Zenrube personality system.
Ensures safe and appropriate personality mode selection.
"""

from typing import Dict, Any, Tuple

from personality_presets import get_neutral_personality


def apply_safety_governor(domain: str, roast_level: int, task_type: str, personalities: Dict[str, Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    overrides_applied = 0
    neutral_fallback_used = False
    reasons = []
    
    adjusted_personalities = personalities.copy()
    
    # Rule 1: Roast Clamping
    for brain_name, personality_cfg in personalities.items():
        if roast_level == 0:
            adjusted_personalities[brain_name] = get_neutral_personality(brain_name)
            overrides_applied += 1
            reasons.append(f"Forced neutral_mode for {brain_name} (roast_level=0)")
        elif roast_level < personality_cfg.get("allowed_roast", 0):
            adjusted_personalities[brain_name] = get_neutral_personality(brain_name)
            overrides_applied += 1
            reasons.append(f"Clamped {brain_name} to neutral_mode (insufficient roast_level)")
    
    # Rule 2: Chaos Cooling (simple version)
    if domain == "emotional":
        for brain_name in adjusted_personalities:
            adjusted_personalities[brain_name] = get_neutral_personality(brain_name)
            overrides_applied += 1
        reasons.append("Forced neutral_mode for all experts (emotional domain)")
    
    if task_type == "sensitive":
        for brain_name in adjusted_personalities:
            adjusted_personalities[brain_name] = get_neutral_personality(brain_name)
            overrides_applied += 1
        reasons.append("Forced neutral_mode for all experts (sensitive task_type)")
    
    # Rule 3: Neutral Fallback
    if overrides_applied >= 2:
        for brain_name in adjusted_personalities:
            adjusted_personalities[brain_name] = get_neutral_personality(brain_name)
        neutral_fallback_used = True
        reasons.append("Neutral fallback triggered (2+ overrides)")
    
    # Rule 4: Safety Summary
    safety_summary = {
        "overrides_applied": overrides_applied,
        "neutral_fallback_used": neutral_fallback_used,
        "reason": "; ".join(reasons) if reasons else "No safety overrides applied"
    }
    
    return adjusted_personalities, safety_summary