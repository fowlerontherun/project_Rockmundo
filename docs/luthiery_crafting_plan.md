# RockMundo Luthiery Crafting — Phased Implementation Plan

**Status:** Planned
**Initial scope:** Electric guitars and electric basses
**Long-term system:** Craftsmanship professions, beginning with Luthiery
**Rule:** Complete and verify each phase before progressing.

## Vision
Build a persistent player crafting profession in which characters learn Luthiery, buy materials/components, visually assemble unique guitars and basses, use them as gear, and sell individual creations through player-owned shops. Every crafted instrument permanently retains its maker, materials, five component choices, appearance, quality, traits and gameplay modifiers.

## Existing systems to reuse
- Existing skill progression/prerequisites and learning routes.
- Gear modifiers and live-performance gear bonus integration.
- Economy/wallet transactions.
- City/player shops, marketplace, trading, payments and shipping.
- Character authentication/identity helpers.

The current GearService crafting is in-memory base-item + component crafting. It has no persistent provenance, Luthier skill calculation, material inventory or character-safe ownership. The /gear/craft route also accepts a client-supplied band_id. Reuse useful modifier concepts, but do not build the profession around this storage model.

# Phase 0 — Architecture and migration guardrails
**Goal:** Freeze the data contract and prevent competing crafting systems.

- [x] Audit every caller of GearService craft/upgrade/repair/assign/trade/bonus functions.
- [x] Audit gear/item ownership and inventory APIs.
- [x] Audit marketplace/trade/shop assumptions about stackable vs unique items.
- [x] Audit skill ranges and professional/mastery conventions.
- [x] Define crafted instruments as character-owned.
- [x] Keep optional band assignment/equipping separate from ownership.
- [x] Remove client authority over owner/band identifiers (legacy band selectors are server-validated, never trusted as ownership proof).
- [x] Document migration path for legacy crafted gear.
- [x] Define stable IDs for materials, shapes, component designs and traits.
- [x] Add Luthiery feature flag.
- [x] Add cross-character access/security tests.

**Exit:** one persistent model; no new Luthiery dependency on in-memory ownership; character-safe ownership tested.

# Phase 1 — Luthiery skills and progression
**Goal:** Make Luthiery a real skill family before production.

## Skill tree
- [x] Add Basic Luthiery under a Craftsmanship category.
- [x] Add Woodworking.
- [x] Add Fretwork.
- [x] Add Instrument Electronics.
- [x] Add Instrument Finishing.
- [x] Add Advanced Luthiery.
- [x] Add Master Luthier.
- [x] Add Legendary Luthier.
- [x] Define prerequisites/unlock levels.
- [ ] Display the tree in the player skill UI.
- [ ] Explain benefits and locked requirements.

## Learning
- [ ] Add beginner, intermediate and advanced Luthiery books.
- [ ] Add courses.
- [ ] Add video/YouTube learning.
- [ ] Add Luthier mentors/tutors.
- [ ] Ensure every skill has at least one valid learning route.
- [ ] Add professional/mastery unlock notifications.
- [ ] Add learning-path tests.

## Progression rewards
- [ ] Level-based material unlock table.
- [ ] Level-based shape unlock table.
- [ ] Level-based finish unlock table.
- [ ] Level-based component unlock table.
- [ ] Show upcoming unlocks in skill tree.

**Exit:** a new character can discover/train Luthiery; advanced skills unlock correctly; no skill is unreachable; UI shows current/upcoming unlocks.

# Phase 2 — Materials and component catalogue
**Goal:** Establish the five-part recipe and material economy.

Every guitar/bass requires exactly:
1. Body
2. Neck
3. Fretboard
4. Electronics
5. Hardware

Finish/colour is a separate customisation layer.

## Data
- [ ] Add crafting_materials.
- [ ] Add crafting_component_designs.
- [ ] Add instrument_shapes.
- [ ] Add crafting_unlocks.
- [ ] Add character material inventory.
- [ ] Add material purchase history.
- [ ] Store rarity, cost, quality and stat affinities.
- [ ] Store instrument compatibility.
- [ ] Store required skill/level.
- [ ] Add admin enable/disable controls.

## Woods/materials
- [ ] Basswood.
- [ ] Poplar.
- [ ] Alder.
- [ ] Ash.
- [ ] Maple.
- [ ] Mahogany.
- [ ] Walnut.
- [ ] Rosewood.
- [ ] Ebony.
- [ ] Flame maple.
- [ ] Quilted maple.
- [ ] Initial exotic/premium set.

## Electronics
- [ ] Standard single-coil.
- [ ] Standard humbucker.
- [ ] P-style bass pickup.
- [ ] J-style bass pickup.
- [ ] Ceramic variants.
- [ ] Alnico variants.
- [ ] Active electronics.
- [ ] Premium/boutique electronics.

## Hardware
- [ ] Standard bridge/tuners.
- [ ] Compatible tremolo bridge.
- [ ] Locking tuners.
- [ ] Touring hardware.
- [ ] Brass hardware.
- [ ] Premium lightweight hardware.

## Purchasing
- [ ] Luthier supplier/shop inventory.
- [ ] Economy-compatible stock/cost.
- [ ] Locked-material restrictions.
- [ ] Atomic money deduction + inventory addition.
- [ ] Transaction rollback.
- [ ] Material inventory UI.
- [ ] Purchase/funds/ownership tests.

**Exit:** starter inputs can be bought and persist; locked materials cannot be used early; transactions are atomic.

# Phase 3 — Shapes and visual definitions
**Goal:** Create recognisably different instruments.

## Starter
- [ ] RockMundo Strat-style variant.
- [ ] RockMundo Tele-style variant.
- [ ] Single-cut.
- [ ] Double-cut.
- [ ] P-style bass.
- [ ] J-style bass.

## Advanced
- [ ] V-style.
- [ ] Explorer-style.
- [ ] Offset.
- [ ] Modern metal.
- [ ] Headless.
- [ ] Semi-hollow.
- [ ] Extended-range guitar.
- [ ] Extended-range bass.

## Master/legendary
- [ ] Extreme asymmetric.
- [ ] Extreme horns.
- [ ] Coffin-inspired original.
- [ ] Star-inspired original.
- [ ] Extreme V.
- [ ] More fictional RockMundo signature shapes.

## Compatibility
- [ ] Body anchor points.
- [ ] Neck attachment points.
- [ ] Fretboard alignment.
- [ ] Pickup/electronics slots.
- [ ] Bridge/hardware slots.
- [ ] Combination validation.
- [ ] Missing-asset fallback.

**Exit:** starter combinations render correctly; locks show requirements; no floating/detached parts.

# Phase 4 — Persistent crafting engine and quality
**Goal:** Produce a unique persistent instrument.

## Persistence
- [ ] Add crafted_items.
- [ ] Add crafted_item_parts.
- [ ] Add crafting_jobs if builds consume scheduled time.
- [ ] Permanent creator character ID.
- [ ] Creation timestamp.
- [ ] Unique serial number.
- [ ] Instrument type/shape.
- [ ] Five component/material selections.
- [ ] Colour/finish.
- [ ] Crafting skill snapshot.
- [ ] Workshop/tool snapshot.
- [ ] Final quality/tier.
- [ ] Generated traits.
- [ ] Final stat modifiers.
- [ ] Permanent resale provenance.

## Initial quality model
Target weighting:
- 35% Luthiery skill.
- 35% materials/components.
- 15% specialist skills.
- 10% workshop/tools.
- 5% controlled craftsmanship variance.

- [ ] Server-authoritative calculation.
- [ ] Skill-based quality floor/ceiling.
- [ ] Premium materials cannot bypass low skill.
- [ ] Masters can make strong instruments from ordinary materials.
- [ ] Tiers: Poor, Basic, Good, Excellent, Professional, Masterwork, Legendary.
- [ ] Novice/intermediate/master balance tests.

## Imperfection
- [ ] Prefer imperfect output over destructive random failure.
- [ ] Low-skill defect chance.
- [ ] Material waste rules.
- [ ] Repair/rework rules.
- [ ] Prevent reroll exploits.

**Exit:** controlled variation works; skill/materials matter; results survive restart; no duplication exploit.

# Phase 5 — Stats and unique traits
**Goal:** Make construction choices meaningful without one universal best build.

- [ ] Characteristics: Tone, Sustain, Clarity, Output, Playability, Reliability, Durability, Stage Impact.
- [ ] Gameplay modifiers: performance quality, instrument effectiveness, recording quality, practice effectiveness, stage presence, audience reaction, reliability.
- [ ] Carefully balanced genre affinities where useful.
- [ ] Traits: Exceptional Sustain, Perfectly Balanced, Hot Pickups, Studio Clean, Road Warrior, Vintage Character, Heavyweight, Temperamental Electronics.
- [ ] Add more positive/neutral/negative traits.
- [ ] Weight traits by materials, skills and quality.
- [ ] Prevent conflicting traits.
- [ ] Integrate modifiers with rehearsal/gig/recording consumers.

**Exit:** builds have different profiles; no universal best combination; existing gameplay consumes modifiers.

# Phase 6 — Visual Luthier Workshop
**Goal:** Make crafting a visible interactive build process.

- [ ] Large persistent live preview.
- [ ] Build rail: Body → Neck → Fretboard → Electronics → Hardware → Finish.
- [ ] Preview remains visible while changing options.
- [ ] Click/tap parts to select/place them.
- [ ] Rotate/zoom.
- [ ] Mobile controls.
- [ ] Desktop layout.
- [ ] Accessible controls.
- [ ] Material/shape thumbnails.
- [ ] Locked choices remain visible with requirement.
- [ ] Cost and owned quantity.
- [ ] Estimated quality range.
- [ ] Predicted characteristic changes.
- [ ] Rare-material warning.
- [ ] Primary/accent/body colour.
- [ ] Hardware colour.
- [ ] Natural, solid, transparent, metallic finishes.
- [ ] Gloss/matte.
- [ ] Advanced finishes gated by Instrument Finishing.
- [ ] Final build review.
- [ ] Player names instrument.
- [ ] Confirm material consumption.
- [ ] Craft/reveal quality and traits.
- [ ] Show maker/serial plate.
- [ ] Add to character inventory.

**Exit:** full build works without reload; preview matches saved result; mobile/desktop usable.

# Phase 7 — Equip, use and display
- [ ] Crafted instruments appear in character inventory.
- [ ] Equip to compatible role.
- [ ] Display crafted appearance where visuals support it.
- [ ] Apply modifiers to rehearsals, gigs, recording and relevant practice.
- [ ] Durability/condition.
- [ ] Repair/maintenance.
- [ ] Full item provenance page.
- [ ] Permanent maker and serial.
- [ ] Five-part specification/materials.
- [ ] Quality/traits/date.
- [ ] Favourite/lock to prevent accidental sale.
- [ ] Character-switch safety tests.

**Exit:** crafted gear replaces ordinary gear in normal gameplay safely and bonuses cannot duplicate/stack incorrectly.

# Phase 8 — Player Luthier shops
**Goal:** Turn Luthiery into a player business.

- [ ] Allow eligible players to operate/configure an instrument shop.
- [ ] Reuse existing player-shop ownership.
- [ ] Support individually serialized stock.
- [ ] List/delist unique instrument.
- [ ] Set asking price.
- [ ] Preview exact instrument.
- [ ] Show maker, serial, quality, traits, stats, specification and condition.
- [ ] Atomic money + ownership transfer.
- [ ] Existing taxes/fees where appropriate.
- [ ] Sales history and revenue reporting.
- [ ] Shipping/location integration where required.
- [ ] Marketplace discovery/search.
- [ ] Race-condition tests for duplicate purchase.

**Exit:** one player can craft/list/sell and another receives the exact serialized item; provenance survives resale.

# Phase 9 — Luthier reputation and collectibles
- [ ] Luthier reputation.
- [ ] Reputation from legitimate sales.
- [ ] Reputation when notable/high-fame musicians use an instrument.
- [ ] Reputation from high-quality builds.
- [ ] Anti-farming/diminishing returns.
- [ ] Maker reputation on listings.
- [ ] Provenance/history log.
- [ ] Track notable owners.
- [ ] Track notable gigs/recordings where practical.
- [ ] Collector/desirability signal.
- [ ] Luthier achievements.
- [ ] Signature/masterpiece milestones.
- [ ] Later: custom commissions.

**Exit:** Luthiery supports a long-term career loop and historic instruments retain provenance.

# Phase 10 — Admin, balancing and live operations
- [ ] Material/component/shape catalogues.
- [ ] Unlock-level controls.
- [ ] Material price/supply controls.
- [ ] Quality weighting controls.
- [ ] Trait controls.
- [ ] Crafted-item lookup by serial.
- [ ] Ownership/provenance audit.
- [ ] Economy/craft/material/quality/sales metrics.
- [ ] Suspicious crafting/trading detection.
- [ ] Feature flags for advanced content.

# Phase 11 — QA and release gate
## Security/integrity
- [ ] Cross-character access.
- [ ] Forged owner/band IDs.
- [ ] Duplicate craft submissions.
- [ ] Duplicate purchases.
- [ ] Transaction rollback.
- [ ] Material duplication.
- [ ] Stat tampering.
- [ ] Shop ownership.

## Gameplay/UX
- [ ] Novice/intermediate/master progression.
- [ ] Guitar and bass builds.
- [ ] Locked materials/shapes.
- [ ] Equip/rehearsal/gig/recording.
- [ ] Repair/condition.
- [ ] Resale/provenance.
- [ ] Desktop/mobile workshop.
- [ ] Slow network/retry.
- [ ] Refresh/reload.
- [ ] Character switching.
- [ ] Missing visual fallback.

## Economy
- [ ] Starter materials affordable.
- [ ] Premium materials meaningful money sinks.
- [ ] Crafted gear does not immediately obsolete NPC gear.
- [ ] Player shops can make viable margins.
- [ ] No trivial infinite-money loop.

## Release gate
- [ ] Phase 1–8 exit criteria passed.
- [ ] No critical ownership/economy exploit.
- [ ] Balance telemetry enabled.
- [ ] Admin emergency disable available.
- [ ] Production migration tested.

# Initial release content target
- [ ] Electric guitars and basses.
- [ ] Exactly five construction parts.
- [ ] 25–35 useful material/component choices.
- [ ] At least 8–10 shapes.
- [ ] Multiple colours/finishes.
- [ ] Skill-gated materials and shapes.
- [ ] Persistent unique quality/traits/modifiers.
- [ ] Visual workshop.
- [ ] Character inventory/equipping.
- [ ] Player Luthier shop sales.
- [ ] Permanent maker/serial provenance.

# Future Craftsmanship professions
Do not implement during initial Luthiery release, but keep architecture reusable for drum building, amplifiers/electronics, effects pedals, synth/keyboards, stage equipment, fashion/clothing, jewellery/accessories and other player-manufactured items.

# Recommended implementation order
1. Phase 0 — architecture/ownership.
2. Phase 1 — skills.
3. Phase 2 — materials/components.
4. Phase 4 — persistent crafting engine.
5. Phase 5 — stats/traits.
6. Phase 3 — full shape/visual catalogue.
7. Phase 6 — interactive workshop.
8. Phase 7 — gameplay integration.
9. Phase 8 — player shops.
10. Phase 9 — reputation/collectibles.
11. Phase 10/11 — live-ops, balance and hardening.

Persistence, security and game rules intentionally come before heavy visual work.
