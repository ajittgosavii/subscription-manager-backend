from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from app.models import (
    User, UserCreate, Subscription, SubscriptionCreate, 
    BillNegotiation, BillNegotiationCreate, PriceAlert, 
    SavingsReport, SubscriptionStatus, BillStatus
)
from app.database import db

app = FastAPI(title="Smart Subscription Manager API", version="1.0.0")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/api/users", response_model=User)
async def create_user(user_data: UserCreate):
    existing_user = db.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    user = User(**user_data.dict())
    return db.create_user(user)

@app.get("/api/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/api/users/email/{email}", response_model=User)
async def get_user_by_email(email: str):
    user = db.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/api/users/{user_id}/subscriptions", response_model=List[Subscription])
async def get_user_subscriptions(user_id: str):
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return db.get_user_subscriptions(user_id)

@app.post("/api/users/{user_id}/subscriptions", response_model=Subscription)
async def create_subscription(user_id: str, subscription_data: SubscriptionCreate):
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    subscription = Subscription(user_id=user_id, **subscription_data.dict())
    return db.create_subscription(subscription)

@app.get("/api/subscriptions/{subscription_id}", response_model=Subscription)
async def get_subscription(subscription_id: str):
    subscription = db.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription

@app.put("/api/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(subscription_id: str):
    subscription = db.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    updated = db.update_subscription(subscription_id, {"status": SubscriptionStatus.CANCELLED})
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")
    
    return {"message": "Subscription cancelled successfully", "subscription": updated}

@app.put("/api/subscriptions/{subscription_id}/pause")
async def pause_subscription(subscription_id: str):
    subscription = db.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    updated = db.update_subscription(subscription_id, {"status": SubscriptionStatus.PAUSED})
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to pause subscription")
    
    return {"message": "Subscription paused successfully", "subscription": updated}

@app.delete("/api/subscriptions/{subscription_id}")
async def delete_subscription(subscription_id: str):
    subscription = db.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    success = db.delete_subscription(subscription_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete subscription")
    
    return {"message": "Subscription deleted successfully"}

@app.get("/api/users/{user_id}/negotiations", response_model=List[BillNegotiation])
async def get_user_negotiations(user_id: str):
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return db.get_user_negotiations(user_id)

@app.post("/api/users/{user_id}/negotiations", response_model=BillNegotiation)
async def create_bill_negotiation(user_id: str, negotiation_data: BillNegotiationCreate):
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    negotiation = BillNegotiation(user_id=user_id, **negotiation_data.dict())
    negotiation.savings_potential = negotiation.current_amount * 0.15  # 15% average savings
    
    return db.create_bill_negotiation(negotiation)

@app.put("/api/negotiations/{negotiation_id}/complete")
async def complete_negotiation(negotiation_id: str, actual_savings: float):
    negotiation = db.get_bill_negotiation(negotiation_id)
    if not negotiation:
        raise HTTPException(status_code=404, detail="Negotiation not found")
    
    updates = {
        "status": BillStatus.COMPLETED,
        "savings_potential": actual_savings,
        "completed_at": datetime.utcnow()
    }
    
    updated = db.update_bill_negotiation(negotiation_id, updates)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to complete negotiation")
    
    return {"message": "Negotiation completed successfully", "negotiation": updated}

@app.get("/api/users/{user_id}/savings-report", response_model=SavingsReport)
async def get_savings_report(user_id: str):
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return db.get_user_savings_report(user_id)

@app.get("/api/users/{user_id}/unused-subscriptions", response_model=List[Subscription])
async def get_unused_subscriptions(user_id: str, days_unused: int = 30):
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    subscriptions = db.get_user_subscriptions(user_id)
    cutoff_date = datetime.utcnow() - timedelta(days=days_unused)
    
    unused = []
    for sub in subscriptions:
        if sub.status == SubscriptionStatus.ACTIVE and sub.last_used and sub.last_used < cutoff_date:
            unused.append(sub)
    
    return unused

@app.get("/api/users/{user_id}/price-alerts", response_model=List[PriceAlert])
async def get_price_alerts(user_id: str):
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return db.get_user_price_alerts(user_id)

@app.put("/api/price-alerts/{alert_id}/acknowledge")
async def acknowledge_price_alert(alert_id: str):
    success = db.acknowledge_price_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Price alert not found")
    return {"message": "Price alert acknowledged"}

@app.get("/api/currencies")
async def get_supported_currencies():
    from app.currency import get_currency_info
    from app.models import Currency
    try:
        currencies = []
        for currency in Currency:
            currencies.append(get_currency_info(currency.value))
        return currencies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users/{user_id}/detect-subscriptions")
async def detect_subscriptions(user_id: str):
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    detected_subscriptions = [
        {
            "name": "Amazon Prime",
            "company": "Amazon",
            "amount": 14.99,
            "billing_cycle": "monthly",
            "category": "streaming",
            "confidence": 0.95
        },
        {
            "name": "Microsoft 365",
            "company": "Microsoft",
            "amount": 6.99,
            "billing_cycle": "monthly", 
            "category": "software",
            "confidence": 0.88
        }
    ]
    
    return {
        "message": f"Detected {len(detected_subscriptions)} potential subscriptions",
        "detected_subscriptions": detected_subscriptions
    }
