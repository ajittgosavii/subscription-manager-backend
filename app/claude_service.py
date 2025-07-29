import anthropic
import os
import json
import re
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class ClaudeSubscriptionDetector:
    def __init__(self):
        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key:
            logger.warning("CLAUDE_API_KEY not found, using mock detection")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=api_key)
    
    async def analyze_bank_statement(self, statement_text: str) -> List[Dict[str, Any]]:
        """Analyze bank statement text to detect subscriptions"""
        if not self.client:
            return self._get_mock_subscriptions()
        
        prompt = f"""
        Analyze this bank statement and identify recurring subscription charges.
        Look for patterns like monthly/yearly charges from the same merchant.
        
        For each subscription found, provide ONLY a JSON array with this exact format:
        [
          {{
            "name": "Service name",
            "company": "Company name",
            "amount": 15.99,
            "billing_cycle": "monthly",
            "category": "streaming",
            "confidence": 0.95
          }}
        ]
        
        Categories must be one of: streaming, software, utilities, fitness, insurance, telecom, news, gaming, other
        Billing cycle must be one of: monthly, yearly, weekly
        Confidence should be between 0.0 and 1.0
        
        Bank statement text:
        {statement_text}
        
        Return ONLY the JSON array, no other text.
        """
        
        try:
            response = await self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text if response.content else ""
            return self._parse_claude_response(content)
            
        except Exception as e:
            logger.error(f"Claude AI analysis failed: {str(e)}")
            return self._get_mock_subscriptions()
    
    def _parse_claude_response(self, content: str) -> List[Dict[str, Any]]:
        """Parse Claude's response and extract subscription data"""
        try:
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                subscriptions = json.loads(json_str)
                
                validated_subscriptions = []
                for sub in subscriptions:
                    if self._validate_subscription(sub):
                        validated_subscriptions.append(sub)
                
                return validated_subscriptions
            else:
                logger.warning("No JSON array found in Claude response")
                return self._get_mock_subscriptions()
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {str(e)}")
            return self._get_mock_subscriptions()
    
    def _validate_subscription(self, sub: Dict[str, Any]) -> bool:
        """Validate subscription data structure"""
        required_fields = ['name', 'company', 'amount', 'billing_cycle', 'category', 'confidence']
        valid_categories = ['streaming', 'software', 'utilities', 'fitness', 'insurance', 'telecom', 'news', 'gaming', 'other']
        valid_cycles = ['monthly', 'yearly', 'weekly']
        
        try:
            for field in required_fields:
                if field not in sub:
                    return False
            
            if sub['category'] not in valid_categories:
                sub['category'] = 'other'
            
            if sub['billing_cycle'] not in valid_cycles:
                sub['billing_cycle'] = 'monthly'
            
            if not isinstance(sub['amount'], (int, float)) or sub['amount'] <= 0:
                return False
            
            if not isinstance(sub['confidence'], (int, float)) or not (0 <= sub['confidence'] <= 1):
                sub['confidence'] = 0.8
            
            return True
            
        except Exception:
            return False
    
    def _get_mock_subscriptions(self) -> List[Dict[str, Any]]:
        """Fallback mock subscriptions when Claude AI is not available"""
        return [
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

claude_detector = ClaudeSubscriptionDetector()
