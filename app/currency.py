from typing import Dict
from app.models import Currency

EXCHANGE_RATES: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 0.85,
    "GBP": 0.73,
    "INR": 83.12,
    "AUD": 1.52,
    "CAD": 1.36,
    "JPY": 149.50
}

CURRENCY_SYMBOLS: Dict[str, str] = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "INR": "₹",
    "AUD": "A$",
    "CAD": "C$",
    "JPY": "¥"
}

def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    if from_currency == to_currency:
        return amount
    
    usd_amount = amount / EXCHANGE_RATES[from_currency]
    return usd_amount * EXCHANGE_RATES[to_currency]

def format_currency(amount: float, currency: str) -> str:
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    
    if currency == "JPY":
        return f"{symbol}{int(amount):,}"
    else:
        return f"{symbol}{amount:,.2f}"

def get_currency_info(currency: str) -> Dict[str, str]:
    return {
        "code": currency,
        "symbol": CURRENCY_SYMBOLS.get(currency, currency),
        "rate": str(EXCHANGE_RATES.get(currency, 1.0))
    }
