# Migration Notes

## Irreversible Migrations

- **0022_100_song_licensing**: Adds `license_fee` and `royalty_rate` columns to the `songs` table. SQLite lacks straightforward support for dropping columns prior to v3.35 and doing so would require recreating the table and migrating data, which is unsafe for production. The migration therefore only drops the `cover_royalties` table during downgrade and leaves the added columns in place.

All other migrations include downgrade steps that fully reverse their schema changes.
