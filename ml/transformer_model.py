"""
Transformer-based Classifier (Milestone 2)
Replaces baseline classifier with deep learning model
"""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Tuple, List
import numpy as np
from config import settings


class TransformerClassifier:
    """
    Transformer-based classifier using DistilBERT for ticket categorization
    and sentiment analysis for urgency scoring.
    """
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.TRANSFORMER_MODEL
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._loaded = False
    
    def load(self):
        """Load the transformer model and tokenizer"""
        if self._loaded:
            return
        
        print(f"Loading transformer model: {self.model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name,
            num_labels=3  # Positive, Negative, Neutral
        )
        self.model.to(self.device)
        self.model.eval()
        self._loaded = print("Transformer model loaded successfully")
    
    def classify(self, text: str) -> Tuple[str, float]:
        """
        Classify ticket into category and generate urgency score.
        
        Args:
            text: The ticket text content
            
        Returns:
            Tuple of (category, urgency_score)
        """
        if not self._loaded:
            self.load()
        
        # Get sentiment for urgency score
        urgency = self._get_sentiment_score(text)
        
        # Get category based on keywords (enhanced with ML)
        category = self._classify_category(text)
        
        return category, urgency
    
    def _get_sentiment_score(self, text: str) -> float:
        """
        Generate continuous urgency score S ∈ [0, 1] using sentiment analysis.
        
        Args:
            text: The ticket text content
            
        Returns:
            Urgency score between 0 and 1
        """
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.softmax(outputs.logits, dim=-1)
            
            # Sentiment: 0=negative, 1=neutral, 2=positive
            # Map to urgency: negative = high urgency, positive = low urgency
            sentiment = probabilities[0].cpu().numpy()
            
            # Urgency = 1 - positive_probability
            # Higher negative sentiment = higher urgency
            urgency = 1.0 - sentiment[2]  # Assuming index 2 is positive
            
            # Clamp to [0, 1]
            return float(np.clip(urgency, 0.0, 1.0))
    
    def _classify_category(self, text: str) -> str:
        """
        Classify ticket into category using keyword matching
        (can be enhanced with fine-tuned model).
        
        Args:
            text: The ticket text content
            
        Returns:
            Category string
        """
        text_lower = text.lower()
        
        # Billing keywords
        billing_keywords = ["invoice", "payment", "bill", "charge", "refund", 
                          "subscription", "pricing", "billing", "transaction"]
        if any(kw in text_lower for kw in billing_keywords):
            return "Billing"
        
        # Technical keywords
        technical_keywords = ["error", "bug", "crash", "broken", "api", "server",
                              "database", "timeout", "exception", "technical"]
        if any(kw in text_lower for kw in technical_keywords):
            return "Technical"
        
        # Legal keywords
        legal_keywords = ["legal", "compliance", "gdpr", "privacy", "terms",
                         "contract", "regulation", "data protection"]
        if any(kw in text_lower for kw in legal_keywords):
            return "Legal"
        
        return "General"
    
    def batch_classify(self, texts: List[str]) -> List[Tuple[str, float]]:
        """
        Classify multiple tickets.
        
        Args:
            texts: List of ticket texts
            
        Returns:
            List of (category, urgency_score) tuples
        """
        return [self.classify(text) for text in texts]
    
    def is_available(self) -> bool:
        """Check if model is loaded and available"""
        return self._loaded


# Singleton instance
transformer_classifier = TransformerClassifier()
