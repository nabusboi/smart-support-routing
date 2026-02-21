"""
Smart-Support Ticket Routing Engine - Main Application
FastAPI REST API for ticket submission and management
"""
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import time

# Import ML modules
from ml.classifier import BaselineClassifier
from queue.priority_queue import PriorityQueue, Ticket
from routing.skill_routing import AgentRegistry, TicketRequest

# Initialize components
classifier = BaselineClassifier()
ticket_queue = PriorityQueue()
agent_registry = AgentRegistry()

app = FastAPI(
    title="Smart-Support Ticket Routing Engine",
    description="Intelligent ticket routing with ML-based categorization and agent assignment",
    version="1.0.0"
)

# ============ Models ============

class TicketCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)


class TicketResponse(BaseModel):
    ticket_id: str
    subject: str
    description: str
    category: str
    urgency: float
    priority: float
    status: str
    created_at: datetime
    customer_id: str


class TicketPriorityUpdate(BaseModel):
    new_priority: float = Field(..., ge=0, le=1)


class TicketListResponse(BaseModel):
    tickets: List[TicketResponse]
    total: int


class HealthResponse(BaseModel):
    status: str
    version: str
    queue_size: int


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1)
    skills: dict
    capacity: int = Field(default=5, ge=1, le=20)


class AgentResponse(BaseModel):
    agent_id: str
    name: str
    skills: dict
    capacity: int
    current_load: int


# ============ Root ============

@app.get("/")
async def root():
    return {"message": "Welcome to Smart-Support Ticket Routing Engine", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", version="1.0.0", queue_size=ticket_queue.size())


# ============ Ticket Create ============

@app.post("/api/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(ticket_data: TicketCreate):
    text = f"{ticket_data.subject} {ticket_data.description}"

    category, urgency = classifier.classify(text)

    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"

    ticket = Ticket(
        priority=urgency,
        timestamp=time.time(),
        ticket_id=ticket_id,
        subject=ticket_data.subject,
        description=ticket_data.description,
        category=category.value,
        urgency=urgency,
        status="pending",
        metadata={"customer_id": ticket_data.customer_id}
    )

    ticket_queue.enqueue(ticket)

    return TicketResponse(
        ticket_id=ticket.ticket_id,
        subject=ticket.subject,
        description=ticket.description,
        category=ticket.category,
        urgency=ticket.urgency,
        priority=-ticket.priority,
        status=ticket.status,
        created_at=ticket.created_at,
        customer_id=ticket_data.customer_id
    )


# ============ List Tickets ============

@app.get("/api/tickets", response_model=TicketListResponse)
async def list_tickets(status_filter: Optional[str] = None):
    tickets = ticket_queue.get_all()

    if status_filter:
        tickets = [t for t in tickets if t.status == status_filter]

    responses = [
        TicketResponse(
            ticket_id=t.ticket_id,
            subject=t.subject,
            description=t.description,
            category=t.category,
            urgency=t.urgency,
            priority=-t.priority,
            status=t.status,
            created_at=t.created_at,
            customer_id=t.metadata.get("customer_id", "unknown")
        )
        for t in tickets
    ]

    return TicketListResponse(tickets=responses, total=len(responses))


# ============ GET Ticket ============

@app.get("/api/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str):
    ticket = ticket_queue.get_by_id(ticket_id)

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return TicketResponse(
        ticket_id=ticket.ticket_id,
        subject=ticket.subject,
        description=ticket.description,
        category=ticket.category,
        urgency=ticket.urgency,
        priority=-ticket.priority,
        status=ticket.status,
        created_at=ticket.created_at,
        customer_id=ticket.metadata.get("customer_id", "unknown")
    )


# ============ DELETE ============

@app.delete("/api/tickets/{ticket_id}", status_code=204)
async def delete_ticket(ticket_id: str):
    ticket = ticket_queue.get_by_id(ticket_id)

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = "cancelled"


# ============ ⭐ FIXED PRIORITY ENDPOINT ============

@app.put("/api/tickets/{ticket_id}/priority", response_model=TicketResponse)
async def update_ticket_priority(ticket_id: str, data: TicketPriorityUpdate):

    success = ticket_queue.update_priority(ticket_id, data.new_priority)

    if not success:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = ticket_queue.get_by_id(ticket_id)

    return TicketResponse(
        ticket_id=ticket.ticket_id,
        subject=ticket.subject,
        description=ticket.description,
        category=ticket.category,
        urgency=ticket.urgency,
        priority=-ticket.priority,
        status=ticket.status,
        created_at=ticket.created_at,
        customer_id=ticket.metadata.get("customer_id", "unknown")
    )


# ============ Run ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)