"""Centralized revenue configuration for payouts.

This module defines per-channel rates and default split rules used across
services and jobs.  Keeping these values in one place makes it easy to
maintain consistency whenever business terms change.
"""

# -------- Royalty channel configuration --------
# Per-stream rate expressed in microcents (1/100th of a cent).
STREAM_RATE_MICROCENTS = 30000  # 0.30 cents per stream

# Anti-fraud cap for counting streams per user/song/day.
DAILY_STREAM_CAP_PER_USER_PER_SONG = 50

# -------- Sponsorship channel configuration --------
# Revenue generated per ad impression in cents.
SPONSOR_IMPRESSION_RATE_CENTS = 2

# Default revenue split percentages for sponsorship payouts.
# Values represent percentage of gross sponsorship revenue.
SPONSOR_PAYOUT_SPLIT = {
    "venue": 80,      # share that goes to the venue/artist
    "platform": 20,   # platform's retained share
}
