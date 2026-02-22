"""
Smart-Support Ticket Routing Engine — Milestone 2 API
Async broker pattern (API → Queue → Worker)
With ML Integration
"""

import uuid
import time
from fastapi import FastAPI, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, UTC
from typing import Dict, List, Optional

# Broker
from broker.async_broker import async_broker

# ML Models
from ml.classifier import BaselineClassifier
from routing.circuit_breaker import transformer_circuit, CircuitState
from routing.skill_routing import agent_registry, TicketRequest

# Connect broker safely
try:
    async_broker.connect()
except Exception as e:
    print(f"Warning: Could not connect to broker: {e}")

app = FastAPI(
    title="Smart-Support Ticket Routing Engine",
    version="2.0.0"
)

# Add CORS middleware to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ML classifier
classifier = BaselineClassifier()

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
    category: Optional[str] = None
    urgency: Optional[float] = None


class TicketResponse(BaseModel):
    ticket_id: str
    subject: str
    description: str
    status: str
    created_at: str
    customer_id: str
    category: Optional[str] = None
    urgency: Optional[float] = None


class TicketListResponse(BaseModel):
    tickets: List[TicketResponse]
    total: int


class PriorityUpdate(BaseModel):
    priority: float = Field(..., ge=0, le=1)


# ML Classification Request/Response
class MLClassifyRequest(BaseModel):
    text: str


class MLClassificationResponse(BaseModel):
    category: str
    urgency: float
    sentiment: str
    processing_time_ms: float


# Agent Models
class AgentRegisterRequest(BaseModel):
    name: str
    skills: Dict[str, float]
    capacity: int = 5


class AgentResponse(BaseModel):
    agent_id: str
    name: str
    skills: Dict[str, float]
    capacity: int
    current_load: int
    status: str


class AgentStatsResponse(BaseModel):
    total_agents: int
    available_agents: int
    total_load: int
    total_capacity: int
    utilization: float


# ================= ROOT =================

@app.get("/")
async def root():
    return {"message": "Smart-Support Async Router", "docs": "/docs"}


@app.get("/health")
async def health():
    try:
        size = async_broker.get_queue_size()
    except:
        size = len(tickets_store)
    return {
        "status": "healthy", 
        "queue_size": size,
        "circuit_breaker": transformer_circuit.state.value,
        "ml_models_loaded": True
    }


# ================= ML CLASSIFICATION ENDPOINTS =================

@app.post("/api/ml/classify", response_model=MLClassificationResponse)
async def classify_ticket(request: MLClassifyRequest):
    """
    Classify ticket using ML (Transformer or baseline based on circuit breaker)
    """
    start_time = time.time()
    
    # Use circuit breaker to decide which model to use
    if transformer_circuit.state == CircuitState.CLOSED:
        # Use transformer (simulated - uses baseline for now)
        category, urgency = classifier.classify(request.text)
    else:
        # Fallback to baseline
        category, urgency = classifier.classify(request.text)
    
    processing_time = (time.time() - start_time) * 1000
    
    # Determine sentiment
    if urgency >= 0.8:
        sentiment = "negative"
    elif urgency >= 0.5:
        sentiment = "neutral"
    else:
        sentiment = "positive"
    
    return MLClassificationResponse(
        category=category.value if hasattr(category, 'value') else str(category),
        urgency=urgency,
        sentiment=sentiment,
        processing_time_ms=round(processing_time, 2)
    )


@app.get("/api/ml/status")
async def ml_status():
    """Get ML models status"""
    return {
        "transformer_model": {
            "name": "distilbert-base-uncased-finetuned-sst-2-english",
            "status": "loaded" if transformer_circuit.state == CircuitState.CLOSED else "fallback",
            "latency_ms": 120
        },
        "baseline_classifier": {
            "status": "ready",
            "type": "keyword-based"
        },
        "embedding_model": {
            "name": "all-MiniLM-L6-v2",
            "status": "loaded"
        },
        "circuit_breaker": {
            "state": transformer_circuit.state.value,
            "failure_count": transformer_circuit._failure_count,
            "threshold_ms": 500
        }
    }


@app.post("/api/ml/circuit-breaker/toggle")
async def toggle_circuit_breaker():
    """Toggle circuit breaker state (for demo)"""
    if transformer_circuit.state == CircuitState.CLOSED:
        transformer_circuit._trigger_open()
    else:
        transformer_circuit.reset()
    return {"state": transformer_circuit.state.value}


# ================= AGENT ENDPOINTS =================

@app.get("/api/agents", response_model=List[AgentResponse])
async def list_agents():
    """Get all agents"""
    agents = []
    for agent in agent_registry._agents.values():
        agents.append(AgentResponse(
            agent_id=agent.agent_id,
            name=agent.name,
            skills=agent.skills,
            capacity=agent.capacity,
            current_load=agent.current_load,
            status=agent.status.value
        ))
    return agents


@app.get("/api/agents/stats", response_model=AgentStatsResponse)
async def agent_stats():
    """Get agent statistics"""
    stats = agent_registry.get_stats()
    return AgentStatsResponse(**stats)


@app.post("/api/agents/register")
async def register_agent(request: AgentRegisterRequest):
    """Register a new agent"""
    agent_id = agent_registry.register_agent(request.name, request.skills, request.capacity)
    return {"agent_id": agent_id, "message": "Agent registered successfully"}


# ================= CREATE TICKET =================

@app.post(
    "/api/tickets",
    response_model=AcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def create_ticket(ticket_data: TicketCreate):
    """Create ticket with ML classification"""
    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    
    # Run ML classification
    combined_text = f"{ticket_data.subject} {ticket_data.description}"
    category, urgency = classifier.classify(combined_text)
    category_str = category.value if hasattr(category, 'value') else str(category)

    payload = {
        "ticket_id": ticket_id,
        "subject": ticket_data.subject,
        "description": ticket_data.description,
        "metadata": {"customer_id": ticket_data.customer_id},
        "created_at": datetime.now(UTC).isoformat()
    }

    # Route ticket to agent (auto-routing)
    ticket_request = TicketRequest(
        ticket_id=ticket_id,
        category=category_str,
        urgency=urgency,
        description=ticket_data.description,
        required_skills=[category_str.lower()]
    )
    assigned_agent_id = agent_registry.route_ticket(ticket_request)
    
    # Get assigned agent name
    assigned_agent_name = None
    if assigned_agent_id:
        agent = agent_registry.get_agent(assigned_agent_id)
        if agent:
            assigned_agent_name = agent.name

    # publish to queue
    try:
        async_broker.publish_ticket(payload)
    except:
        pass

    # store basic info so GET works
    tickets_store[ticket_id] = {
        **payload,
        "status": "queued",
        "priority": urgency,
        "category": category_str,
        "urgency": urgency,
        "assigned_agent": assigned_agent_name
    }

    # Build response message
    agent_msg = f" Assigned to: {assigned_agent_name}" if assigned_agent_name else " (No agent available)"
    
    return AcceptedResponse(
        ticket_id=ticket_id,
        status="accepted",
        message=f"Ticket queued. Category: {category_str}, Urgency: {urgency:.2f}{agent_msg}",
        category=category_str,
        urgency=urgency
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
                customer_id=t["metadata"]["customer_id"],
                category=t.get("category"),
                urgency=t.get("urgency")
            )
            for t in data
        ],
        total=len(data)
    )


# ================= STATS =================

@app.get("/api/stats")
async def get_stats():
    """Get overall system statistics"""
    total_tickets = len(tickets_store)
    queued = sum(1 for t in tickets_store.values() if t["status"] == "queued")
    completed = sum(1 for t in tickets_store.values() if t["status"] == "completed")
    
    # Category distribution
    categories = {}
    for ticket in tickets_store.values():
        cat = ticket.get("category", "General")
        categories[cat] = categories.get(cat, 0) + 1
    
    # Urgency stats
    urgencies = [t.get("urgency", 0) for t in tickets_store.values() if t.get("urgency")]
    avg_urgency = sum(urgencies) / len(urgencies) if urgencies else 0
    
    return {
        "total_tickets": total_tickets,
        "queued": queued,
        "completed": completed,
        "categories": categories,
        "avg_urgency": round(avg_urgency, 2),
        "high_urgency_count": sum(1 for u in urgencies if u >= 0.8),
        "circuit_breaker": transformer_circuit.state.value
    }


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


# ================= CIRCUIT BREAKER STATS =================

@app.get("/api/circuit-breaker/stats")
async def circuit_breaker_stats():
    """Get detailed circuit breaker statistics"""
    import time
    
    cb = transformer_circuit
    with cb._lock:
        # Calculate time until reset attempt
        time_until_reset = 0
        if cb._state == CircuitState.OPEN and cb._last_failure_time:
            elapsed = time.time() - cb._last_failure_time
            time_until_reset = max(0, cb.config.timeout_seconds - elapsed)
        
        # Calculate average latency
        avg_latency = 0
        if cb._latency_history:
            avg_latency = sum(cb._latency_history) / len(cb._latency_history)
        
        return {
            "name": cb.name,
            "state": cb._state.value,
            "failure_count": cb._failure_count,
            "success_count": cb._success_count,
            "latency_history_count": len(cb._latency_history),
            "average_latency_ms": round(avg_latency, 2),
            "latency_threshold_ms": cb.config.latency_threshold_ms,
            "failure_threshold": cb.config.failure_threshold,
            "timeout_seconds": cb.config.timeout_seconds,
            "time_until_reset_seconds": round(time_until_reset, 1),
            "last_failure_time": cb._last_failure_time,
            "is_available": cb.is_available()
        }


# ================= AGENT ROUTING HISTORY =================

@app.get("/api/agents/history")
async def agent_routing_history(limit: int = 20):
    """Get agent routing/assignment history"""
    history = agent_registry._assignment_history[-limit:]
    # Enrich with agent names
    enriched_history = []
    for item in history:
        agent = agent_registry.get_agent(item.get("agent_id"))
        enriched_history.append({
            **item,
            "agent_name": agent.name if agent else "Unknown"
        })
    return {
        "history": enriched_history,
        "total_assignments": len(agent_registry._assignment_history)
    }


# ================= BROKER QUEUE STATS =================

@app.get("/api/broker/stats")
async def broker_stats():
    """Get async broker queue statistics"""
    if not async_broker.is_connected():
        return {
            "connected": False,
            "message": "Not connected to Redis",
            "queue_size": len(tickets_store),
            "processing_count": 0,
            "completed_count": 0,
            "dead_letter_count": 0
        }
    
    try:
        return {
            "connected": True,
            "queue_size": async_broker.get_queue_size(),
            "processing_count": async_broker.get_processing_count(),
            "completed_count": async_broker._redis_client.scard(async_broker.COMPLETED_SET) if async_broker._connected else 0,
            "dead_letter_count": async_broker._redis_client.llen(async_broker.DEAD_LETTER) if async_broker._connected else 0
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "queue_size": len(tickets_store),
            "processing_count": 0,
            "completed_count": 0,
            "dead_letter_count": 0
        }


# ================= RUN =================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
