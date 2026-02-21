"""
Async Broker for Ticket Processing (Milestone 2)
Uses Redis for message queue - thin layer with only push/pop/lock operations
"""
import json
import threading
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import redis
import uuid

from config import settings


@dataclass
class TicketMessage:
    """Message format for ticket queue"""
    ticket_id: str
    subject: str
    description: str
    category: str
    urgency: float
    sentiment_score: float
    created_at: str
    metadata: Dict[str, Any]


class AsyncBroker:
    """
    Asynchronous message broker using Redis.
    Thin layer with only push/pop/lock operations.
    """
    
    def __init__(self):
        self._redis_client: Optional[redis.Redis] = None
        self._connected = False
        self._lock = threading.RLock()
        
        # Queue names
        self.TICKET_QUEUE = "tickets:queue"
        self.PROCESSING_SET = "tickets:processing"
        self.COMPLETED_SET = "tickets:completed"
        self.DEAD_LETTER = "tickets:dead_letter"
    
    def connect(self, host: str = None, port: int = None, db: int = None) -> bool:
        """Connect to Redis server."""
        host = host or settings.REDIS_HOST
        port = port or settings.REDIS_PORT
        db = db or settings.REDIS_DB
        
        try:
            self._redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self._redis_client.ping()
            self._connected = True
            print(f"Connected to Redis at {host}:{port}")
            return True
        except redis.ConnectionError as e:
            print(f"Failed to connect to Redis: {e}")
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from Redis server"""
        if self._redis_client:
            self._redis_client.close()
            self._connected = False
    
    def is_connected(self) -> bool:
        """Check if connected to Redis"""
        return self._connected
    
    def get_queue_size(self) -> int:
        """Get the number of tickets in queue"""
        if not self._connected:
            return 0
        return self._redis_client.llen(self.TICKET_QUEUE)
    
    # ============ PUSH OPERATIONS ============
    
    def publish_ticket(self, ticket_data: Dict[str, Any]) -> str:
        """
        Push a ticket to the async processing queue.
        Returns ticket ID.
        
        Args:
            ticket_data: Ticket information dictionary
            
        Returns:
            Ticket ID
        """
        if not self._connected:
            raise RuntimeError("Not connected to Redis")
        
        ticket_id = ticket_data.get("ticket_id", str(uuid.uuid4()))
        
        message = TicketMessage(
            ticket_id=ticket_id,
            subject=ticket_data.get("subject", ""),
            description=ticket_data.get("description", ""),
            category=ticket_data.get("category", "General"),
            urgency=ticket_data.get("urgency", 0.5),
            sentiment_score=ticket_data.get("sentiment_score", 0.5),
            created_at=ticket_data.get("created_at", datetime.now().isoformat()),
            metadata=ticket_data.get("metadata", {})
        )
        
        # Atomic push with lock
        message_json = json.dumps(message.__dict__)
        
        with self._lock:
            pipe = self._redis_client.pipeline()
            pipe.lpush(self.TICKET_QUEUE, message_json)
            pipe.sadd(self.PROCESSING_SET, ticket_id)
            pipe.expire(self.PROCESSING_SET, 3600)
            pipe.execute()
        
        return ticket_id
    
    # ============ POP OPERATIONS ============
    
    def consume_ticket(self, timeout: int = 0) -> Optional[TicketMessage]:
        """
        Pop a ticket from the queue (blocking).
        
        Args:
            timeout: Timeout in seconds (0 = non-blocking)
            
        Returns:
            TicketMessage if available, None otherwise
        """
        if not self._connected:
            raise RuntimeError("Not connected to Redis")
        
        # Atomic move from queue to processing set
        result = self._redis_client.brpoplpush(
            self.TICKET_QUEUE,
            self.PROCESSING_SET,
            timeout=timeout
        )
        
        if result:
            data = json.loads(result)
            return TicketMessage(**data)
        
        return None
    
    # ============ LOCK/STATUS OPERATIONS ============
    
    def complete_ticket(self, ticket_id: str) -> bool:
        """
        Mark a ticket as completed (release lock).
        
        Args:
            ticket_id: The ticket ID
            
        Returns:
            True if successful
        """
        if not self._connected:
            return False
        
        with self._lock:
            pipe = self._redis_client.pipeline()
            pipe.srem(self.PROCESSING_SET, ticket_id)
            pipe.sadd(self.COMPLETED_SET, ticket_id)
            pipe.execute()
        
        return True
    
    def fail_ticket(self, ticket_id: str, error: str = None) -> bool:
        """
        Move a failed ticket to dead letter queue (release lock).
        
        Args:
            ticket_id: The ticket ID
            error: Optional error message
            
        Returns:
            True if successful
        """
        if not self._connected:
            return False
        
        with self._lock:
            pipe = self._redis_client.pipeline()
            pipe.srem(self.PROCESSING_SET, ticket_id)
            if error:
                pipe.lpush(self.DEAD_LETTER, json.dumps({
                    "ticket_id": ticket_id,
                    "error": error,
                    "timestamp": datetime.now().isoformat()
                }))
            pipe.execute()
        
        return True
    
    def get_processing_count(self) -> int:
        """Get the number of tickets being processed"""
        if not self._connected:
            return 0
        return self._redis_client.scard(self.PROCESSING_SET)


# Global broker instance
async_broker = AsyncBroker()
