"""
Authentication module for Enterprise Restaurant Inventory System
Módulo de autenticación - Sistema Enterprise de Inventarios
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from jose import jwt, JWTError
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.database import User, Restaurant, SessionLocal
from backend.config import settings
from werkzeug.security import check_password_hash

# Security
security = HTTPBearer()
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_HOURS = settings.ACCESS_TOKEN_EXPIRE_HOURS

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    restaurant_id: int

# Router
router = APIRouter()

# Rate limiter
try:
    from backend.middleware.rate_limit import limiter
    rate_limiter_available = True
except ImportError:
    rate_limiter_available = False
    limiter = None

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute") # Add rate limiting to login endpoint
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint with rate limiting"""
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    # Verify password
    if not check_password_hash(user.hashed_password, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Get restaurant info
    restaurant = db.query(Restaurant).filter(Restaurant.id == user.restaurant_id).first()
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "restaurant_id": user.restaurant_id}
    )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "restaurant_id": user.restaurant_id,
            "restaurant_name": restaurant.name if restaurant else None
        }
    )

@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user information"""
    restaurant = db.query(Restaurant).filter(Restaurant.id == current_user.restaurant_id).first()
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "restaurant_id": current_user.restaurant_id,
        "restaurant_name": restaurant.name if restaurant else None,
        "is_active": current_user.is_active,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }

@router.post("/logout")
async def logout():
    """Logout endpoint (client-side token removal)"""
    return {"message": "Logout successful. Please remove token on client side."}
