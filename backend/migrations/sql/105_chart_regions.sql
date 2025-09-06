-- Add region column to chart_snapshots to support regional charts
ALTER TABLE chart_snapshots ADD COLUMN region TEXT DEFAULT 'global';
CREATE INDEX IF NOT EXISTS ix_charts_region ON chart_snapshots(region);
