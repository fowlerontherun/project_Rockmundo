"""Service layer for managing player support tickets."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from utils.db import get_conn


class SupportServiceError(Exception):
    """Raised when support ticket operations fail."""


class SupportService:
    """Simple CRUD helpers for support tickets."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    # ------------------------------------------------------------------
    # Ticket creation
    # ------------------------------------------------------------------
    def create(self, user_id: int, subject: str, body: str) -> int:
        """Create a new support ticket.

        Parameters
        ----------
        user_id:
            Identifier of the user creating the ticket.
        subject:
            Brief title describing the issue.
        body:
            Detailed description of the problem.

        Returns
        -------
        int
            The id of the newly created ticket.

        Raises
        ------
        SupportServiceError
            If ``subject`` or ``body`` are empty.
        """

        if not subject.strip():
            raise SupportServiceError("subject is required")
        if not body.strip():
            raise SupportServiceError("body is required")

        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO support_tickets (user_id, subject, body)
                VALUES (?, ?, ?)
                """,
                (user_id, subject, body),
            )
            ticket_id = int(cur.lastrowid)

        return ticket_id

    # ------------------------------------------------------------------
    # Ticket listing
    # ------------------------------------------------------------------
    def list(
        self,
        *,
        user_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Return support tickets.

        Parameters
        ----------
        user_id:
            When provided, only tickets created by this user are returned.
        limit, offset:
            Basic pagination controls.
        """

        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            sql = (
                "SELECT id, user_id, subject, body, status, created_at, resolved_at "
                "FROM support_tickets"
            )
            params: List[Any] = []
            if user_id is not None:
                sql += " WHERE user_id = ?"
                params.append(user_id)
            sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Ticket resolution
    # ------------------------------------------------------------------
    def resolve(self, ticket_id: int) -> bool:
        """Mark the ticket as resolved.

        Parameters
        ----------
        ticket_id:
            Identifier of the ticket to resolve.

        Returns
        -------
        bool
            ``True`` if the ticket was updated.

        Raises
        ------
        SupportServiceError
            If the ticket does not exist or is already resolved.
        """

        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            # Ensure the ticket exists and is still open
            cur.execute(
                "SELECT id FROM support_tickets WHERE id = ? AND status != 'resolved'",
                (ticket_id,),
            )
            if cur.fetchone() is None:
                raise SupportServiceError("ticket not found or already resolved")

            cur.execute(
                """
                UPDATE support_tickets
                SET status = 'resolved', resolved_at = datetime('now')
                WHERE id = ?
                """,
                (ticket_id,),
            )
            return True

