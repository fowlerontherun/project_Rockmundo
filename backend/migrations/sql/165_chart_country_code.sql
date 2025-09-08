-- Add country_code column to chart_snapshots to support country-specific charts
ALTER TABLE chart_snapshots ADD COLUMN country_code TEXT;
CREATE INDEX IF NOT EXISTS ix_charts_country ON chart_snapshots(country_code);
