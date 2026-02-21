"""
Semantic Deduplication Service (Milestone 3)
Detects ticket storms and creates Master Incidents
"""
import threading
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict

import numpy as np

from ml.embeddings import embedding_service
from config import settings


@dataclass
class TicketEntry:
    """Entry for tracking tickets in deduplication"""
    ticket_id: str
    subject: str
    description: str
    embedding: np.ndarray
    created_at: datetime = field(default_factory=datetime.now)
    processed: bool = False


@dataclass
class MasterIncident:
    """Master incident created from similar tickets"""
    master_id: str
    ticket_ids: List[str]
    similarity_score: float
    category: str
    created_at: datetime
    suppressed_count: int = 0


class SemanticDeduplicator:
    """
    Detects semantic duplicates using sentence embeddings.
    Triggers Master Incident creation when:
    - similarity > 0.9 for more than 10 tickets in 5 minutes
    """
    
    def __init__(self):
        self._tickets: List[TicketEntry] = []
        self._master_incidents: Dict[str, MasterIncident] = {}
        self._lock = threading.RLock()
        
        # Configuration from settings
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD  # 0.9
        self.time_window_minutes = settings.DUPLICATE_TIME_WINDOW_MINUTES  # 5
        self.count_threshold = settings.DUPLICATE_COUNT_THRESHOLD  # 10
        
        # Ensure embedding model is loaded
        embedding_service.load()
    
    def add_ticket(self, ticket_id: str, subject: str, description: str) -> Tuple[bool, Optional[str]]:
        """
        Add a ticket for deduplication checking.
        
        Args:
            ticket_id: Unique ticket identifier
            subject: Ticket subject
            description: Ticket description
            
        Returns:
            Tuple of (is_duplicate, master_incident_id if exists)
        """
        with self._lock:
            # Combine subject and description for embedding
            text = f"{subject} {description}"
            embedding = embedding_service.get_embedding(text)
            
            ticket_entry = TicketEntry(
                ticket_id=ticket_id,
                subject=subject,
                description=description,
                embedding=embedding
            )
            
            # Check for similar tickets
            similar_tickets = self._find_similar_in_window(ticket_entry)
            
            if similar_tickets:
                # Check if we should create a Master Incident
                if len(similar_tickets) >= self.count_threshold:
                    master_id = self._create_master_incident(ticket_entry, similar_tickets)
                    return True, master_id
                
                # Link to existing master incident if any
                for sim_ticket in similar_tickets:
                    for master in self._master_incidents.values():
                        if sim_ticket.ticket_id in master.ticket_ids:
                            master.ticket_ids.append(ticket_id)
                            master.suppressed_count += 1
                            return True, master.master_id
            
            self._tickets.append(ticket_entry)
            self._cleanup_old_tickets()
            
            return False, None
    
    def _find_similar_in_window(self, new_ticket: TicketEntry) -> List[TicketEntry]:
        """
        Find similar tickets within the time window.
        
        Args:
            new_ticket: The new ticket to check
            
        Returns:
            List of similar tickets
        """
        cutoff_time = datetime.now() - timedelta(minutes=self.time_window_minutes)
        similar = []
        
        for ticket in self._tickets:
            # Skip if outside time window or already processed
            if ticket.created_at < cutoff_time or ticket.processed:
                continue
            
            # Calculate cosine similarity
            similarity = embedding_service.cosine_similarity(
                new_ticket.embedding,
                ticket.embedding
            )
            
            if similarity > self.similarity_threshold:
                similar.append(ticket)
        
        return similar
    
    def _create_master_incident(
        self, 
        new_ticket: TicketEntry, 
        similar_tickets: List[TicketEntry]
    ) -> str:
        """
        Create a Master Incident from similar tickets.
        
        Args:
            new_ticket: The new ticket
            similar_tickets: List of similar tickets
            
        Returns:
            Master incident ID
        """
        import uuid
        
        master_id = f"MASTER-{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate average similarity
        similarities = [
            embedding_service.cosine_similarity(new_ticket.embedding, t.embedding)
            for t in similar_tickets
        ]
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
        
        # Collect all ticket IDs
        ticket_ids = [t.ticket_id for t in similar_tickets]
        ticket_ids.append(new_ticket.ticket_id)
        
        # Determine category from similar tickets
        category = self._infer_category(similar_tickets)
        
        master_incident = MasterIncident(
            master_id=master_id,
            ticket_ids=ticket_ids,
            similarity_score=avg_similarity,
            category=category,
            created_at=datetime.now(),
            suppressed_count=len(ticket_ids) - 1  # Excluding the master
        )
        
        self._master_incidents[master_id] = master_incident
        
        # Mark similar tickets as processed
        for ticket in similar_tickets:
            ticket.processed = True
        
        print(f"🎯 Master Incident Created: {master_id}")
        print(f"   - Suppressed {master_incident.suppressed_count} duplicate alerts")
        print(f"   - Average similarity: {avg_similarity:.2%}")
        
        return master_id
    
    def _infer_category(self, tickets: List[TicketEntry]) -> str:
        """Infer category from ticket contents"""
        # Simple keyword-based category inference
        category_keywords = {
            "Billing": ["invoice", "payment", "bill", "charge", "refund"],
            "Technical": ["error", "bug", "crash", "broken", "api", "server"],
            "Legal": ["legal", "compliance", "gdpr", "privacy", "contract"]
        }
        
        category_counts = defaultdict(int)
        
        for ticket in tickets:
            text = f"{ticket.subject} {ticket.description}".lower()
            for category, keywords in category_keywords.items():
                if any(kw in text for kw in keywords):
                    category_counts[category] += 1
        
        if category_counts:
            return max(category_counts, key=category_counts.get)
        return "General"
    
    def _cleanup_old_tickets(self) -> None:
        """Remove tickets outside the time window"""
        cutoff_time = datetime.now() - timedelta(minutes=self.time_window_minutes * 2)
        self._tickets = [t for t in self._tickets if t.created_at > cutoff_time]
    
    def get_master_incident(self, master_id: str) -> Optional[MasterIncident]:
        """Get a master incident by ID"""
        with self._lock:
            return self._master_incidents.get(master_id)
    
    def get_all_master_incidents(self) -> List[MasterIncident]:
        """Get all master incidents"""
        with self._lock:
            return list(self._master_incidents.values())
    
    def get_stats(self) -> Dict:
        """Get deduplication statistics"""
        with self._lock:
            return {
                "tracked_tickets": len(self._tickets),
                "master_incidents": len(self._master_incidents),
                "total_suppressed": sum(m.suppressed_count for m in self._master_incidents.values()),
                "similarity_threshold": self.similarity_threshold,
                "time_window_minutes": self.time_window_minutes,
                "count_threshold": self.count_threshold
            }


# Global deduplication service
semantic_deduplicator = SemanticDeduplicator()
