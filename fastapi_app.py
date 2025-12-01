from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from workflows.langgraph_workflow import TicketState, run_workflow, LLMClient
import uvicorn
import os
import uuid
import logging

logger = logging.getLogger("fastapi")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="SignalDesk Triage Demo")

class IngestTicket(BaseModel):
    channel: str
    text: str
    metadata: dict = {}

@app.post("/ingest", status_code=202)
async def ingest(ticket: IngestTicket, background_tasks: BackgroundTasks):
    ticket_id = str(uuid.uuid4())
    state = TicketState(ticket_id=ticket_id, channel=ticket.channel, text=ticket.text, metadata=ticket.metadata)
    llm = LLMClient()
    config = {
        "low_confidence_threshold": float(os.getenv("LOW_CONF_THRESHOLD", "0.7")),
        "high_risk_keywords": os.getenv("HIGH_RISK_KEYWORDS", "lawsuit|security breach|data leak").split("|")
    }

    # For demo purposes we run the workflow in background.
    background_tasks.add_task(run_workflow, state, llm, config)
    logger.info(f"Accepted ticket {ticket_id} for processing")
    return {"ticket_id": ticket_id, "status": "accepted"}

if __name__ == "__main__":
    uvicorn.run("services.fastapi_app:app", host="0.0.0.0", port=8000, reload=True)
