from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    PENDING_CANCELLATION = "pending_cancellation"

class BillStatus(str, Enum):
    PENDING = "pending"
    NEGOTIATING = "negotiating"
    COMPLETED = "completed"
    FAILED = "failed"

class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"
    AUD = "AUD"
    CAD = "CAD"
    JPY = "JPY"

class SubscriptionCategory(str, Enum):
    STREAMING = "streaming"
    SOFTWARE = "software"
    UTILITIES = "utilities"
    INSURANCE = "insurance"
    TELECOM = "telecom"
    FITNESS = "fitness"
    NEWS = "news"
    GAMING = "gaming"
    OTHER = "other"

class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    company: str
    amount: float
    currency: str = "USD"
    billing_cycle: str  # monthly, yearly, weekly
    next_billing_date: datetime
    category: SubscriptionCategory
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    auto_detected: bool = True
    last_used: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class BillNegotiation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    subscription_id: Optional[str] = None
    service_name: str
    current_amount: float
    target_amount: Optional[float] = None
    status: BillStatus = BillStatus.PENDING
    savings_potential: Optional[float] = None
    negotiation_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    currency: Currency = Currency.USD
    total_monthly_spending: float = 0.0
    total_savings: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SavingsReport(BaseModel):
    user_id: str
    monthly_savings: float
    yearly_savings: float
    cancelled_subscriptions: int
    negotiated_bills: int
    total_subscriptions: int
    active_subscriptions: int

class PriceAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    subscription_id: str
    old_price: float
    new_price: float
    change_percentage: float
    alert_date: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False

class SubscriptionCreate(BaseModel):
    name: str
    company: str
    amount: float
    currency: str = "USD"
    billing_cycle: str
    next_billing_date: datetime
    category: SubscriptionCategory

class BillNegotiationCreate(BaseModel):
    service_name: str
    current_amount: float
    target_amount: Optional[float] = None

class UserCreate(BaseModel):
    email: str
    name: str
    currency: Currency = Currency.USD
