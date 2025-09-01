import json
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List

DATA_PATH = Path(__file__).with_name("performance_events.json")
FEEDBACK_PATH = Path(__file__).with_name("setlist_feedback.json")


class SetlistOptimizer:
    """Simple optimizer trained on past performance events.

    Each performance event should provide tempo, crowd reaction and energy
    for a given song. Training aggregates the average of these metrics per
    song, which is later used to sort songs according to a chosen
    objective.
    """

    def __init__(self) -> None:
        self.song_stats: Dict[str, Dict[str, float]] = {}
        self._load_feedback()
        self.train([])

    def train(self, events: Iterable[Dict[str, float]]) -> None:
        """Train the model from an iterable of performance events.

        Each event is expected to contain the keys ``song``, ``tempo``,
        ``crowd_reaction`` and ``energy``.
        """
        songs: Dict[str, List[Dict[str, float]]] = {}

        # Include any previously recorded feedback as additional events
        feedback_events = self.feedback.get("events", [])
        for event in list(events) + feedback_events:
            song_id = event["song"]
            songs.setdefault(song_id, []).append(event)

        for song_id, entries in songs.items():
            self.song_stats[song_id] = {
                "tempo": mean(e["tempo"] for e in entries),
                "crowd": mean(e["crowd_reaction"] for e in entries),
                "energy": mean(e["energy"] for e in entries),
            }

        # Persist aggregated stats for transparency
        DATA_PATH.write_text(json.dumps(self.song_stats, indent=2))

    def recommend(self, songs: List[str], objective: str = "crowd_energy") -> List[str]:
        """Return a recommended ordering of ``songs`` based on ``objective``."""
        if objective == "fame_gain":
            key = lambda s: self.song_stats.get(s, {}).get("crowd", 0.0)
        else:  # crowd_energy
            key = lambda s: self.song_stats.get(s, {}).get("energy", 0.0)
        return sorted(songs, key=key, reverse=True)

    # -- feedback handling -------------------------------------------------
    def _load_feedback(self) -> None:
        if FEEDBACK_PATH.exists():
            self.feedback = json.loads(FEEDBACK_PATH.read_text())
        else:
            self.feedback = {"comparisons": [], "events": []}

    def record_feedback(
        self, selected: List[str], recommended: List[str], objective: str
    ) -> None:
        """Persist chosen vs. recommended orders for future training."""
        self.feedback["comparisons"].append(
            {
                "selected": selected,
                "recommended": recommended,
                "objective": objective,
            }
        )
        FEEDBACK_PATH.write_text(json.dumps(self.feedback, indent=2))


optimizer = SetlistOptimizer()
