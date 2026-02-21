"""
Unified ML Router (Milestone 3)
Integrates baseline classifier, transformer model, circuit breaker, and deduplication
"""
import time
from typing import Dict, Tuple, Optional, Any
from dataclasses import dataclass

from ml.classifier import BaselineClassifier, TicketCategory
from ml.transformer_model import TransformerClassifier
from ml.embeddings import embedding_service
from ml.deduplication import semantic_deduplicator
from routing.circuit_breaker import transformer_circuit, baseline_circuit, CircuitState
from config import settings


@dataclass
class ClassificationResult:
    """Result of ticket classification"""
    ticket_id: str
    category: str
    urgency: float
    sentiment_score: float
    model_used: str
    processing_time_ms: float
    is_master_incident: bool = False
    master_incident_id: Optional[str] = None


class UnifiedMLRouter:
    """
    Unified ML router that coordinates all ML components:
    - Baseline classifier (Milestone 1)
    - Transformer model (Milestone 2)  
    - Circuit breaker failover (Milestone 3)
    - Semantic deduplication (Milestone 3)
    """
    
    def __init__(self):
        # Initialize components
        self.baseline_classifier = BaselineClassifier()
        self.transformer_classifier = TransformerClassifier()
        
        # Circuit breakers
        self.transformer_circuit = transformer_circuit
        self.baseline_circuit = baseline_circuit
        
        # Deduplication
        self.deduplicator = semantic_deduplicator
        
        # Model selection logic
        self._use_transformer = True
    
    def classify(
        self, 
        ticket_id: str, 
        subject: str, 
        description: str,
        enable_dedup: bool = True
    ) -> ClassificationResult:
        """
        Classify a ticket using the best available model.
        
        Args:
            ticket_id: Unique ticket identifier
            subject: Ticket subject
            description: Ticket description
            enable_dedup: Whether to enable deduplication
            
        Returns:
            ClassificationResult with category, urgency, and model info
        """
        start_time = time.time()
        
        # Combine text for classification
        text = f"{subject} {description}"
        
        # Check circuit breaker state for transformer
        transformer_available = (
            self.transformer_circuit.state != CircuitState.OPEN and
            self.transformer_circuit.is_available()
        )
        
        # Determine which model to use
        if self._use_transformer and transformer_available:
            # Try transformer with circuit breaker timing
            try:
                category, urgency = self._classify_with_transformer(text)
                model_used = "transformer"
                self.transformer_circuit.record_success()
            except Exception as e:
                print(f"Transformer failed: {e}, falling back to baseline")
                category, urgency = self._classify_with_baseline(text)
                model_used = "baseline_fallback"
                self.transformer_circuit.record_failure()
        else:
            # Use baseline classifier
            category, urgency = self._classify_with_baseline(text)
            model_used = "baseline"
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Check deduplication (if enabled)
        is_master_incident = False
        master_incident_id = None
        
        if enable_dedup:
            is_duplicate, master_incident_id = self.deduplicator.add_ticket(
                ticket_id=ticket_id,
                subject=subject,
                description=description
            )
            is_master_incident = is_duplicate
        
        return ClassificationResult(
            ticket_id=ticket_id,
            category=category,
            urgency=urgency,
            sentiment_score=urgency,  # Use urgency as sentiment score
            model_used=model_used,
            processing_time_ms=processing_time_ms,
            is_master_incident=is_master_incident,
            master_incident_id=master_incident_id
        )
    
    def _classify_with_transformer(self, text: str) -> Tuple[str, float]:
        """Classify using transformer model with timing"""
        start = time.time()
        
        # Load model if needed
        if not self.transformer_classifier.is_available():
            self.transformer_classifier.load()
        
        category, urgency = self.transformer_classifier.classify(text)
        
        latency_ms = (time.time() - start) * 1000
        
        # Record latency for circuit breaker
        self.transformer_circuit.record_latency(latency_ms)
        
        # Check if we should switch to baseline
        if latency_ms > settings.CIRCUIT_BREAKER_THRESHOLD_MS:
            print(f"⚠️ Transformer latency {latency_ms}ms exceeded threshold, may switch to baseline")
            self._use_transformer = False
        
        return category, urgency
    
    def _classify_with_baseline(self, text: str) -> Tuple[str, float]:
        """Classify using baseline classifier"""
        category, urgency = self.baseline_classifier.classify(text)
        return category.value if isinstance(category, TicketCategory) else category, urgency
    
    def get_deduplication_stats(self) -> Dict:
        """Get deduplication statistics"""
        return self.deduplicator.get_stats()
    
    def get_circuit_breaker_status(self) -> Dict:
        """Get circuit breaker status for both models"""
        return {
            "transformer": {
                "state": self.transformer_circuit.state.value,
                "available": self.transformer_circuit.is_available()
            },
            "baseline": {
                "state": self.baseline_circuit.state.value,
                "available": self.baseline_circuit.is_available()
            }
        }
    
    def reset_circuits(self) -> None:
        """Manually reset both circuit breakers"""
        self.transformer_circuit.reset()
        self.baseline_circuit.reset()
        self._use_transformer = True
    
    def enable_transformer(self) -> None:
        """Manually enable transformer model"""
        self._use_transformer = True
        self.reset_circuits()
    
    def disable_transformer(self) -> None:
        """Manually disable transformer model"""
        self._use_transformer = False
        self.transformer_circuit._trigger_open()


# Global router instance
ml_router = UnifiedMLRouter()
