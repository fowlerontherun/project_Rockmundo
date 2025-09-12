"""Service for retrieving songs available for cover licensing.

This service fetches song catalogs from partner APIs.  The partner client is
injected so it can be easily mocked in tests."""

from typing import List, Dict, Protocol


class PartnerClient(Protocol):
    """Protocol for partner API clients."""

    def fetch_catalog(self) -> List[Dict]:
        """Return a list of songs with licensing terms.

        Each song dictionary should contain at minimum ``song_id``, ``title`` and
        ``license_fee`` keys.  Additional fields from the partner API are passed
        through as-is.
        """
        ...


class DefaultPartnerClient:
    """Fallback client used when no external integration is provided."""

    def fetch_catalog(self) -> List[Dict]:
        # In production this would call out to the partner's HTTP API.  To keep
        # this module fully offline-friendly we simply return an empty catalog.
        return []


class LicensingMarketplaceService:
    """Expose a catalog of songs bands can license for covers."""

    def __init__(self, partner_client: PartnerClient | None = None) -> None:
        self.partner_client = partner_client or DefaultPartnerClient()

    def list_available_songs(self) -> List[Dict]:
        """Return songs available for cover along with fees and terms."""
        return self.partner_client.fetch_catalog()
