# Luthiery Phase 0 Architecture Contract

## Ownership
Crafted instruments are **character-owned unique assets**. Account/user IDs authenticate the session but are not item owners. A band may be assigned an instrument for gameplay, but band assignment never transfers ownership. Every mutation must derive the acting character from the authenticated selected-character dependency; clients must never choose or assert the owner. Legacy band-scoped routes may accept a requested band target only when server-side membership/ownership validation proves the selected character is authorised.

## Legacy gear audit
The legacy GearService stores items and ownership in process memory. Direct callers found on main:
- gear routes: craft, repair and trade.
- rehearsal service: reads band-wide rehearsal bonus.
- live performance service: reads band-wide performance bonus.
- legacy gear tests.

This service remains compatibility-only until persistent crafted items replace its consumers. New Luthiery code must not add data to its in-memory item or ownership dictionaries.

## Inventory/shop audit
Current item/shop inventory is quantity-based and already resolves the selected character in player-facing item/shop routes. This pattern is the reference for Luthiery authorization.

City/player shop stock uses shop_items quantities keyed by item_id. A crafted instrument is serialized and must not be represented as a stackable quantity. Phase 8 therefore requires a unique crafted-item listing relation referencing crafted_item_id.

The generic marketplace currently stores listing metadata but does not prove ownership of a serialized item. Luthiery listings must bind a listing to an owned crafted_item_id and transfer that exact row atomically.

## Skill audit
Seed skill IDs are currently generated from list position. Inserting skills in the middle can renumber existing skills. Luthiery skills must be appended until skill seeding is migrated to explicit stable IDs. Stable machine keys, not display labels, will be referenced by crafting rules.

## Stable key contract
Use immutable lowercase snake-case string keys for content definitions:
- material: luthier.material.<key>
- component design: luthier.component.<part>.<key>
- shape: luthier.shape.<instrument_type>.<key>
- trait: luthier.trait.<key>

Database integer primary keys may change between environments; gameplay rules and seeds must use these stable keys.

## Persistent model boundary
Phase 4 will persist:
- crafted_items: identity, owner_character_id, creator_character_id, serial, type, shape key, appearance, quality, condition and immutable creation snapshots.
- crafted_item_parts: exactly one body, neck, fretboard, electronics and hardware selection per instrument.
- crafted item modifiers/traits: final baked result.
- provenance events: transfers without rewriting creator identity.
- optional band assignment/equipment relation: separate from ownership.

## Authorization invariants
1. owner_character_id is server-derived on creation.
2. Creator identity is immutable.
3. Only the owning selected character may repair, list, transfer, rework or equip an instrument unless an explicit privileged admin path exists.
4. Band assignment requires the selected character to have appropriate band access and own the item.
5. Changing selected characters must immediately change visible/mutable crafted inventory.
6. Purchase/trade changes ownership exactly once in the same transaction as payment/listing state.
7. No endpoint accepts from_character_id or owner_character_id as authoritative client input. Legacy band_id/from_band fields are compatibility selectors only and must be validated against server-side membership and actual item ownership before mutation.

## Legacy migration
1. Do not attempt to persist process-memory legacy gear retroactively; it has no durable source of truth across restarts.
2. Keep legacy GearService consumers operational during rollout.
3. Build persistent Luthiery alongside legacy gear behind ENABLE_LUTHIERY_CRAFTING (default off).
4. Adapt rehearsal/live performance bonus aggregation to read equipped persistent crafted gear plus legacy gear during transition.
5. Once all consumers use persistent gear, deprecate legacy craft/trade routes and remove in-memory ownership.
6. Existing normal catalogue inventory remains unchanged; only uniquely crafted instruments use the serialized model.

## Phase 0 release gate
- New Luthiery persistence must follow this contract.
- Cross-character mutation tests are mandatory before enabling the feature.
- The feature flag stays off by default until the gate passes.
