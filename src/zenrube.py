"""
zenrube-mcp: Zen-Inspired Consensus for Rube Workflows

Author: vmanoilov
License: Apache 2.0
"""

from datetime import datetime
import json


def zen_consensus(question, models=None, synthesis_style="balanced"):
    """
    Zen MCP-style consensus tool adapted for Rube

    Args:
        question: The question/problem to get consensus on
        models: List of model identifiers
        synthesis_style: "balanced", "critical", or "collaborative"

    Returns:
        Dict with individual responses and synthesized consensus
    """

    if models is None:
        models = ["expert_1", "expert_2", "expert_3"]

    responses = []

    for model_name in models:
        # Craft perspective-specific prompts
        perspective_prompts = {
            "expert_1": f"As a pragmatic engineer, analyze: {question}\n\nFocus on: practical implementation, trade-offs.",
            "expert_2": f"As a systems architect, analyze: {question}\n\nFocus on: scalability, maintainability.",
            "expert_3": f"As a security expert, analyze: {question}\n\nFocus on: security, vulnerabilities."
        }

        prompt = perspective_prompts.get(model_name, f"Analyze: {question}")
        response, error = invoke_llm(prompt)

        if not error:
            responses.append({
                "model": model_name,
                "response": response
            })

    # Synthesize consensus
    synthesis_prompt = f"""
    Experts provided these perspectives:
    {json.dumps(responses, indent=2)}

    Synthesize a consensus with:
    1. Areas of agreement
    2. Key disagreements
    3. Recommendation
    4. Confidence level
    """

    consensus, _ = invoke_llm(synthesis_prompt)

    return {
        "question": question,
        "experts_consulted": len(responses),
        "individual_responses": responses,
        "consensus": consensus,
        "timestamp": datetime.now().isoformat()
    }
