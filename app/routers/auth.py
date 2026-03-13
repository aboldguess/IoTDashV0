"""
Mini README:
Authentication routes: registration, login, logout, and profile management.
Uses session-based auth with secure password hashing.
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SubscriptionTier, User
from app.security import generate_api_key, hash_password, verify_password

router = APIRouter(tags=["auth"])


@router.post("/register")
def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(""),
    db: Session = Depends(get_db),
):
    if db.execute(select(User).where(User.email == email.lower().strip())).scalar_one_or_none():
        request.session["flash"] = "Email already exists"
        return RedirectResponse(url="/login", status_code=303)

    default_tier = db.execute(select(SubscriptionTier).order_by(SubscriptionTier.price_monthly.asc())).scalars().first()
    user = User(
        email=email.lower().strip(),
        password_hash=hash_password(password),
        full_name=full_name,
        api_key=generate_api_key(),
        subscription_tier_id=default_tier.id if default_tier else None,
    )
    db.add(user)
    db.commit()
    request.session["user_id"] = user.id
    return RedirectResponse(url="/dashboard", status_code=303)


@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == email.lower().strip())).scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        request.session["flash"] = "Invalid credentials"
        return RedirectResponse(url="/login", status_code=303)
    request.session["user_id"] = user.id
    return RedirectResponse(url="/dashboard", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@router.post("/profile")
def update_profile(
    request: Request,
    full_name: str = Form(""),
    profile_picture_url: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    user = db.get(User, user_id)
    user.full_name = full_name
    user.profile_picture_url = profile_picture_url
    db.commit()
    request.session["flash"] = "Profile updated"
    return RedirectResponse(url="/profile", status_code=303)
