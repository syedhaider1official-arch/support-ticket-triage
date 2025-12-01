# Automating Support Ticket Triage with LangGraph

Product: SignalDesk AI (AI-powered support workflow engine for SaaS companies)  
Core Tech: LangGraph, Python, FastAPI, PostgreSQL, Redis, Azure OpenAI, Slack & Jira APIs

## 1. Problem Statement
SignalDesk centralizes customer support from email, in-app chat, and integrations. As usage grew:
- Agents spent 4–6 hours per day manually sorting and routing tickets.
- Priority labels were inconsistent (different agents triaged differently).
- Critical incidents (P0/P1) didn’t always reach the right team quickly.

Business impact:
- Wasted expert time on repetitive triage work.
- Unpredictable response times and SLA risk.
- Frustrated customers during incidents and launches.

Goal: Automate most of the triage workflow using AI, while keeping humans in control for sensitive or ambiguous cases and maintaining full transparency into “why” a ticket was handled a certain way.

## 2. Solution Overview (LangGraph-Based Workflow)
We implemented a LangGraph-driven ticket triage workflow that:
- Ingests tickets from multiple channels into a unified format.
- Classifies issue type (Bug, Billing, Feature Request, Account, Other) and priority (P0–P3) using an LLM.
- Applies business rules (enterprise, SLA, confidence thresholds).
- Routes tickets to the correct team (Backend, Frontend, Billing, Product, Customer Success).
- Sends ambiguous / high-risk tickets to a human for review in Slack.
- Optionally generates auto-reply drafts for simple, low-priority tickets.

LangGraph lets us model this as a stateful graph: each node (LLM, policy, routing, human review) reads and updates a shared TicketState, making the workflow debuggable and extensible.

## 3. System Integration
- Backend: FastAPI microservice hosting LangGraph workflows; async endpoints, Pydantic models.
- Data Layer: PostgreSQL for tickets/labels/logs; Redis for caching and task queues.
- External Integrations:
  - Slack – human-in-the-loop review & notifications.
  - Jira – engineering tickets.
  - Internal APIs – ticket creation/status & UI integration.
- Deployment: Dockerized services, deployed to Azure Container Apps; Prometheus + Grafana for metrics (throughput, latency, error rates).

## 4. Outcomes
Over ~8 weeks of staged rollout and A/B testing:
- Triage time per ticket: ~3 minutes → < 10 seconds.
- Manual triage effort: ~35–40 hours/week saved across the support team.
- P0/P1 handling: Critical tickets reached the right team 2.5× faster; 90th percentile first-response time improved by ~32%.
- Consistency: Label disagreement rate dropped from 23% → 7%.
- Scalability: Handled 5× traffic spikes during launches with no additional headcount.

## 5. Where to look in this repo
- workflows/langgraph_workflow.py — example workflow and TicketState model.
- services/fastapi_app.py — FastAPI ingestion endpoint that invokes the workflow (demo).
- db/schema.sql — Postgres schema for tickets and logs.
- slack/slack_review_card.json — Example Slack Block Kit payload for one-click review.
- .env.example — environment variables used by the services.
- Dockerfile — simple container setup.

## 6. How it works (high level)
1. Ingest: Tickets arrive via webhook / connector and are normalized into a Ticket payload.
2. Enqueue: Ticket placed into Redis queue (or processed immediately for low-volume setups).
3. LangGraph Workflow: Stateful graph executes nodes (classification → business rules → routing → human-review or auto-reply).
4. Integrations: Slack/Jira/UI updates applied based on routing decisions.
5. Persist: TicketState and logs stored in PostgreSQL for auditability.

## 7. Next steps to enable this in your environment
1. Populate `.env` from `.env.example` with secrets and connection strings.
2. Create the DB schema: `psql $DATABASE_URL -f db/schema.sql`
3. Build and run the container locally: `docker build -t sd-triage . && docker run --env-file .env -p 8000:8000 sd-triage`
4. Wire ticket webhooks (email/chat) to `POST /ingest` endpoint or enqueue to Redis.
5. Configure Slack/Jira credentials and test the human-review flow.

## 8. Contact / Feedback loop
- When agents flag misroutes, those records feed a feedback table used to retrain or tune prompts/policies every few weeks.
