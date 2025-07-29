import stripe
import os
from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.models import UserPlan, Payment, PaymentStatus, PaymentCreate
import logging

logger = logging.getLogger(__name__)

class StripeService:
    def __init__(self):
        stripe_key = os.getenv("STRIPE_SECRET_KEY")
        if not stripe_key:
            logger.warning("STRIPE_SECRET_KEY not found, payment processing disabled")
            self.enabled = False
        else:
            stripe.api_key = stripe_key
            self.enabled = True
        
        self.plan_prices = {
            UserPlan.premium: {
                "USD": 9.99,
                "EUR": 8.49,
                "GBP": 7.99,
                "INR": 799.00,
                "AUD": 14.99,
                "CAD": 12.99,
                "JPY": 1499.00
            }
        }
    
    async def create_customer(self, email: str, name: str) -> Optional[str]:
        """Create a Stripe customer"""
        if not self.enabled:
            return None
        
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name
            )
            return customer.id
        except Exception as e:
            logger.error(f"Failed to create Stripe customer: {str(e)}")
            return None
    
    async def create_payment_intent(self, user_id: str, payment_data: PaymentCreate, customer_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a payment intent for subscription"""
        if not self.enabled:
            raise HTTPException(status_code=503, detail="Payment processing is currently unavailable")
        
        try:
            amount = self.plan_prices[payment_data.plan][payment_data.currency]
            
            if payment_data.currency != "JPY":
                stripe_amount = int(amount * 100)
            else:
                stripe_amount = int(amount)
            
            intent_data = {
                "amount": stripe_amount,
                "currency": payment_data.currency.lower(),
                "metadata": {
                    "user_id": user_id,
                    "plan": payment_data.plan.value
                }
            }
            
            if customer_id:
                intent_data["customer"] = customer_id
            
            payment_intent = stripe.PaymentIntent.create(**intent_data)
            
            return {
                "client_secret": payment_intent.client_secret,
                "payment_intent_id": payment_intent.id,
                "amount": amount,
                "currency": payment_data.currency
            }
            
        except Exception as e:
            logger.error(f"Failed to create payment intent: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create payment intent")
    
    async def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """Confirm payment status"""
        if not self.enabled:
            return {"status": "disabled"}
        
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                "status": payment_intent.status,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
                "metadata": payment_intent.metadata
            }
        except Exception as e:
            logger.error(f"Failed to confirm payment: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to confirm payment")
    
    def get_plan_price(self, plan: UserPlan, currency: str) -> float:
        """Get plan price in specified currency"""
        return self.plan_prices.get(plan, {}).get(currency, 9.99)

stripe_service = StripeService()
