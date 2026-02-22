"""
Machine Learning Classifier for Ticket Routing
Routes tickets into three categories: Billing, Technical, or Legal
Uses Logistic Regression with TF-IDF features.
"""
import re
import os
import joblib
from typing import Dict, List, Tuple, Optional
from enum import Enum


class TicketCategory(str, Enum):
    BILLING = "Billing"
    TECHNICAL = "Technical"
    LEGAL = "Legal"
    GENERAL = "General"


class TicketClassifier:
    """
    ML classifier using Logistic Regression.
    Trained on TF-IDF features with bigram support.
    """
    
    MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")
    
    # Urgency keywords (regex patterns) - Refined for continuous gradient
    URGENCY_PATTERNS = [
        # Level 5: Extreme (0.95 - 1.0)
        (r"\b(emergency|critical|catastrophic|blocking|production down)\b", 1.0),
        # Level 4: High (0.8 - 0.9)
        (r"\b(urgent|asap|immediately|hacked|broken|down|crashed)\b", 0.9),
        # Level 3: Medium-High (0.65 - 0.75)
        (r"\b(priority|high|soon|quick(ly)?|fast|outage|fail(ed|ing)?)\b", 0.75),
        # Level 2: Medium (0.4 - 0.6)
        (r"\b(slow|lag(ging)?|delay(ed)?|stuck|blocked|problem|issue)\b", 0.5),
        # Level 1: Low (0.1 - 0.3)
        (r"\b(whenever|when you can|low priority|no rush|fyi|question)\b", 0.2),
    ]
    
    # High-confidence keyword matching to reinforce or override ML predictions
    CATEGORY_KEYWORDS = {
        TicketCategory.TECHNICAL: [
            r"install", r"pip", r"npm", r"bug", r"crash", r"error", r"api", 
            r"server", r"down", r"setup", r"python", r"node", r"build"
        ],
        TicketCategory.BILLING: [
            r"invoice", r"payment", r"refund", r"billing", r"finance", 
            r"charge", r"subscription", r"pricing", r"transaction", r"bank"
        ],
        TicketCategory.LEGAL: [
            r"privacy", r"gdpr", r"terms", r"legal", r"compliance", r"license"
        ]
    }
    
    def __init__(self):
        self.categories = list(TicketCategory)
        self.model = self._load_model()
    
    def _load_model(self) -> Optional[object]:
        """Load the trained ML model, training it if not found."""
        if not os.path.exists(self.MODEL_PATH):
            print("ML model not found. Training now...")
            try:
                from ml.train import train_model
                train_model()
            except Exception as e:
                print(f"Error training ML model: {e}")
                return None

        if os.path.exists(self.MODEL_PATH):
            try:
                return joblib.load(self.MODEL_PATH)
            except Exception as e:
                print(f"Error loading ML model: {e}")
        return None
    
    def classify(self, text: str) -> Tuple[TicketCategory, float]:
        """
        Classify ticket into category and detect urgency.
        Uses a hybrid approach of ML and keyword reinforcement.
        """
        text_lower = text.lower()
        ml_category = TicketCategory.GENERAL
        
        # 1. Get ML Model Prediction
        if self.model:
            try:
                prediction = self.model.predict([text])[0]
                for cat in TicketCategory:
                    if cat.value.lower() == prediction.lower():
                        ml_category = cat
                        break
            except Exception as e:
                print(f"ML Prediction failed: {e}")
        
        # 2. Keyword Reinforcement (Boost or Override)
        final_category = ml_category
        keyword_matches = {}
        
        for category, patterns in self.CATEGORY_KEYWORDS.items():
            matches = sum(1 for p in patterns if re.search(p, text_lower))
            if matches > 0:
                keyword_matches[category] = matches
        
        # If the ML model says "General" but we have strong keyword matches, override it
        if ml_category == TicketCategory.GENERAL and keyword_matches:
            final_category = max(keyword_matches, key=keyword_matches.get)
        # If ML model predicted something but keywords strongly suggest otherwise, we could override
        # For now, we prefer keywords if ML is "General", or if they agree.
        elif ml_category in keyword_matches and keyword_matches[ml_category] > 0:
            final_category = ml_category
        elif keyword_matches:
            # If ML and Keywords disagree and ML isn't General, 
            # we check if keywords are significantly stronger
            best_keyword_cat = max(keyword_matches, key=keyword_matches.get)
            if keyword_matches[best_keyword_cat] >= 2: # High confidence
                final_category = best_keyword_cat
                
        print(f"Classification: ML={ml_category.value}, Keywords={list(keyword_matches.keys())}, Final={final_category.value}")

        # 3. Detect urgency using refined continuous logic
        urgency = self._detect_urgency(text, final_category)
        
        return final_category, urgency
    
    def _detect_urgency(self, text: str, category: TicketCategory = TicketCategory.GENERAL) -> float:
        """
        Detect urgency level using a multi-factor additive model.
        S = min(1.0, BaseMax + Modifiers + Bias)
        """
        text_lower = text.lower()
        
        # Factor 1: Base Max Score from Keywords
        base_score = 0.0
        matches_found = 0
        matched_patterns = set()
        
        for pattern, score in self.URGENCY_PATTERNS:
            if re.search(pattern, text_lower):
                base_score = max(base_score, score)
                matched_patterns.add(pattern)
                matches_found += 1
        
        if base_score == 0:
            # Default for general tickets without keywords
            base_score = 0.1
        
        # Factor 2: Keyword Density Boost (+0.05 for each unique extra match)
        density_mod = max(0, matches_found - 1) * 0.05
        
        # Factor 3: Emphasis Boost (caps, exclamations)
        emphasis_mod = 0.0
        if "!!!" in text:
            emphasis_mod += 0.05
        
        # CAPS LOCK detection (words > 4 chars in all caps)
        caps_words = re.findall(r"\b[A-Z]{5,}\b", text)
        if caps_words:
            emphasis_mod += 0.05
            
        # Factor 4: Category Bias
        category_bias = 0.0
        if category == TicketCategory.TECHNICAL:
            category_bias = 0.05
        elif category == TicketCategory.LEGAL:
            category_bias = 0.03
            
        # Final Score Calculation
        final_score = base_score + density_mod + emphasis_mod + category_bias
        
        # Clamp between 0.0 and 1.0
        return min(1.0, max(0.0, round(final_score, 2)))
    
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
classifier = TicketClassifier()
