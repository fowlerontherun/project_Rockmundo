# Attribute Effects on Skills

Avatar attributes influence how quickly skills grow and decay:

- **Creativity** boosts XP gain for creative skills such as songwriting.  The
  multiplier is `1 + creativity / 200`.
- **Charisma** boosts XP gain for performance and stage skills using
  `1 + charisma / 200`.
- **Intelligence** boosts business skill training with
  `1 + intelligence / 200`.
- **Discipline** affects all training with `1 + (discipline - 50) / 100` and
  reduces skill decay by scaling losses by `1 - discipline / 200`.

Higher attributes mean faster progression, while high discipline slows the rate
that skills fade over time.
