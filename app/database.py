from typing import Dict, List, Optional
from app.models import User, Subscription, BillNegotiation, PriceAlert, SavingsReport, Currency
import uuid
from datetime import datetime, timedelta

class InMemoryDatabase:
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.subscriptions: Dict[str, Subscription] = {}
        self.bill_negotiations: Dict[str, BillNegotiation] = {}
        self.price_alerts: Dict[str, PriceAlert] = {}
        
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        sample_user = User(
            id="sample-user-123",
            email="demo@example.com",
            name="Demo User",
            currency=Currency.USD,
            total_monthly_spending=156.97,
            total_savings=45.50
        )
        self.users[sample_user.id] = sample_user
        
        sample_subscriptions = [
            Subscription(
                id="sub-1",
                user_id=sample_user.id,
                name="Netflix Premium",
                company="Netflix",
                amount=15.99,
                billing_cycle="monthly",
                next_billing_date=datetime.utcnow() + timedelta(days=15),
                category="streaming",
                last_used=datetime.utcnow() - timedelta(days=2)
            ),
            Subscription(
                id="sub-2",
                user_id=sample_user.id,
                name="Spotify Premium",
                company="Spotify",
                amount=9.99,
                billing_cycle="monthly",
                next_billing_date=datetime.utcnow() + timedelta(days=8),
                category="streaming",
                last_used=datetime.utcnow() - timedelta(hours=3)
            ),
            Subscription(
                id="sub-3",
                user_id=sample_user.id,
                name="Adobe Creative Cloud",
                company="Adobe",
                amount=52.99,
                billing_cycle="monthly",
                next_billing_date=datetime.utcnow() + timedelta(days=22),
                category="software",
                last_used=datetime.utcnow() - timedelta(days=45)
            ),
            Subscription(
                id="sub-4",
                user_id=sample_user.id,
                name="Gym Membership",
                company="FitLife Gym",
                amount=29.99,
                billing_cycle="monthly",
                next_billing_date=datetime.utcnow() + timedelta(days=5),
                category="fitness",
                last_used=datetime.utcnow() - timedelta(days=30),
                status="active"
            ),
            Subscription(
                id="sub-5",
                user_id=sample_user.id,
                name="Disney+",
                company="Disney",
                amount=7.99,
                billing_cycle="monthly",
                next_billing_date=datetime.utcnow() + timedelta(days=12),
                category="streaming",
                last_used=datetime.utcnow() - timedelta(days=60),
                status="active"
            )
        ]
        
        for sub in sample_subscriptions:
            self.subscriptions[sub.id] = sub
    
    def create_user(self, user: User) -> User:
        self.users[user.id] = user
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def create_subscription(self, subscription: Subscription) -> Subscription:
        self.subscriptions[subscription.id] = subscription
        return subscription
    
    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        return self.subscriptions.get(subscription_id)
    
    def get_user_subscriptions(self, user_id: str) -> List[Subscription]:
        return [sub for sub in self.subscriptions.values() if sub.user_id == user_id]
    
    def update_subscription(self, subscription_id: str, updates: dict) -> Optional[Subscription]:
        if subscription_id in self.subscriptions:
            subscription = self.subscriptions[subscription_id]
            for key, value in updates.items():
                if hasattr(subscription, key):
                    setattr(subscription, key, value)
            subscription.updated_at = datetime.utcnow()
            return subscription
        return None
    
    def delete_subscription(self, subscription_id: str) -> bool:
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            return True
        return False
    
    def create_bill_negotiation(self, negotiation: BillNegotiation) -> BillNegotiation:
        self.bill_negotiations[negotiation.id] = negotiation
        return negotiation
    
    def get_bill_negotiation(self, negotiation_id: str) -> Optional[BillNegotiation]:
        return self.bill_negotiations.get(negotiation_id)
    
    def get_user_negotiations(self, user_id: str) -> List[BillNegotiation]:
        return [neg for neg in self.bill_negotiations.values() if neg.user_id == user_id]
    
    def update_bill_negotiation(self, negotiation_id: str, updates: dict) -> Optional[BillNegotiation]:
        if negotiation_id in self.bill_negotiations:
            negotiation = self.bill_negotiations[negotiation_id]
            for key, value in updates.items():
                if hasattr(negotiation, key):
                    setattr(negotiation, key, value)
            return negotiation
        return None
    
    def create_price_alert(self, alert: PriceAlert) -> PriceAlert:
        self.price_alerts[alert.id] = alert
        return alert
    
    def get_user_price_alerts(self, user_id: str) -> List[PriceAlert]:
        return [alert for alert in self.price_alerts.values() if alert.user_id == user_id]
    
    def acknowledge_price_alert(self, alert_id: str) -> bool:
        if alert_id in self.price_alerts:
            self.price_alerts[alert_id].acknowledged = True
            return True
        return False
    
    def get_user_savings_report(self, user_id: str) -> SavingsReport:
        user_subscriptions = self.get_user_subscriptions(user_id)
        user_negotiations = self.get_user_negotiations(user_id)
        
        active_subs = [sub for sub in user_subscriptions if sub.status == "active"]
        cancelled_subs = [sub for sub in user_subscriptions if sub.status == "cancelled"]
        completed_negotiations = [neg for neg in user_negotiations if neg.status == "completed"]
        
        monthly_savings = sum(neg.savings_potential or 0 for neg in completed_negotiations)
        monthly_savings += sum(sub.amount for sub in cancelled_subs)
        
        return SavingsReport(
            user_id=user_id,
            monthly_savings=monthly_savings,
            yearly_savings=monthly_savings * 12,
            cancelled_subscriptions=len(cancelled_subs),
            negotiated_bills=len(completed_negotiations),
            total_subscriptions=len(user_subscriptions),
            active_subscriptions=len(active_subs)
        )

db = InMemoryDatabase()
