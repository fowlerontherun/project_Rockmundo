.PHONY: migrate db-reset

# Run database migrations
migrate:
	scripts/migrate.sh

# Drop the SQLite database, recreate it, and apply migrations
# Useful during development to start with a clean schema
# Uses migrate.sh which skips already-applied revisions.
db-reset:
	rm -f rockmundo.db
	scripts/migrate.sh
