"""Configuration values for lifestyle decay and XP modifiers.

Centralising these values makes it easy to tweak balance for the lifestyle
system without touching the core scheduling logic.  Admin routes can mutate
these dictionaries at runtime for live tuning.
"""

# Daily decay values applied to lifestyle attributes.
DECAY = {
    "mental_health": 1.0,
    "stress": 1.5,
    "training_discipline": 0.5,
}

# Thresholds for XP modifiers. Each entry defines either a minimum or maximum
# threshold that triggers a multiplier when violated.
MODIFIER_THRESHOLDS = {
    "sleep_hours": {"min": 5, "modifier": 0.7},
    "stress": {"max": 80, "modifier": 0.75},
    "training_discipline": {"min": 30, "modifier": 0.85},
    "mental_health": {"min": 60, "modifier": 0.8},
    "nutrition": {"min": 40, "modifier": 0.9},
    "fitness": {"min": 30, "modifier": 0.9},
}

