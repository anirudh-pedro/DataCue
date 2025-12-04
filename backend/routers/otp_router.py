"""OTP and email verification endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import random
import string
from datetime import datetime, timedelta
from typing import Dict

router = APIRouter(prefix="/otp", tags=["OTP"])

# In-memory OTP storage (use Redis in production)
otp_store: Dict[str, dict] = {}


class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerification(BaseModel):
    email: EmailStr
    otp: str


def generate_otp(length: int = 6) -> str:
    """Generate a random numeric OTP."""
    return ''.join(random.choices(string.digits, k=length))


@router.post("/send")
async def send_otp(request: OTPRequest):
    """
    Generate and send OTP to email.
    In production, this should integrate with your email service.
    """
    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Store OTP with expiration
    otp_store[request.email] = {
        "otp": otp,
        "expires_at": expires_at,
        "attempts": 0
    }
    
    # For development only - integrate email service in production
    return {
        "message": "OTP sent successfully",
        "email": request.email,
        "otp": otp,  # Remove this in production!
        "expires_in_minutes": 10
    }


@router.post("/verify")
async def verify_otp(verification: OTPVerification):
    """Verify OTP for email."""
    email = verification.email
    
    if email not in otp_store:
        raise HTTPException(status_code=404, detail="No OTP found for this email")
    
    stored_data = otp_store[email]
    
    # Check expiration
    if datetime.utcnow() > stored_data["expires_at"]:
        del otp_store[email]
        raise HTTPException(status_code=400, detail="OTP has expired")
    
    # Check attempt limit
    if stored_data["attempts"] >= 3:
        del otp_store[email]
        raise HTTPException(status_code=429, detail="Too many failed attempts")
    
    # Verify OTP
    if stored_data["otp"] != verification.otp:
        stored_data["attempts"] += 1
        raise HTTPException(status_code=401, detail="Invalid OTP")
    
    # Success - remove OTP
    del otp_store[email]
    
    return {
        "message": "Email verified successfully",
        "email": email,
        "verified": True
    }


@router.delete("/invalidate/{email}")
async def invalidate_otp(email: str):
    """Invalidate OTP for an email."""
    if email in otp_store:
        del otp_store[email]
        return {"message": "OTP invalidated successfully"}
    
    raise HTTPException(status_code=404, detail="No OTP found for this email")
