-- EclipseGlasses quote-request storage.
-- Run this against the Cloudflare D1 database bound to the Worker as DB.

CREATE TABLE IF NOT EXISTS quotes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  quote_number TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  quantity INTEGER NOT NULL,
  message TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'new'
);

CREATE INDEX IF NOT EXISTS idx_quotes_created_at
  ON quotes (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_quotes_status
  ON quotes (status);
