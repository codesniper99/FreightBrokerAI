-- db/init/003_events.sql
CREATE TABLE IF NOT EXISTS events (
  id            BIGSERIAL PRIMARY KEY,
  ts            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  source        TEXT NOT NULL,                 -- e.g., 'webhook', 'api'
  name          TEXT NOT NULL,                 -- e.g., 'secure-test', 'inbound-call'
  status        TEXT,                          -- e.g., 'ok', 'error'
  duration_ms   INTEGER,                       -- optional timing
  user_id       TEXT,                          -- optional
  agent         TEXT,                          -- optional
  route         TEXT,                          -- e.g., '/webhook'
  payload       JSONB                          -- raw or trimmed input
);

-- simple indexes for common filters
CREATE INDEX IF NOT EXISTS idx_events_ts ON events (ts DESC);
CREATE INDEX IF NOT EXISTS idx_events_source ON events (source);
CREATE INDEX IF NOT EXISTS idx_events_name ON events (name);