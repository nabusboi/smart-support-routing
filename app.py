"""
Smart-Support Ticket Routing Engine — Milestone 2 API
Async broker pattern (API → Queue → Worker)
"""

import uuid
from fastapi import FastAPI, status, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, UTC
from typing import Dict, List, Optional

# Broker
from broker.async_broker import async_broker

# Connect broker safely
async_broker.connect()

app = FastAPI(
    title="Smart-Support Ticket Routing Engine",
    version="2.0.0"
)

# ================= TEMP STORE (for GET endpoints) =================
tickets_store: Dict[str, dict] = {}

# ================= MODELS =================

class TicketCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)


class AcceptedResponse(BaseModel):
    ticket_id: str
    status: str
    message: str


class TicketResponse(BaseModel):
    ticket_id: str
    subject: str
    description: str
    status: str
    created_at: str
    customer_id: str


class TicketListResponse(BaseModel):
    tickets: List[TicketResponse]
    total: int


class PriorityUpdate(BaseModel):
    priority: float = Field(..., ge=0, le=1)


# ================= ROOT =================

@app.get("/")
async def root():
    return {"message": "Smart-Support Async Router", "docs": "/docs"}


@app.get("/health")
async def health():
    size = async_broker.get_queue_size()   # ✅ FIXED
    return {"status": "healthy", "queue_size": size}


# ================= CREATE TICKET =================

@app.post(
    "/api/tickets",
    response_model=AcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def create_ticket(ticket_data: TicketCreate):

    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"

    payload = {
        "ticket_id": ticket_id,
        "subject": ticket_data.subject,
        "description": ticket_data.description,
        "metadata": {"customer_id": ticket_data.customer_id},
        "created_at": datetime.now(UTC).isoformat()
    }

    # publish to queue
    async_broker.publish_ticket(payload)

    # store basic info so GET works
    tickets_store[ticket_id] = {
        **payload,
        "status": "queued",
        "priority": None
    }

    return AcceptedResponse(
        ticket_id=ticket_id,
        status="accepted",
        message="Ticket queued for background processing"
    )


# ================= LIST =================

@app.get("/api/tickets", response_model=TicketListResponse)
async def list_tickets(status_filter: Optional[str] = None):

    data = list(tickets_store.values())

    if status_filter:
        data = [t for t in data if t["status"] == status_filter]

    return TicketListResponse(
        tickets=[
            TicketResponse(
                ticket_id=t["ticket_id"],
                subject=t["subject"],
                description=t["description"],
                status=t["status"],
                created_at=t["created_at"],
                customer_id=t["metadata"]["customer_id"]
            )
            for t in data
        ],
        total=len(data)
    )


# ================= GET ONE =================

@app.get("/api/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str):

    ticket = tickets_store.get(ticket_id)

    if not ticket:
        raise HTTPException(404, "Ticket not found")

    return TicketResponse(
        ticket_id=ticket["ticket_id"],
        subject=ticket["subject"],
        description=ticket["description"],
        status=ticket["status"],
        created_at=ticket["created_at"],
        customer_id=ticket["metadata"]["customer_id"]
    )


# ================= UPDATE PRIORITY =================

@app.put("/api/tickets/{ticket_id}/priority")
async def update_priority(ticket_id: str, data: PriorityUpdate):

    ticket = tickets_store.get(ticket_id)

    if not ticket:
        raise HTTPException(404, "Ticket not found")

    ticket["priority"] = data.priority

    return {"message": "priority updated", "ticket_id": ticket_id}


# ================= DELETE =================

@app.delete("/api/tickets/{ticket_id}")
async def delete_ticket(ticket_id: str):

    if ticket_id not in tickets_store:
        raise HTTPException(404, "Ticket not found")

    tickets_store[ticket_id]["status"] = "cancelled"

    return {"message": "ticket cancelled"}


# ================= RUN =================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)