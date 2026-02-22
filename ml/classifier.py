import re
from typing import Dict, List, Tuple
from enum import Enum

class TicketCategory(str, Enum):
    BILLING = "Billing"
    TECHNICAL = "Technical"
    LEGAL = "Legal"
    GENERAL = "General"

class TicketClassifier:
    """
    Heuristic classifier that uses regular expressions to categorize tickets.
    Fast, predictable, and requires no Machine Learning models.
    """
    
    # Priority-ordered keyword matching
    CATEGORY_KEYWORDS = {
        TicketCategory.TECHNICAL: [
            r"install", r"pip", r"npm", r"bug", r"crash", r"error", r"api", 
            r"server", r"down", r"setup", r"python", r"node", r"build", 
            r"deployment", r"code", r"system", r"dashboard", r"loading",
            r"failed", r"connection", r"timeout", r"database", r"mysql", r"postgre"
        ],
        TicketCategory.BILLING: [
            r"invoice", r"payment", r"refund", r"billing", r"finance", 
            r"charge", r"subscription", r"pricing", r"transaction", r"bank",
            r"receipt", r"visa", r"card", r"overcharge", r"checkout", r"cost",
            r"money", r"bill", r"pay", r"credit", r"debit"
        ],
        TicketCategory.LEGAL: [
            r"privacy", r"gdpr", r"terms", r"legal", r"compliance", r"license",
            r"agreement", r"violation", r"policy", r"contract", r"law", r"court",
            r"sue", r"identity", r"theft", r"security", r"audit"
        ]
    }

    # Urgency detection patterns with weights
    URGENCY_PATTERNS = [
        (r"\b(urgent|asap|critical|emergency|immediately|breakdown|down|dead|blocking|catastrophic)\b", 0.5),
        (r"\b(blocked|cannot|can't|unable|stuck|preventing|hacked|broken|crashed)\b", 0.3),
        (r"\b(security|vulnerability|exploit|access denied)\b", 0.4),
        (r"\b(failed|money|finance|invoice error|refund|overcharge)\b", 0.2),
        (r"\b(please help|help needed|assistance|outage)\b", 0.1),
        (r"\b(whenever|when you can|low priority|no rush|fyi|question)\b", -0.2),
    ]
    
    def __init__(self):
        self.categories = list(TicketCategory)
    
    def classify(self, text: str) -> Tuple[TicketCategory, float]:
        """
        Classify ticket into category and detect urgency using heuristics.
        """
        text_lower = text.lower()
        
        # 1. Category Matching via Regex Hits
        category_scores = {cat: 0 for cat in TicketCategory}
        
        for category, patterns in self.CATEGORY_KEYWORDS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    # Higher scores for more matches
                    category_scores[category] += 1
        
        # Default to General
        final_category = TicketCategory.GENERAL
        
        # Pick category with highest hits
        if max(category_scores.values()) > 0:
            final_category = max(category_scores, key=category_scores.get)
            
        print(f"Heuristic Classification | Text: '{text[:40]}...' | Category: {final_category.value}")

        # 2. Detect urgency using additive logic
        urgency = self._detect_urgency(text, final_category)
        
        return final_category, urgency

    def _detect_urgency(self, text: str, category: TicketCategory = TicketCategory.GENERAL) -> float:
        """
        Detect urgency level using a multi-factor additive model.
        Returns a value between 0.0 and 1.0
        """
        text_lower = text.lower()
        
        # Initial base score
        score = 0.2
        
        # Additive weights from patterns
        for pattern, weight in self.URGENCY_PATTERNS:
            if re.search(pattern, text_lower):
                score += weight
        
        # Emphasis Boost (caps, exclamations)
        if "!!!" in text or "URGENT" in text.upper():
            score += 0.1
            
        # Category Bias
        if category == TicketCategory.TECHNICAL:
            score += 0.05
        elif category == TicketCategory.BILLING:
            score += 0.05
            
        return min(1.0, max(0.0, round(score, 2)))

    def batch_classify(self, texts: List[str]) -> List[Tuple[TicketCategory, float]]:
        return [self.classify(text) for text in texts]

# Singleton instance
classifier = TicketClassifier()
