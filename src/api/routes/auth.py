from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional
from src.api.auth import (
    register_user,
    get_user_by_email,
    verify_password,
    create_access_token,
    decode_access_token,
    initialize_default_users
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)

initialize_default_users()

class UserRegisterRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$", description="Valid email address")
    password: str = Field(min_length=6, description="Password must be at least 6 characters")
    full_name: Optional[str] = "Analyst"

class UserLoginRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$", description="Valid email address")
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    email: str
    full_name: str
    tier: str
    created_at: str

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    """Dependency for securing endpoints requiring authentication."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user_by_email(payload["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[dict]:
    """Optional authentication dependency for soft-gating features."""
    if not credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None
    return get_user_by_email(payload["sub"])

@router.post("/register", response_model=TokenResponse)
def register(request: UserRegisterRequest):
    """Register a new user account and return JWT session token."""
    try:
        user = register_user(request.email, request.password, request.full_name or "")
        token = create_access_token({"sub": user["email"], "tier": user["tier"]})
        user_clean = {k: v for k, v in user.items() if k not in ["hashed_password", "salt"]}
        return TokenResponse(access_token=token, user=user_clean)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=TokenResponse)
def login(request: UserLoginRequest):
    """Authenticate with email and password to receive JWT session token."""
    user = get_user_by_email(request.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(request.password, user["hashed_password"], user["salt"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token({"sub": user["email"], "tier": user["tier"]})
    user_clean = {k: v for k, v in user.items() if k not in ["hashed_password", "salt"]}
    return TokenResponse(access_token=token, user=user_clean)

@router.get("/me", response_model=UserResponse)
def get_profile(current_user: dict = Depends(get_current_user)):
    """Retrieve current logged in user profile and tier."""
    return UserResponse(
        email=current_user["email"],
        full_name=current_user["full_name"],
        tier=current_user["tier"],
        created_at=current_user["created_at"]
    )
