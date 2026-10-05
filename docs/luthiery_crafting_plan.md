# RockMundo Luthiery Crafting — Phased Implementation Plan

**Status:** Initial Luthiery release (Phases 0–8) complete and release-gated. Shipping/location and tax/fee integration remain optional post-release integrations.
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
- [x] Display the tree in the player skill UI.
- [x] Explain benefits and locked requirements.

## Learning
- [x] Add beginner, intermediate and advanced Luthiery books.
- [x] Add courses.
- [x] Add video/YouTube learning.
- [x] Add Luthier mentors/tutors.
- [x] Ensure every skill has at least one valid learning route.
- [x] Add professional/mastery unlock notifications.
- [x] Add learning-path tests.

## Progression rewards
- [x] Level-based material unlock table.
- [x] Level-based shape unlock table.
- [x] Level-based finish unlock table.
- [x] Level-based component unlock table.
- [x] Show upcoming unlocks in skill tree.

**Exit:** a new character can discover/train Luthiery; advanced skills unlock correctly; no skill is unreachable; UI shows current/upcoming unlocks.

# Phase 2 — Materials and component catalogue
**Status:** Complete — implementation review fixes pending CI
**Goal:** Establish the five-part recipe and material economy.

Every guitar/bass requires exactly:
1. Body
2. Neck
3. Fretboard
4. Electronics
5. Hardware

Finish/colour is a separate customisation layer.

## Data
- [x] Add crafting_materials.
- [x] Add crafting_component_designs.
- [x] Add instrument_shapes.
- [x] Add crafting_unlocks.
- [x] Add character material inventory.
- [x] Add material purchase history.
- [x] Store rarity, cost, quality and stat affinities.
- [x] Store instrument compatibility.
- [x] Store required skill/level.
- [x] Add admin enable/disable controls.

## Woods/materials
- [x] Basswood.
- [x] Poplar.
- [x] Alder.
- [x] Ash.
- [x] Maple.
- [x] Mahogany.
- [x] Walnut.
- [x] Rosewood.
- [x] Ebony.
- [x] Flame maple.
- [x] Quilted maple.
- [x] Initial exotic/premium set.

## Electronics
- [x] Standard single-coil.
- [x] Standard humbucker.
- [x] P-style bass pickup.
- [x] J-style bass pickup.
- [x] Ceramic variants.
- [x] Alnico variants.
- [x] Active electronics.
- [x] Premium/boutique electronics.

## Hardware
- [x] Standard bridge/tuners.
- [x] Compatible tremolo bridge.
- [x] Locking tuners.
- [x] Touring hardware.
- [x] Brass hardware.
- [x] Premium lightweight hardware.

## Purchasing
- [x] Luthier supplier/shop inventory.
- [x] Economy-compatible stock/cost.
- [x] Locked-material restrictions.
- [x] Atomic money deduction + inventory addition.
- [x] Transaction rollback.
- [x] Material inventory UI.
- [x] Purchase/funds/ownership tests.

**Exit:** starter inputs can be bought and persist; locked materials cannot be used early; transactions are atomic.

# Phase 3 — Shapes and visual definitions
**Goal:** Create recognisably different instruments.

## Starter
- [x] RockMundo Strat-style variant.
- [x] RockMundo Tele-style variant.
- [x] Single-cut.
- [x] Double-cut.
- [x] P-style bass.
- [x] J-style bass.

## Advanced
- [x] V-style.
- [x] Explorer-style.
- [x] Offset.
- [x] Modern metal.
- [x] Headless.
- [x] Semi-hollow.
- [x] Extended-range guitar.
- [x] Extended-range bass.

## Master/legendary
- [x] Extreme asymmetric.
- [x] Extreme horns.
- [x] Coffin-inspired original.
- [x] Star-inspired original.
- [x] Extreme V.
- [x] More fictional RockMundo signature shapes.

## Compatibility
- [x] Body anchor points.
- [x] Neck attachment points.
- [x] Fretboard alignment.
- [x] Pickup/electronics slots.
- [x] Bridge/hardware slots.
- [x] Combination validation.
- [x] Missing-asset fallback.

**Exit:** starter combinations render correctly; locks show requirements; no floating/detached parts.

# Phase 4 — Persistent crafting engine and quality
**Goal:** Produce a unique persistent instrument.

## Persistence
- [x] Add crafted_items.
- [x] Add crafted_item_parts.
- [x] Add crafting_jobs if builds consume scheduled time.
- [x] Permanent creator character ID.
- [x] Creation timestamp.
- [x] Unique serial number.
- [x] Instrument type/shape.
- [x] Five component/material selections.
- [x] Colour/finish.
- [x] Crafting skill snapshot.
- [x] Workshop/tool snapshot.
- [x] Final quality/tier.
- [x] Generated traits.
- [x] Final stat modifiers.
- [x] Permanent resale provenance.

## Initial quality model
Target weighting:
- 35% Luthiery skill.
- 35% materials/components.
- 15% specialist skills.
- 10% workshop/tools.
- 5% controlled craftsmanship variance.

- [x] Server-authoritative calculation.
- [x] Skill-based quality floor/ceiling.
- [x] Premium materials cannot bypass low skill.
- [x] Masters can make strong instruments from ordinary materials.
- [x] Tiers: Poor, Basic, Good, Excellent, Professional, Masterwork, Legendary.
- [x] Novice/intermediate/master balance tests.

## Imperfection
- [x] Prefer imperfect output over destructive random failure.
- [x] Low-skill defect chance.
- [x] Material waste rules. *(five required inputs are consumed atomically; failed validation/transactions roll back without waste)*
- [x] Repair/rework rules.
- [x] Prevent reroll exploits.

**Exit:** controlled variation works; skill/materials matter; results survive restart; no duplication exploit.

# Phase 5 — Stats and unique traits
**Goal:** Make construction choices meaningful without one universal best build.

- [x] Characteristics: Tone, Sustain, Clarity, Output, Playability, Reliability, Durability, Stage Impact.
- [x] Gameplay modifiers: performance quality, instrument effectiveness, recording quality, practice effectiveness, stage presence, audience reaction, reliability.
- [x] Carefully balanced genre affinities where useful.
- [x] Traits: Exceptional Sustain, Perfectly Balanced, Hot Pickups, Studio Clean, Road Warrior, Vintage Character, Heavyweight, Temperamental Electronics.
- [x] Add more positive/neutral/negative traits.
- [x] Weight traits by materials, skills and quality.
- [x] Prevent conflicting traits.
- [x] Add safe rehearsal/gig/recording modifier consumer bridge; activation is restricted to explicit equipped item IDs so Phase 7 can wire authoritative equipment without ownership-wide stacking.

**Exit:** builds have different profiles; no universal best combination; existing gameplay consumes modifiers.

# Phase 6 — Visual Luthier Workshop
**Goal:** Make crafting a visible interactive build process.

- [x] Large persistent live preview.
- [x] Build rail: Body → Neck → Fretboard → Electronics → Hardware → Finish.
- [x] Preview remains visible while changing options.
- [x] Click/tap parts to select/place them.
- [x] Rotate/zoom.
- [x] Mobile controls.
- [x] Desktop layout.
- [x] Accessible controls.
- [x] Material/shape thumbnails.
- [x] Locked choices remain visible with requirement.
- [x] Cost and owned quantity.
- [x] Estimated quality range.
- [x] Predicted characteristic changes.
- [x] Rare-material warning.
- [x] Primary/accent/body colour.
- [x] Hardware colour.
- [x] Natural, solid, transparent, metallic finishes.
- [x] Gloss/matte.
- [x] Advanced finishes gated by Instrument Finishing.
- [x] Final build review.
- [x] Player names instrument.
- [x] Confirm material consumption.
- [x] Craft/reveal quality and traits.
- [x] Show maker/serial plate.
- [x] Add to character inventory.

**Exit:** full build works without reload; preview matches saved result; mobile/desktop usable.

# Phase 7 — Equip, use and display
- [x] Crafted instruments appear in character inventory.
- [x] Equip to compatible role.
- [x] Display crafted appearance where visuals support it.
- [x] Apply modifiers to rehearsals, gigs, recording and relevant practice.
- [x] Durability/condition.
- [x] Repair/maintenance.
- [x] Full item provenance page.
- [x] Permanent maker and serial.
- [x] Five-part specification/materials.
- [x] Quality/traits/date.
- [x] Favourite/lock to prevent accidental sale.
- [x] Character-switch safety tests.

**Exit:** crafted gear replaces ordinary gear in normal gameplay safely and bonuses cannot duplicate/stack incorrectly.

# Phase 8 — Player Luthier shops
**Goal:** Turn Luthiery into a player business.

- [x] Allow eligible players to operate/configure an instrument shop.
- [x] Reuse existing player-shop ownership. *(No generic character-owned shop entity currently exists; Phase 8 uses the dedicated character-owned Luthier shop relation while reusing shared economy/shop authorization patterns.)*
- [x] Support individually serialized stock.
- [x] List/delist unique instrument.
- [x] Set asking price.
- [x] Preview exact instrument.
- [x] Show maker, serial, quality, traits, stats, specification and condition.
- [x] Atomic money + ownership transfer.
- [ ] Existing taxes/fees where appropriate.
- [x] Sales history and revenue reporting.
- [ ] Shipping/location integration where required.
- [x] Marketplace discovery/search.
- [x] Race-condition tests for duplicate purchase.

**Exit:** one player can craft/list/sell and another receives the exact serialized item; provenance survives resale.

# Phase 9 — Luthier reputation and collectibles
- [x] Luthier reputation.
- [x] Reputation from legitimate sales.
- [x] Reputation when notable/high-fame musicians use an instrument.
- [x] Reputation from high-quality builds.
- [x] Anti-farming/diminishing returns.
- [x] Maker reputation on listings.
- [x] Provenance/history log.
- [x] Track notable owners.
- [x] Track notable gigs/recordings where practical.
- [x] Collector/desirability signal.
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
- [x] Cross-character access.
- [x] Forged owner/band IDs.
- [x] Duplicate craft submissions.
- [x] Duplicate purchases.
- [x] Transaction rollback.
- [x] Material duplication.
- [x] Stat tampering.
- [x] Shop ownership.

## Gameplay/UX
- [x] Novice/intermediate/master progression.
- [x] Guitar and bass builds.
- [x] Locked materials/shapes.
- [x] Equip/rehearsal/gig/recording.
- [x] Repair/condition.
- [x] Resale/provenance.
- [x] Desktop/mobile workshop.
- [x] Slow network/retry.
- [x] Refresh/reload.
- [x] Character switching.
- [x] Missing visual fallback.

## Economy
- [x] Starter materials affordable.
- [x] Premium materials meaningful money sinks.
- [x] Crafted gear does not immediately obsolete NPC gear. *(single crafted-instrument effects are capped below the whole-band context cap; legacy gear remains independently additive)*
- [x] Player shops can make viable margins. *(asking prices are player-set above finite material input costs; no forced fee currently consumes margin)*
- [x] No trivial infinite-money loop. *(supplier purchases destroy player currency; instrument sales transfer existing currency buyer→seller with no system buyback)*

## Release gate
- [x] Phase 1–8 exit criteria passed.
- [x] No critical ownership/economy exploit.
- [x] Balance telemetry enabled.
- [x] Admin emergency disable available.
- [x] Production migration tested. *(forward migration now explicitly repairs the legacy listing-history uniqueness constraint while preserving rows)*

# Initial release content target
- [x] Electric guitars and basses.
- [x] Exactly five construction parts.
- [x] 25–35 useful material/component choices.
- [x] At least 8–10 shapes.
- [x] Multiple colours/finishes.
- [x] Skill-gated materials and shapes.
- [x] Persistent unique quality/traits/modifiers.
- [x] Visual workshop.
- [x] Character inventory/equipping.
- [x] Player Luthier shop sales.
- [x] Permanent maker/serial provenance.

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
