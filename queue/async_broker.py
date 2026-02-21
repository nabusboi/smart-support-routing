"""
Async Broker for Ticket Processing (Milestone 2)
Uses Redis for message queue with async workers
"""
import asyncio
import json
import threading
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from dataclasses import dataclass
import redis
import time
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
    Handles ticket processing with 202 Accepted pattern.
    """
    
    def __init__(self):
        self._redis_client: Optional[redis.Redis] = None
        self._connected = False
        self._worker_task: Optional[asyncio.Task] = None
        self._workers: List[Callable] = []
        self._running = False
        self._lock = threading.RLock()
        self._processing_lock = asyncio.Lock()
        
        # Queue names
        self.TICKET_QUEUE = "tickets:queue"
        self.PROCESSING_SET = "tickets:processing"
        self.COMPLETED_SET = "tickets:completed"
        self.DEAD_LETTER = "tickets:dead_letter"
    
    def connect(self, host: str = None, port: int = None, db: int = None) -> bool:
        """
        Connect to Redis server.
        
        Args:
            host: Redis host (default from settings)
            port: Redis port (default from settings)
            db: Redis database number
            
        Returns:
            True if connected successfully
        """
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
            # Test connection
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
    
    def publish_ticket(self, ticket_data: Dict[str, Any]) -> str:
        """
        Publish a ticket to the async processing queue.
        Returns immediately with 202 Accepted.
        
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
        
        # Add to processing queue with atomic lock
        message_json = json.dumps(message.__dict__)
        
        # Use Redis transaction for atomic operations
        pipe = self._redis_client.pipeline()
        pipe.lpush(self.TICKET_QUEUE, message_json)
        pipe.sadd(self.PROCESSING_SET, ticket_id)
        pipe.expire(self.PROCESSING_SET, 3600)  # 1 hour TTL
        pipe.execute()
        
        return ticket_id
    
    def consume_ticket(self, timeout: int = 0) -> Optional[TicketMessage]:
        """
        Consume a ticket from the queue.
        
        Args:
            timeout: Timeout in seconds (0 = non-blocking)
            
        Returns:
            TicketMessage if available, None otherwise
        """
        if not self._connected:
            raise RuntimeError("Not connected to Redis")
        
        # Use atomic lock to prevent race conditions
        # BRPOPLPUSH: atomic move from queue to processing
        result = self._redis_client.brpoplpush(
            self.TICKET_QUEUE,
            self.PROCESSING_SET,
            timeout=timeout
        )
        
        if result:
            data = json.loads(result)
            return TicketMessage(**data)
        
        return None
    
    def complete_ticket(self, ticket_id: str) -> bool:
        """
        Mark a ticket as completed.
        
        Args:
            ticket_id: The ticket ID
            
        Returns:
            True if successful
        """
        if not self._connected:
            return False
        
        # Atomic move from processing to completed
        pipe = self._redis_client.pipeline()
        pipe.srem(self.PROCESSING_SET, ticket_id)
        pipe.sadd(self.COMPLETED_SET, ticket_id)
        pipe.execute()
        
        return True
    
    def fail_ticket(self, ticket_id: str, error: str = None) -> bool:
        """
        Move a failed ticket to dead letter queue.
        
        Args:
            ticket_id: The ticket ID
            error: Optional error message
            
        Returns:
            True if successful
        """
        if not self._connected:
            return False
        
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
    
    def get_queue_size(self) -> int:
        """Get the number of tickets in queue"""
        if not self._connected:
            return 0
        return self._redis_client.llen(self.TICKET_QUEUE)
    
    def get_processing_count(self) -> int:
        """Get the number of tickets being processed"""
        if not self._connected:
            return 0
        return self._redis_client.scard(self.PROCESSING_SET)
    
    def register_worker(self, worker: Callable) -> None:
        """
        Register a worker function to process tickets.
        
        Args:
            worker: Async callable that takes TicketMessage
        """
        self._workers.append(worker)
    
    async def process_queue(self) -> None:
        """Async method to process tickets from the queue"""
        self._running = True
        
        while self._running:
            try:
                # Get ticket with lock to prevent race conditions
                async with self._processing_lock:
                    ticket = self.consume_ticket(timeout=1)
                
                if ticket:
                    # Process with registered workers
                    for worker in self._workers:
                        try:
                            await worker(ticket)
                            self.complete_ticket(ticket.ticket_id)
                        except Exception as e:
                            print(f"Worker error for {ticket.ticket_id}: {e}")
                            self.fail_ticket(ticket.ticket_id, str(e))
                else:
                    # No ticket available, wait a bit
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                print(f"Queue processing error: {e}")
                await asyncio.sleep(1)
    
    def start_worker(self) -> None:
        """Start the async worker in a background thread"""
        if not self._running:
            def run_worker():
                asyncio.run(self.process_queue())
            
            thread = threading.Thread(target=run_worker, daemon=True)
            thread.start()
    
    def stop_worker(self) -> None:
        """Stop the async worker"""
        self._running = False


# Global broker instance
async_broker = AsyncBroker()
