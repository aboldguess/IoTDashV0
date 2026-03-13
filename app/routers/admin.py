"""
Mini README:
Admin API routes for user management, subscription tier CRUD, and site settings.
"""

from fastapi import APIRouter, Depends, Form
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin
from app.models import SiteConfig, SubscriptionTier, User

router = APIRouter(prefix="/admin/api", tags=["admin"])


@router.post("/users/{user_id}/toggle-admin")
def toggle_admin(user_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    user.is_admin = not user.is_admin
    db.commit()
    return {"ok": True, "is_admin": user.is_admin}


@router.post("/tiers")
def create_or_update_tier(
    name: str = Form(...),
    price_monthly: float = Form(0.0),
    usage_limit_daily: int = Form(1000),
    usage_limit_monthly: int = Form(30000),
    included_features: str = Form("basic_widgets"),
    special_offer: str = Form(""),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    tier = db.execute(select(SubscriptionTier).where(SubscriptionTier.name == name)).scalar_one_or_none()
    if not tier:
        tier = SubscriptionTier(name=name)
        db.add(tier)
    tier.price_monthly = price_monthly
    tier.usage_limit_daily = usage_limit_daily
    tier.usage_limit_monthly = usage_limit_monthly
    tier.included_features = included_features
    tier.special_offer = special_offer
    db.commit()
    return {"ok": True}


@router.post("/site-config")
def update_site_config(
    splash_tagline: str = Form(...),
    help_markdown: str = Form(...),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    config = db.get(SiteConfig, 1)
    if not config:
        config = SiteConfig(id=1)
        db.add(config)
    config.splash_tagline = splash_tagline
    config.help_markdown = help_markdown
    db.commit()
    return {"ok": True}
