"""
BOTUVIC API Server
FastAPI backend for API key validation and usage tracking.
Deploy to Render for production use.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker, relationship
from datetime import datetime
import secrets
import os

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./botuvic.db")
# Fix for Render PostgreSQL URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# =============================================================================
# DATABASE MODELS
# =============================================================================

class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    subscription_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    api_keys = relationship("APIKey", back_populates="user")


class APIKey(Base):
    """API Key model."""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="api_keys")
    usage = relationship("Usage", back_populates="api_key")


class Usage(Base):
    """Usage tracking model."""
    __tablename__ = "usage"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"))
    event = Column(String)  # create_project, generate_tests, etc.
    metadata = Column(String, nullable=True)  # JSON string
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    api_key = relationship("APIKey", back_populates="usage")


# Create tables
Base.metadata.create_all(bind=engine)


# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="BOTUVIC API",
    description="API key validation and usage tracking for BOTUVIC MCP server",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/")
def root():
    """Health check."""
    return {
        "service": "BOTUVIC API",
        "status": "running",
        "version": "1.0.0"
    }


@app.post("/validate")
def validate_key(data: dict, db: Session = Depends(get_db)):
    """
    Validate API key.
    
    Request: {"key": "sk_live_xxx"}
    Response: {"valid": true/false, "user_id": 123}
    """
    key = data.get("key")
    
    if not key:
        return {"valid": False, "error": "No key provided"}
    
    # Query API key
    api_key = db.query(APIKey).filter(
        APIKey.key == key,
        APIKey.is_active == True
    ).first()
    
    if not api_key:
        return {"valid": False, "error": "Invalid key"}
    
    # Check user subscription
    user = api_key.user
    if not user.subscription_active:
        return {"valid": False, "error": "Subscription inactive"}
    
    return {
        "valid": True,
        "user_id": user.id,
        "email": user.email
    }


@app.post("/track")
def track_usage(data: dict, db: Session = Depends(get_db)):
    """
    Track usage event.
    
    Request: {"key": "sk_live_xxx", "event": "create_project", "metadata": {...}}
    Response: {"tracked": true}
    """
    key = data.get("key")
    event = data.get("event")
    metadata = data.get("metadata", {})
    
    if not key or not event:
        raise HTTPException(400, "Missing key or event")
    
    # Find API key
    api_key = db.query(APIKey).filter_by(key=key).first()
    if not api_key:
        raise HTTPException(404, "Invalid key")
    
    # Create usage record
    import json
    usage = Usage(
        api_key_id=api_key.id,
        event=event,
        metadata=json.dumps(metadata) if metadata else None
    )
    db.add(usage)
    db.commit()
    
    return {"tracked": True, "event": event}


@app.post("/keys/create")
def create_key(data: dict, db: Session = Depends(get_db)):
    """
    Create new API key for user.
    
    Request: {"email": "user@example.com"}
    Response: {"key": "sk_live_xxx", "user_id": 123}
    """
    email = data.get("email")
    
    if not email:
        raise HTTPException(400, "Email required")
    
    # Find or create user
    user = db.query(User).filter_by(email=email).first()
    if not user:
        user = User(email=email, subscription_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Generate key
    key = f"sk_live_{secrets.token_urlsafe(32)}"
    
    api_key = APIKey(
        key=key,
        user_id=user.id,
        is_active=True
    )
    db.add(api_key)
    db.commit()
    
    return {
        "key": key,
        "user_id": user.id,
        "email": user.email
    }


@app.post("/keys/revoke")
def revoke_key(data: dict, db: Session = Depends(get_db)):
    """
    Revoke API key.
    
    Request: {"key": "sk_live_xxx"}
    Response: {"revoked": true}
    """
    key = data.get("key")
    
    if not key:
        raise HTTPException(400, "Key required")
    
    api_key = db.query(APIKey).filter_by(key=key).first()
    if api_key:
        api_key.is_active = False
        db.commit()
        return {"revoked": True}
    
    raise HTTPException(404, "Key not found")


@app.get("/usage/{user_id}")
def get_usage(user_id: int, db: Session = Depends(get_db)):
    """
    Get usage statistics for user.
    
    Response: {"total_events": 123, "events": {...}}
    """
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    # Get all usage for user's keys
    usage_records = []
    for api_key in user.api_keys:
        usage_records.extend(api_key.usage)
    
    # Count by event type
    event_counts = {}
    for usage in usage_records:
        event_counts[usage.event] = event_counts.get(usage.event, 0) + 1
    
    return {
        "user_id": user_id,
        "email": user.email,
        "total_events": len(usage_records),
        "events": event_counts,
        "subscription_active": user.subscription_active
    }


@app.get("/usage/stats")
def get_usage_stats(db: Session = Depends(get_db)):
    """
    Get usage statistics for current user (from auth token).
    
    Response: {
        "projects_built": 15,
        "total_usage_hours": 42,
        "total_sessions": 128,
        "last_activity": "2026-01-17T09:00:00"
    }
    """
    # TODO: Get user from auth token
    # For now, return aggregate stats or mock data
    
    # Get all usage records
    all_usage = db.query(Usage).all()
    
    # Count projects (create_project events)
    projects_built = len([u for u in all_usage if u.event == "create_project"])
    
    # Count sessions (activate_live_mode events)
    total_sessions = len([u for u in all_usage if u.event == "activate_live_mode"])
    
    # Estimate usage hours (rough: 1 hour per project + 0.5 hour per session)
    total_usage_hours = projects_built + (total_sessions * 0.5)
    
    # Get last activity
    last_activity = None
    if all_usage:
        sorted_usage = sorted(all_usage, key=lambda x: x.timestamp, reverse=True)
        last_activity = sorted_usage[0].timestamp.isoformat() if sorted_usage else None
    
    return {
        "projects_built": projects_built,
        "total_usage_hours": int(total_usage_hours),
        "total_sessions": total_sessions,
        "last_activity": last_activity
    }



@app.post("/admin/activate")
def activate_subscription(data: dict, db: Session = Depends(get_db)):
    """
    Activate user subscription (admin only).
    
    Request: {"email": "user@example.com"}
    Response: {"activated": true}
    """
    # TODO: Add admin authentication
    email = data.get("email")
    
    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    user.subscription_active = True
    db.commit()
    
    return {"activated": True, "email": email}


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
