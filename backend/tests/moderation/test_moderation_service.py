
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from backend.services.moderation_service import ModerationService


def test_handle_report_auto_sanction():
    svc = ModerationService()
    report = svc.handle_report(1, 2, "abuse in chat")
    assert report.status == "resolved"
    assert report.resolution == "ban"
    assert len(svc.sanctions) == 1
    assert svc.sanctions[0].user_id == 2


def test_manual_sanction_flow():
    svc = ModerationService()
    report = svc.file_report(1, 3, "spam links")
    pending = svc.get_pending_reports()
    assert pending and pending[0].id == report.id
    svc.resolve_report(report.id, "sanction", "warning")
    assert svc.sanctions[-1].type == "warning"
    assert svc.reports[0].status == "resolved"

