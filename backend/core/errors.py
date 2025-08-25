# File: backend/core/errors.py
from fastapi import HTTPException, status

class AppError(Exception):
    code = "APP_ERROR"
    http_status = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str = "", *, code: str = None, http_status: int = None):
        super().__init__(message or self.code)
        if code: self.code = code
        if http_status: self.http_status = http_status
        self.message = message or self.code

    def to_http(self) -> HTTPException:
        return HTTPException(status_code=self.http_status, detail={"code": self.code, "message": self.message})

class VenueConflictError(AppError):
    code = "VENUE_CONFLICT"
    http_status = status.HTTP_409_CONFLICT

class TourMinStopsError(AppError):
    code = "TOUR_MIN_STOPS_NOT_MET"
    http_status = status.HTTP_400_BAD_REQUEST

class MailNoRecipientsError(AppError):
    code = "MAIL_NO_RECIPIENTS"
    http_status = status.HTTP_400_BAD_REQUEST
