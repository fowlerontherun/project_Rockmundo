"""Simple moderation workflows for handling user reports and sanctions."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from backend.models.moderation import Report, Sanction, AuditLog


class ModerationService:
    def __init__(self):
        self.reports: List[Report] = []
        self.sanctions: List[Sanction] = []
        self.audit_logs: List[AuditLog] = []
        self._report_id = 1
        self._sanction_id = 1
        self._audit_id = 1

    # ----------- report handling -----------
    def file_report(self, reporter_id: int, target_id: int, reason: str) -> Report:
        report = Report(self._report_id, reporter_id, target_id, reason)
        self._report_id += 1
        self.reports.append(report)
        self.log_audit("report_filed", {"report_id": report.id})
        return report

    def get_pending_reports(self) -> List[Report]:
        return [r for r in self.reports if r.status == "pending"]

    def check_rules(self, report: Report) -> Optional[str]:
        reason = report.reason.lower()
        if "abuse" in reason:
            return "ban"
        if "spam" in reason:
            return "warning"
        return None

    def resolve_report(self, report_id: int, action: str, sanction_type: Optional[str] = None) -> Report:
        for report in self.reports:
            if report.id == report_id:
                if action == "sanction" and sanction_type:
                    self.apply_sanction(report.target_id, sanction_type, report.reason)
                    report.status = "resolved"
                    report.resolution = sanction_type
                else:
                    report.status = "dismissed"
                    report.resolution = action
                self.log_audit("report_resolved", {"report_id": report.id, "status": report.status})
                return report
        raise ValueError("report not found")

    def handle_report(self, reporter_id: int, target_id: int, reason: str) -> Report:
        report = self.file_report(reporter_id, target_id, reason)
        sanction_type = self.check_rules(report)
        if sanction_type:
            self.apply_sanction(target_id, sanction_type, reason)
            report.status = "resolved"
            report.resolution = sanction_type
        return report

    # ----------- sanctions -----------
    def apply_sanction(
        self,
        user_id: int,
        type_: str,
        reason: str,
        duration_hours: Optional[int] = None,
    ) -> Sanction:
        sanction = Sanction(self._sanction_id, user_id, type_, reason)
        if duration_hours:
            sanction.expires_at = (datetime.utcnow() + timedelta(hours=duration_hours)).isoformat()
        self._sanction_id += 1
        self.sanctions.append(sanction)
        self.log_audit(
            "sanction_applied",
            {"sanction_id": sanction.id, "user_id": user_id, "type": type_},
        )
        return sanction

    # ----------- logging -----------
    def log_audit(self, action: str, details: Dict[str, Any]) -> AuditLog:
        log = AuditLog(self._audit_id, action, details)
        self._audit_id += 1
        self.audit_logs.append(log)
        return log

    def log_suspicious_activity(self, action: str, details: Dict[str, Any]) -> AuditLog:
        return self.log_audit(f"suspicious_{action}", details)


# Shared instance for easy imports
moderation_service = ModerationService()
