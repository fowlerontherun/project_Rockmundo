from auth.dependencies import get_current_user_id, require_role
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from utils.auth_utils import create_access_token, verify_user_credentials
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

class TokenResponse(BaseModel):
    
access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = verify_user_credentials(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user["username"])
    return TokenResponse(access_token=token)