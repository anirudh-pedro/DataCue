from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from services.otp_service import (
    EmailDispatchError,
    EmailNotConfiguredError,
    get_otp_service,
)

router = APIRouter(prefix="/otp", tags=["otp"])


class SendOtpRequest(BaseModel):
    email: EmailStr


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str


@router.post("/send")
def send_otp(payload: SendOtpRequest) -> dict[str, str | bool]:
    service = get_otp_service()
    try:
        service.send_code(payload.email)
    except EmailNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except EmailDispatchError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return {"success": True, "message": "OTP sent successfully"}


@router.post("/verify")
def verify_otp(payload: VerifyOtpRequest) -> dict[str, str | bool]:
    service = get_otp_service()
    is_valid = service.verify_code(payload.email, payload.otp)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
    return {"success": True, "message": "OTP verified successfully"}


@router.get("/health")
def otp_health() -> dict[str, int | str]:
    service = get_otp_service()
    return {"status": "ok", "activeOtps": service.active_count()}
