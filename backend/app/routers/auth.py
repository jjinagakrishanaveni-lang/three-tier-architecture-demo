import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from ..config import settings
from ..database import get_db
from ..models import User
from ..schemas import (
    UserRegisterRequest,
    UserVerifyRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    RegistrationSuccessResponse,
    VerificationSuccessResponse
)
from ..redis_client import (
    save_pending_registration,
    get_pending_registration,
    delete_pending_registration,
    is_email_pending_in_redis
)
from ..auth import hash_password, verify_password, create_access_token, get_current_user
from ..email_service import send_verification_email

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post(
    "/register",
    response_model=RegistrationSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user and initiate email verification"
)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Workflow 1 & 2 & 3:
    - User registers via name, email, password.
    - Validate that email is not already registered and verified in PostgreSQL.
    - Temporarily store registration details and token in Redis (with TTL).
    - Send email verification link.
    """
    clean_email = request.email.lower().strip()
    
    # Check if already verified in PostgreSQL
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address is already registered and verified."
        )

    # Hash the password with bcrypt
    hashed_pwd = hash_password(request.password)

    # Generate a cryptographically secure random verification token
    verification_token = secrets.token_urlsafe(32)

    # Store pending registration in Redis (temporary storage)
    save_pending_registration(
        token=verification_token,
        name=request.name.strip(),
        email=clean_email,
        hashed_password=hashed_pwd
    )

    # Send verification email with link
    email_record = send_verification_email(
        email=clean_email,
        name=request.name.strip(),
        token=verification_token
    )

    return RegistrationSuccessResponse(
        message="Registration initiated! A verification link has been sent to your email address.",
        email=clean_email,
        verification_token=verification_token,
        verification_url=email_record["verification_url"],
        expires_in_seconds=settings.PENDING_REGISTRATION_TTL
    )

@router.post(
    "/verify",
    response_model=VerificationSuccessResponse,
    summary="Verify email token and commit user to database"
)
def verify_email(
    request: UserVerifyRequest = None,
    token: str = Query(None, description="Optional query parameter verification token"),
    db: Session = Depends(get_db)
):
    """
    Workflow 4:
    - Check token in Redis.
    - If valid, extract user details and insert into PostgreSQL.
    - Delete pending token from Redis.
    """
    verify_token = (request.token if request and request.token else token)
    if not verify_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token is required."
        )

    # Lookup pending registration in Redis
    pending_data = get_pending_registration(verify_token)
    if not pending_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token is invalid, expired, or already used."
        )

    email = pending_data["email"].lower()
    name = pending_data["name"]
    hashed_pwd = pending_data["hashed_password"]

    # Check if user was already inserted
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        # Clean up Redis just in case
        delete_pending_registration(verify_token, email)
        return VerificationSuccessResponse(
            message="Email was already verified! You can log in now.",
            user=existing_user
        )

    # Insert into PostgreSQL
    new_user = User(
        name=name,
        email=email,
        hashed_password=hashed_pwd,
        is_verified=True,
        created_at=datetime.utcnow(),
        verified_at=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Clean up temporary data from Redis
    delete_pending_registration(verify_token, email)

    return VerificationSuccessResponse(
        message="Email successfully verified! Your account has been activated in PostgreSQL.",
        user=new_user
    )

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in verified users and return JWT access token"
)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Workflow 5:
    - Allow only verified users to log in.
    - Validates email and password against PostgreSQL.
    """
    clean_email = request.email.lower().strip()

    # Query PostgreSQL
    user = db.query(User).filter(User.email == clean_email).first()

    if not user:
        # Check if user has an unverified pending registration in Redis
        if is_email_pending_in_redis(clean_email):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your email is pending verification. Please check your email and click the verification link before logging in."
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Verify email status
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not verified. Please verify your email first."
        )

    # Create access token
    access_token = create_access_token(data={"sub": user.id, "email": user.email})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current logged in user profile"
)
def get_me(current_user: User = Depends(get_current_user)):
    """Protected endpoint to retrieve current authenticated user details."""
    return current_user
