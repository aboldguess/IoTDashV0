"""
Mini README:
Main FastAPI app entrypoint with page routes, startup seeding, session middleware,
and Stripe checkout integration hooks. Run with uvicorn app.main:app.
"""

import logging

import stripe
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine, get_db
from app.deps import get_current_user, require_admin
from app.models import DashboardWidget, SensorEnrollment, SiteConfig, SubscriptionTier, User
from app.mqtt_service import init_mqtt_manager
from app.routers import admin, auth, dashboard
from app.security import generate_api_key, hash_password

logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, same_site="lax", https_only=False)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
stripe.api_key = settings.stripe_secret_key


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    init_mqtt_manager(SessionLocal)
    db = SessionLocal()
    try:
        if not db.execute(select(SubscriptionTier)).first():
            db.add_all(
                [
                    SubscriptionTier(name="Free", price_monthly=0, included_features="basic_widgets,api", special_offer="Starter"),
                    SubscriptionTier(name="Pro", price_monthly=19, included_features="all_widgets,api,automation", special_offer="10% off annual"),
                    SubscriptionTier(name="Enterprise", price_monthly=99, included_features="all_widgets,api,automation,sso", special_offer="Dedicated support"),
                ]
            )
        if not db.get(SiteConfig, 1):
            db.add(SiteConfig(id=1))
        admin_user = db.execute(select(User).where(User.email == "admin@iotdash.local")).scalar_one_or_none()
        if not admin_user:
            db.add(
                User(
                    email="admin@iotdash.local",
                    password_hash=hash_password("ChangeMe123!"),
                    full_name="Platform Admin",
                    is_admin=True,
                    api_key=generate_api_key(),
                )
            )
            logger.info("Seeded default admin account: admin@iotdash.local / ChangeMe123!")
        db.commit()
    finally:
        db.close()


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(admin.router)


@app.get("/")
def splash(request: Request, db: Session = Depends(get_db)):
    config = db.get(SiteConfig, 1)
    return templates.TemplateResponse("splash.html", {"request": request, "config": config, "user": None})


@app.get("/login")
def login_page(request: Request):
    flash = request.session.pop("flash", None)
    return templates.TemplateResponse("login.html", {"request": request, "flash": flash, "user": None})


@app.get("/dashboard")
def dashboard_page(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    widgets = db.execute(select(DashboardWidget).where(DashboardWidget.owner_id == user.id).order_by(DashboardWidget.created_at.desc())).scalars().all()
    sensors = db.execute(select(SensorEnrollment).where(SensorEnrollment.owner_id == user.id).order_by(SensorEnrollment.created_at.desc())).scalars().all()
    flash = request.session.pop("flash", None)
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "widgets": widgets, "sensors": sensors, "flash": flash})


@app.get("/help")
def help_page(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    config = db.get(SiteConfig, 1)
    return templates.TemplateResponse("help.html", {"request": request, "user": user, "config": config})


@app.get("/profile")
def profile_page(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tiers = db.execute(select(SubscriptionTier)).scalars().all()
    return templates.TemplateResponse("profile.html", {"request": request, "user": user, "tiers": tiers})


@app.post("/create-checkout-session")
def create_checkout_session(
    request: Request,
    price_id: str = Form(...),
    user: User = Depends(get_current_user),
):
    if not settings.stripe_secret_key:
        request.session["flash"] = "Stripe is not configured in this environment."
        return RedirectResponse(url="/profile", status_code=303)
    checkout = stripe.checkout.Session.create(
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url="http://localhost:8000/profile",
        cancel_url="http://localhost:8000/profile",
        customer_email=user.email,
    )
    return RedirectResponse(url=checkout.url, status_code=303)


@app.get("/admin")
def admin_page(request: Request, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.execute(select(User).order_by(User.created_at.desc())).scalars().all()
    tiers = db.execute(select(SubscriptionTier)).scalars().all()
    config = db.get(SiteConfig, 1)
    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "user": user, "users": users, "tiers": tiers, "config": config},
    )
