# Basic Usage Example

## Quick Start

Copy this code into Rube's REMOTE_WORKBENCH:

```python
from datetime import datetime
import json

# The zen_consensus function
def zen_consensus(question, models=None, synthesis_style="balanced"):
    if models is None:
        models = ["expert_1", "expert_2", "expert_3"]

    responses = []
    for model_name in models:
        perspective_prompts = {
            "expert_1": f"As a pragmatic engineer, analyze: {question}\n\nFocus on: practical implementation, trade-offs.",
            "expert_2": f"As a systems architect, analyze: {question}\n\nFocus on: scalability, maintainability.",
            "expert_3": f"As a security expert, analyze: {question}\n\nFocus on: security, vulnerabilities."
        }

        prompt = perspective_prompts.get(model_name, f"Analyze: {question}")
        response, error = invoke_llm(prompt)

        if not error:
            responses.append({"model": model_name, "response": response})

    synthesis_prompt = f'''
    Experts provided these perspectives:
    {json.dumps(responses, indent=2)}

    Synthesize a consensus with:
    1. Areas of agreement
    2. Key disagreements
    3. Recommendation
    4. Confidence level
    '''

    consensus, _ = invoke_llm(synthesis_prompt)

    return {
        "question": question,
        "experts_consulted": len(responses),
        "individual_responses": responses,
        "consensus": consensus,
        "timestamp": datetime.now().isoformat()
    }

# USE IT
result = zen_consensus(
    question="Should I use REST or GraphQL for my API?",
    models=["expert_1", "expert_2"],
    synthesis_style="balanced"
)

print("Question:", result['question'])
print("\nConsensus:", result['consensus'])
```

## Expected Output

You'll get:
- Individual expert analyses from different perspectives
- Synthesized consensus highlighting agreements and disagreements
- Clear recommendation with confidence level
- Timestamp for tracking

## Customization

### Different Question
```python
result = zen_consensus("Choose between AWS Lambda vs Docker containers")
```

### Different Experts
```python
result = zen_consensus(
    question="Your question here",
    models=["expert_1", "expert_3"]  # Skip expert_2
)
```

### Different Synthesis Style
```python
# Options: "balanced", "critical", "collaborative"
result = zen_consensus(
    question="Your question here",
    synthesis_style="critical"  # More challenging analysis
)
```

## Integration with Rube Apps

After getting consensus, use it with other tools:

```python
# Get consensus
result = zen_consensus("Architecture decision...")

# Save to Google Docs
run_composio_tool("GOOGLEDOCS_CREATE_DOCUMENT", {
    "title": "Decision: Architecture Choice",
    "content": result['consensus']
})

# Notify team on Slack
run_composio_tool("SLACK_SEND_MESSAGE", {
    "channel": "#tech-decisions",
    "text": f"Decision made: {result['consensus'][:100]}..."
})
```
