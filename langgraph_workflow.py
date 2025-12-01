from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import asyncio
import os
import json
import logging

logger = logging.getLogger("triage")
logging.basicConfig(level=logging.INFO)

class TicketState(BaseModel):
    ticket_id: str
    channel: str
    text: str
    metadata: Dict[str, Any] = {}
    issue_type: Optional[str] = None
    priority: Optional[str] = None  # P0..P3
    confidence: Optional[float] = None
    classification_reasoning: Optional[str] = None
    routed_team: Optional[str] = None
    jira_issue_key: Optional[str] = None
    human_review_required: bool = False
    logs: List[Dict[str, Any]] = []

# Example mapping from issue_type / priority to teams
ROUTING_TABLE = {
    ("Bug", "P0"): {"team": "Backend", "queue": "engineering-high"},
    ("Bug", "P1"): {"team": "Backend", "queue": "engineering"},
    ("Billing", None): {"team": "Billing", "queue": "billing"},
    ("Feature Request", None): {"team": "Product", "queue": "product"},
    ("Account", None): {"team": "Customer Success", "queue": "cs"},
    ("Other", None): {"team": "Support", "queue": "support"},
}

# --- Abstracted LLM client (replace with Azure OpenAI / OpenAI client) ---
class LLMClient:
    async def classify_ticket(self, text: str) -> Dict[str, Any]:
        # Replace with calls to your LLM via Azure OpenAI
        # Return an object with fields: issue_type, priority, confidence, reasoning
        # This stub returns a dummy classification for demonstration.
        await asyncio.sleep(0.1)
        return {
            "issue_type": "Bug" if "error" in text.lower() else "Other",
            "priority": "P1" if "urgent" in text.lower() else "P3",
            "confidence": 0.92,
            "reasoning": "Detected keywords: error -> Bug. 'urgent' -> P1."
        }

# --- Nodes ---
async def classification_node(state: TicketState, llm: LLMClient):
    res = await llm.classify_ticket(state.text)
    state.issue_type = res.get("issue_type")
    state.priority = res.get("priority")
    state.confidence = res.get("confidence")
    state.classification_reasoning = res.get("reasoning")
    state.logs.append({"node": "classification", "result": res})
    logger.info(f"[{state.ticket_id}] classification: {res}")
    return state

async def policy_node(state: TicketState, config: Dict[str, Any]):
    # Apply deterministic business rules and confidence thresholds
    low_conf_threshold = config.get("low_confidence_threshold", 0.7)
    high_risk_keywords = config.get("high_risk_keywords", ["lawsuit", "security breach", "data leak"])

    # Force review for high-risk keywords
    text_lower = state.text.lower()
    if any(k in text_lower for k in high_risk_keywords):
        state.human_review_required = True
        state.logs.append({"node": "policy", "reason": "high_risk_keyword"})
        logger.info(f"[{state.ticket_id}] flagged for human review due to high-risk keyword")

    # Force review when confidence is low
    if (state.confidence or 0.0) < low_conf_threshold:
        state.human_review_required = True
        state.logs.append({"node": "policy", "reason": "low_confidence"})
        logger.info(f"[{state.ticket_id}] flagged for human review due to low confidence")

    # Additional enterprise rules (example)
    if state.metadata.get("account_tier") == "enterprise" and state.priority in ("P1", "P0"):
        state.human_review_required = True
        state.logs.append({"node": "policy", "reason": "enterprise_high_priority"})
        logger.info(f"[{state.ticket_id}] enterprise high-priority requires human review")

    return state

async def routing_node(state: TicketState):
    # Map issue_type+priority to team
    key = (state.issue_type, state.priority)
    mapping = ROUTING_TABLE.get(key) or ROUTING_TABLE.get((state.issue_type, None)) or ROUTING_TABLE.get(("Other", None))
    state.routed_team = mapping["team"]
    state.logs.append({"node": "routing", "route": mapping, "reasoning": state.classification_reasoning})
    logger.info(f"[{state.ticket_id}] routed to {state.routed_team}")
    return state

# --- Human review & integrations (abstracted) ---
async def send_slack_review(state: TicketState) -> None:
    # Send Slack block kit with action buttons to approve/modify route.
    # The Slack payload should include the ticket_id and allow one-click approve.
    logger.info(f"[{state.ticket_id}] would send Slack review to channel for human triage")
    # Implement slack_client.chat_postMessage(...) with a Block Kit payload.

async def create_jira_issue(state: TicketState) -> Optional[str]:
    # Create a Jira ticket if required by routing; return issue key.
    logger.info(f"[{state.ticket_id}] would create Jira issue for team {state.routed_team}")
    # Implement actual Jira API call and return the created issue key.
    return None

# --- Orchestrator ---
async def run_workflow(state: TicketState, llm: LLMClient, config: Dict[str, Any]):
    state = await classification_node(state, llm)
    state = await policy_node(state, config)
    state = await routing_node(state)

    if state.human_review_required:
        await send_slack_review(state)
    else:
        # Optionally create Jira issue for engineering queues
        issue_key = await create_jira_issue(state)
        state.jira_issue_key = issue_key

    # Persist state/logs to DB here (abstracted)
    state.logs.append({"node": "completed"})
    logger.info(f"[{state.ticket_id}] workflow completed")
    return state

# Example usage for local testing
if __name__ == "__main__":
    async def _main():
        llm = LLMClient()
        state = TicketState(ticket_id="TICKET-123", channel="email", text="There is an error when saving — urgent", metadata={"account_tier": "standard"})
        config = {"low_confidence_threshold": 0.7, "high_risk_keywords": ["lawsuit", "security breach", "data leak"]}
        final = await run_workflow(state, llm, config)
        print(final.json(indent=2))
    asyncio.run(_main())
