from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import aiofiles
import magic
import os

from app.models import (
    User, UserCreate, Subscription, SubscriptionCreate, 
    BillNegotiation, BillNegotiationCreate, PriceAlert, 
    SavingsReport, SubscriptionStatus, BillStatus
)
from app.database import db
from app.claude_service import claude_detector

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
    
    sample_statement = """
    BANK STATEMENT - RECENT TRANSACTIONS
    01/15/2024 NETFLIX.COM         $15.99
    01/10/2024 SPOTIFY PREMIUM     $9.99
    01/08/2024 ADOBE CREATIVE      $52.99
    01/05/2024 AMAZON PRIME        $14.99
    12/15/2023 NETFLIX.COM         $15.99
    12/10/2023 SPOTIFY PREMIUM     $9.99
    12/08/2023 ADOBE CREATIVE      $52.99
    """
    
    detected_subscriptions = await claude_detector.analyze_bank_statement(sample_statement)
    
    return {
        "message": f"AI detected {len(detected_subscriptions)} potential subscriptions",
        "detected_subscriptions": detected_subscriptions,
        "ai_powered": claude_detector.client is not None
    }

@app.post("/api/users/{user_id}/upload-statement")
async def upload_bank_statement(user_id: str, file: UploadFile = File(...)):
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
    
    allowed_types = ['text/plain', 'text/csv', 'application/pdf']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload TXT, CSV, or PDF files.")
    
    try:
        content = await file.read()
        
        if file.content_type == 'application/pdf':
            statement_text = "PDF processing not implemented yet. Using sample data."
        else:
            statement_text = content.decode('utf-8')
        
        detected_subscriptions = await claude_detector.analyze_bank_statement(statement_text)
        
        return {
            "message": f"Analyzed {file.filename} and detected {len(detected_subscriptions)} potential subscriptions",
            "detected_subscriptions": detected_subscriptions,
            "ai_powered": claude_detector.client is not None,
            "file_processed": file.filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/api/users/{user_id}/subscription-insights")
async def get_subscription_insights(user_id: str):
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    subscriptions = db.get_user_subscriptions(user_id)
    
    total_monthly = sum(sub.amount for sub in subscriptions if sub.status == "active" and sub.billing_cycle == "monthly")
    total_yearly = sum(sub.amount for sub in subscriptions if sub.status == "active" and sub.billing_cycle == "yearly")
    
    category_breakdown = {}
    for sub in subscriptions:
        if sub.status == "active":
            if sub.category not in category_breakdown:
                category_breakdown[sub.category] = {"count": 0, "total": 0}
            category_breakdown[sub.category]["count"] += 1
            category_breakdown[sub.category]["total"] += sub.amount
    
    unused_count = len([sub for sub in subscriptions if sub.last_used and 
                       (datetime.utcnow() - sub.last_used).days > 30])
    
    return {
        "total_monthly_cost": total_monthly,
        "total_yearly_cost": total_yearly,
        "annual_projection": (total_monthly * 12) + total_yearly,
        "category_breakdown": category_breakdown,
        "unused_subscriptions_count": unused_count,
        "optimization_potential": unused_count * 15.0,
        "active_subscriptions": len([sub for sub in subscriptions if sub.status == "active"]),
        "total_subscriptions": len(subscriptions)
    }
