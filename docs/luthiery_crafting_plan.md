# RockMundo Luthiery Crafting — Phased Implementation Plan

**Status:** Phase 5 implementation complete — Phase 4 merged; consumer activation awaits Phase 7 equipment state. Repository preflight currently blocked by unrelated missing monitoring.websocket module
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
- [ ] Novice/intermediate/master balance tests.

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
