{
    "system_message": "You are an expert HR assistant...",
    "user_message": {
        "job_description": "[JD text]",
        "resume": "[Resume text]"
    }
}
```

#### Response Format
```json
{
    "decision": "shortlist|reject",
    "justification": "Detailed explanation",
    "match_score": 0.0-1.0,
    "key_matches": ["skill1", "skill2"],
    "missing_requirements": ["req1", "req2"]
}