"""Simple 3D performance rendering prototype.

This module demonstrates how gig completion data can drive visuals. It
uses matplotlib's 3D plotting capabilities to render a bar representing
the crowd attendance of a completed gig.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

from backend.services import gig_service


class PerformanceRenderer:
    """Render gig data in a minimal 3D scene."""

    def __init__(self) -> None:
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111, projection="3d")

    def render(self, attendance: int) -> None:
        """Render a single bar representing crowd attendance."""
        # Draw a bar whose height equals attendance
        self.ax.bar3d([0], [0], [0], 1, 1, [attendance], color="mediumseagreen")
        self.ax.set_zlim(0, max(100, attendance * 1.2))
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.set_zlabel("Attendance")
        self.ax.set_title("Gig Attendance")
        plt.show()


def render_gig(gig_id: int, db_path: str) -> None:
    """Fetch gig results and render them.

    Parameters
    ----------
    gig_id: int
        Identifier of the gig in the database.
    db_path: str
        Path to the SQLite database file containing gig records.
    """
    gig_service.DB_PATH = db_path
    result = gig_service.simulate_gig_result(gig_id)
    attendance = int(result.get("attendance", 0))
    renderer = PerformanceRenderer()
    renderer.render(attendance)
