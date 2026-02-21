"""
In-Memory Priority Queue (Milestone 1)
Uses Python's heapq for priority-based ticket processing
"""
import heapq
import threading
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass(order=True)
class Ticket:
    """
    Priority ticket for the queue.
    Order by: priority (desc), then by timestamp (asc)
    """
    priority: float = field(compare=True)
    timestamp: float = field(compare=True)
    ticket_id: str = field(compare=False)
    subject: str = field(compare=False)
    description: str = field(compare=False)
    category: str = field(compare=False)
    urgency: float = field(compare=False)
    status: str = field(compare=False, default="pending")
    created_at: datetime = field(compare=False, default_factory=datetime.now)
    metadata: Dict[str, Any] = field(compare=False, default_factory=dict)
    
    def __post_init__(self):
        # Negative priority for max-heap behavior
        self.priority = -self.priority


class PriorityQueue:
    """
    Thread-safe in-memory priority queue for ticket processing.
    Uses heapq for efficient priority operations.
    """
    
    def __init__(self):
        self._heap: List[Ticket] = []
        self._lock = threading.RLock()
        self._ticket_index: Dict[str, Ticket] = {}
    
    def enqueue(self, ticket: Ticket) -> str:
        """
        Add a ticket to the priority queue.
        
        Args:
            ticket: The ticket to add
            
        Returns:
            Ticket ID
        """
        with self._lock:
            heapq.heappush(self._heap, ticket)
            self._ticket_index[ticket.ticket_id] = ticket
            return ticket.ticket_id
    
    def dequeue(self) -> Optional[Ticket]:
        """
        Remove and return the highest priority ticket.
        
        Returns:
            The highest priority ticket, or None if queue is empty
        """
        with self._lock:
            if not self._heap:
                return None
            
            ticket = heapq.heappop(self._heap)
            if ticket.ticket_id in self._ticket_index:
                del self._ticket_index[ticket.ticket_id]
            
            return ticket
    
    def peek(self) -> Optional[Ticket]:
        """
        View the highest priority ticket without removing it.
        
        Returns:
            The highest priority ticket, or None if queue is empty
        """
        with self._lock:
            if not self._heap:
                return None
            return self._heap[0]
    
    def get_by_id(self, ticket_id: str) -> Optional[Ticket]:
        """
        Get a specific ticket by ID.
        
        Args:
            ticket_id: The ticket ID
            
        Returns:
            The ticket if found, None otherwise
        """
        with self._lock:
            return self._ticket_index.get(ticket_id)
    
    def update_priority(self, ticket_id: str, new_priority: float) -> bool:
        """
        Update the priority of an existing ticket.
        
        Args:
            ticket_id: The ticket ID
            new_priority: New priority value
            
        Returns:
            True if updated, False if ticket not found
        """
        with self._lock:
            if ticket_id not in self._ticket_index:
                return False
            
            old_ticket = self._ticket_index[ticket_id]
            
            # Create new ticket with updated priority
            new_ticket = Ticket(
                priority=new_priority,
                timestamp=old_ticket.timestamp,
                ticket_id=old_ticket.ticket_id,
                subject=old_ticket.subject,
                description=old_ticket.description,
                category=old_ticket.category,
                urgency=old_ticket.urgency,
                status=old_ticket.status,
                created_at=old_ticket.created_at,
                metadata=old_ticket.metadata
            )
            
            # Remove old ticket and add new one
            self._remove_ticket(old_ticket)
            self.enqueue(new_ticket)
            
            return True
    
    def _remove_ticket(self, ticket: Ticket) -> None:
        """Remove a specific ticket from the heap"""
        try:
            self._heap.remove(ticket)
            heapq.heapify(self._heap)
        except ValueError:
            pass
    
    def size(self) -> int:
        """
        Get the number of tickets in the queue.
        
        Returns:
            Number of tickets
        """
        with self._lock:
            return len(self._heap)
    
    def is_empty(self) -> bool:
        """
        Check if the queue is empty.
        
        Returns:
            True if empty, False otherwise
        """
        with self._lock:
            return len(self._heap) == 0
    
    def get_all(self) -> List[Ticket]:
        """
        Get all tickets in the queue (unsorted).
        
        Returns:
            List of all tickets
        """
        with self._lock:
            return list(self._ticket_index.values())
    
    def clear(self) -> None:
        """Clear all tickets from the queue"""
        with self._lock:
            self._heap.clear()
            self._ticket_index.clear()


# Global queue instance
ticket_queue = PriorityQueue()
