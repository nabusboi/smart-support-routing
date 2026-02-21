"""
Baseline Classifier for Ticket Routing (Milestone 1)
Routes tickets into three categories: Billing, Technical, or Legal
Uses regex-based heuristics for urgency detection
"""
import re
from typing import Dict, List, Tuple
from enum import Enum


class TicketCategory(str, Enum):
    BILLING = "Billing"
    TECHNICAL = "Technical"
    LEGAL = "Legal"
    GENERAL = "General"


class BaselineClassifier:
    """
    Baseline ML classifier using keyword-based heuristics.
    Replace with Transformer model in Milestone 2.
    """
    
    # Category keywords
    CATEGORY_KEYWORDS = {
        TicketCategory.BILLING: [
            "invoice", "payment", "bill", "charge", "refund", "subscription",
            "pricing", "cost", "fee", "transaction", "credit", "debit",
            "billing", "renewal", "upgrade", "downgrade", "plan", "coupon"
        ],
        TicketCategory.TECHNICAL: [
            "error", "bug", "crash", "broken", "not working", "issue",
            "problem", "fix", "debug", "performance", "slow", "loading",
            "api", "server", "database", "connection", "timeout", "503",
            "404", "500", "exception", "stack trace", "crash", "freeze",
            "technical", "support", "help"
        ],
        TicketCategory.LEGAL: [
            "legal", "compliance", "gdpr", "privacy", "terms", "contract",
            "agreement", "law", "regulation", "data protection", "ip",
            "intellectual property", "trademark", "copyright", "litigation",
            "lawsuit", "subpoena", "audit"
        ]
    }
    
    # Urgency keywords (regex patterns)
    URGENCY_PATTERNS = [
        (r"\b(urgent|asap|immediately|emergency|critical)\b", 1.0),
        (r"\b(broken|down|crash|crashed|not working)\b", 0.9),
        (r"\b(soon|quick|fast|priority|high)\b", 0.7),
        (r"\b(whenever|when you can|low priority)\b", 0.3),
        (r"\b(fyi|just so you know|information)\b", 0.1),
    ]
    
    def __init__(self):
        self.categories = list(TicketCategory)
    
    def classify(self, text: str) -> Tuple[TicketCategory, float]:
        """
        Classify ticket into category and detect urgency.
        
        Args:
            text: The ticket text content
            
        Returns:
            Tuple of (category, urgency_score)
        """
        text_lower = text.lower()
        
        # Calculate scores for each category
        category_scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            category_scores[category] = score
        
        # Get the category with highest score
        max_score = max(category_scores.values())
        if max_score == 0:
            category = TicketCategory.GENERAL
        else:
            category = max(category_scores, key=category_scores.get)
        
        # Detect urgency using regex
        urgency = self._detect_urgency(text)
        
        return category, urgency
    
    def _detect_urgency(self, text: str) -> float:
        """
        Detect urgency level using regex patterns.
        
        Args:
            text: The ticket text content
            
        Returns:
            Urgency score between 0 and 1
        """
        text_lower = text.lower()
        urgency_score = 0.0
        
        for pattern, score in self.URGENCY_PATTERNS:
            if re.search(pattern, text_lower):
                urgency_score = max(urgency_score, score)
        
        return urgency_score
    
    def batch_classify(self, texts: List[str]) -> List[Tuple[TicketCategory, float]]:
        """
        Classify multiple tickets.
        
        Args:
            texts: List of ticket texts
            
        Returns:
            List of (category, urgency_score) tuples
        """
        return [self.classify(text) for text in texts]


# Singleton instance
classifier = BaselineClassifier()


def score_urgency(text: str) -> float:
    """
    Score urgency using baseline classifier.
    This is the fallback function used when transformer is too slow.
    
    Args:
        text: The ticket text content
        
    Returns:
        Urgency score between 0 and 1
    """
    return classifier._detect_urgency(text)
