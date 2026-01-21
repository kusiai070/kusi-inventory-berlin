"""
Authentication module for Enterprise Restaurant Inventory System
Módulo de autenticación - Sistema Enterprise de Inventarios
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
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

from backend.models.database import User, Restaurant, SessionLocal, get_db
from backend.config import settings
import bcrypt

# Security
security = HTTPBearer()
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_HOURS = settings.ACCESS_TOKEN_EXPIRE_HOURS

from backend.models.database import User, Restaurant, SessionLocal, get_db

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

if not rate_limiter_available or limiter is None:
    # Dummy limiter to avoid AttributeError when decorator is used
    class DummyLimiter:
        def limit(self, limit_value):
            def decorator(func):
                return func
            return decorator
    
    limiter = DummyLimiter()

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
async def login(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint with rate limiting"""
    print(f"Login attempt for: {login_data.email}")
    try:
        # Find user by email
        user = db.query(User).filter(User.email == login_data.email).first()
        
        if not user:
            print(f"User not found: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        print(f"User found: {user.id} - Role: {user.role}")
        
        if not user.is_active:
            print("User account disabled")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        # Verify password
        print("Verifying password...")
        is_valid = bcrypt.checkpw(login_data.password.encode('utf-8'), user.hashed_password.encode('utf-8'))
        print(f"Password valid? {is_valid}")
        
        if not is_valid:
            print("Password mismatch")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Get restaurant info
        restaurant = db.query(Restaurant).filter(Restaurant.id == user.restaurant_id).first()
        print(f"Restaurant: {restaurant.name if restaurant else 'None'}")
        
        # Create access token
        print("Creating access token...")
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role, "restaurant_id": user.restaurant_id}
        )
        print("Token created successfully")
        
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
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"CRITICAL LOGIN ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login Error: {str(e)}"
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
