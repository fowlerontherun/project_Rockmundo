"""Routes for querying admin audit logs."""
from fastapi import APIRouter, Depends

from auth.dependencies import get_current_user_id, require_permission
from services.admin_audit_service import (
    AdminAuditService,
    audit_dependency,
    get_admin_audit_service,
)

router = APIRouter(
    prefix="/audit", tags=["AdminAudit"], dependencies=[Depends(audit_dependency)]
)


@router.get("/")
async def list_audit_logs(
    skip: int = 0,
    limit: int = 100,
    admin_id: int = Depends(get_current_user_id),
    svc: AdminAuditService = Depends(get_admin_audit_service),
):
    await require_permission(["admin"], admin_id)
    return svc.query(skip, limit)
