CREATE TABLE IF NOT EXISTS tickets (
  id UUID PRIMARY KEY,
  external_id TEXT,
  channel TEXT NOT NULL,
  text TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  issue_type TEXT,
  priority TEXT,
  confidence NUMERIC,
  classification_reasoning TEXT,
  routed_team TEXT,
  jira_issue_key TEXT,
  human_review_required BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ticket_logs (
  id BIGSERIAL PRIMARY KEY,
  ticket_id UUID REFERENCES tickets(id),
  node TEXT,
  payload JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tickets_routed_team ON tickets (routed_team);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets (priority);
