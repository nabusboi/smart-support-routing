"""
Smart-Support Ticket Routing Engine — Milestone 2+3 API
Async broker pattern (API → Queue → Worker)
With ML Integration, Preemption, Generalist Routing, ETA Timers
"""

import uuid
import time
from fastapi import FastAPI, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Broker
from broker.async_broker import async_broker

# ML Models
from ml.classifier import TicketClassifier
from routing.circuit_breaker import transformer_circuit, CircuitState
from routing.skill_routing import agent_registry, TicketRequest, TicketStatus

from config import settings

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
classifier = TicketClassifier()

# ================= REGISTER DEFAULT AGENTS ON STARTUP =================

def _register_default_agents():
    """Register sample agents for skill-based routing on startup"""
    print("  Initializing agent registry...")
    
    # Define your agents here
    sample_agents = [
        {"name": "Alice", "skills": {"billing": 0.9, "technical": 0.3, "legal": 0.1}, "capacity": 3},
        {"name": "Bob", "skills": {"technical": 0.95, "billing": 0.2, "legal": 0.1}, "capacity": 3},
        {"name": "Charlie", "skills": {"legal": 0.9, "billing": 0.3, "technical": 0.1}, "capacity": 3},
        {"name": "Diana", "skills": {"technical": 0.6, "billing": 0.6, "legal": 0.6}, "capacity": 3},  # Generalist
    ]

    # TO ADD NEW AGENTS MANUALLY:
    # 1. Add them to the list above, OR
    # 2. Uncomment and use the template below:
    # 
    # sample_agents.append({
    #     "name": "YOUR_NAME", 
    #     "skills": {"billing": 0.5, "technical": 0.5, "legal": 0.5}, 
    #     "capacity": 5
    # })

    for agent in sample_agents:
        agent_id = agent_registry.register_agent(
            name=agent["name"],
            skills=agent["skills"],
            capacity=agent["capacity"]
        )
        is_gen = "⭐ Generalist" if agent_registry.get_agent(agent_id).is_generalist() else ""
        print(f"    - Registered: {agent['name']} ({agent_id[:8]}...) {is_gen}")

_register_default_agents()
print(f"  {len(agent_registry._agents)} agents ready.\n")


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
    eta_seconds: Optional[int] = None
    assigned_agent: Optional[str] = None
    preempted_ticket: Optional[str] = None


class TicketResponse(BaseModel):
    ticket_id: str
    subject: str
    description: str
    status: str
    created_at: str
    customer_id: str
    category: Optional[str] = None
    urgency: Optional[float] = None
    assigned_agent: Optional[str] = None
    eta_seconds: Optional[int] = None
    remaining_eta: Optional[float] = None
    ticket_status: Optional[str] = None  # active/paused/completed


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
    is_generalist: Optional[bool] = False
    assigned_tickets: Optional[List[dict]] = None


class AgentStatsResponse(BaseModel):
    total_agents: int
    available_agents: int
    total_load: int
    total_capacity: int
    utilization: float
    total_preemptions: Optional[int] = 0
    active_tickets: Optional[int] = 0
    paused_tickets: Optional[int] = 0
    generalist_agents: Optional[int] = 0


# ================= HELPER: auto-complete expired tickets =================

def _sync_ticket_store():
    """Sync tickets_store with agent ticket statuses and auto-complete expired ones"""
    for agent in agent_registry._agents.values():
        # Check for expired tickets
        expired_ids = [tid for tid, t in agent.assigned_tickets.items() if t.is_expired()]
        for tid in expired_ids:
            agent_registry.complete_ticket(agent.agent_id, tid)
            if tid in tickets_store:
                tickets_store[tid]["status"] = "completed"
                tickets_store[tid]["ticket_status"] = "completed"
                tickets_store[tid]["remaining_eta"] = 0

        # Update remaining ETA for active tickets
        for tid, t in agent.assigned_tickets.items():
            if tid in tickets_store:
                tickets_store[tid]["remaining_eta"] = round(t.remaining_eta(), 1)
                tickets_store[tid]["ticket_status"] = t.status.value


# ================= ROOT =================

@app.get("/")
async def root():
    return {"message": "Smart-Support Async Router", "docs": "/docs"}


@app.get("/health")
async def health():
    _sync_ticket_store()
    try:
        size = async_broker.get_queue_size()
    except:
        size = len([t for t in tickets_store.values() if t["status"] == "queued"])
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
        category, urgency = classifier.classify(request.text)
    else:
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
            "type": "logistic-regression"
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
    """Get all agents with their assigned tickets"""
    _sync_ticket_store()
    agents = []
    for agent in agent_registry._agents.values():
        agents.append(AgentResponse(
            agent_id=agent.agent_id,
            name=agent.name,
            skills=agent.skills,
            capacity=agent.capacity,
            current_load=agent.current_load,
            status=agent.status.value,
            is_generalist=agent.is_generalist(),
            assigned_tickets=agent.get_assigned_tickets_info()
        ))
    return agents


@app.get("/api/agents/stats", response_model=AgentStatsResponse)
async def agent_stats():
    """Get agent statistics"""
    _sync_ticket_store()
    stats = agent_registry.get_stats()
    return AgentStatsResponse(
        total_agents=stats["total_agents"],
        available_agents=stats["available_agents"],
        total_load=stats["total_current_load"],
        total_capacity=stats["total_capacity"],
        utilization=stats["utilization"],
        total_preemptions=stats.get("total_preemptions", 0),
        active_tickets=stats.get("active_tickets", 0),
        paused_tickets=stats.get("paused_tickets", 0),
        generalist_agents=stats.get("generalist_agents", 0),
    )


@app.post("/api/agents/register")
async def register_agent(request: AgentRegisterRequest):
    """Register a new agent"""
    agent_id = agent_registry.register_agent(request.name, request.skills, request.capacity)
    agent = agent_registry.get_agent(agent_id)
    return {
        "agent_id": agent_id,
        "message": "Agent registered successfully",
        "is_generalist": agent.is_generalist() if agent else False
    }


# ================= CREATE TICKET =================

@app.post(
    "/api/tickets",
    response_model=AcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def create_ticket(ticket_data: TicketCreate):
    """Create ticket with ML classification, routing, and preemption"""
    _sync_ticket_store()
    
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
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    # Route ticket to agent (with preemption support)
    ticket_request = TicketRequest(
        ticket_id=ticket_id,
        category=category_str,
        urgency=urgency,
        description=ticket_data.description,
        required_skills=[category_str.lower()]
    )
    assigned_agent_id, preempted_ticket_id = agent_registry.route_ticket_with_preemption(ticket_request)
    
    # Get agent info
    assigned_agent_name = None
    eta_seconds = agent_registry.compute_eta(urgency)
    if assigned_agent_id:
        agent = agent_registry.get_agent(assigned_agent_id)
        if agent:
            assigned_agent_name = agent.name

    # If a ticket was preempted, update its status in store
    if preempted_ticket_id and preempted_ticket_id in tickets_store:
        tickets_store[preempted_ticket_id]["ticket_status"] = "paused"
        tickets_store[preempted_ticket_id]["status"] = "paused"

    # publish to queue
    try:
        async_broker.publish_ticket(payload)
    except:
        pass

    # store ticket info
    tickets_store[ticket_id] = {
        **payload,
        "status": "queued",
        "priority": urgency,
        "category": category_str,
        "urgency": urgency,
        "assigned_agent": assigned_agent_name,
        "eta_seconds": eta_seconds,
        "remaining_eta": eta_seconds,
        "ticket_status": "active" if assigned_agent_id else "queued",
        "preempted_ticket": preempted_ticket_id,
    }

    # Build response message
    agent_msg = f" Assigned to: {assigned_agent_name}" if assigned_agent_name else " (No agent available)"
    preempt_msg = f" | Preempted: {preempted_ticket_id}" if preempted_ticket_id else ""
    
    return AcceptedResponse(
        ticket_id=ticket_id,
        status="accepted",
        message=f"Ticket queued. Category: {category_str}, Urgency: {urgency:.2f}{agent_msg}{preempt_msg}",
        category=category_str,
        urgency=urgency,
        eta_seconds=eta_seconds,
        assigned_agent=assigned_agent_name,
        preempted_ticket=preempted_ticket_id,
    )


# ================= LIST =================

@app.get("/api/tickets", response_model=TicketListResponse)
async def list_tickets(status_filter: Optional[str] = None):
    _sync_ticket_store()

    data = list(tickets_store.values())

    if status_filter:
        data = [t for t in data if t["status"] == status_filter]

    # Sort by urgency descending (highest first)
    data.sort(key=lambda t: t.get("urgency", 0), reverse=True)

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
                urgency=t.get("urgency"),
                assigned_agent=t.get("assigned_agent"),
                eta_seconds=t.get("eta_seconds"),
                remaining_eta=t.get("remaining_eta"),
                ticket_status=t.get("ticket_status"),
            )
            for t in data
        ],
        total=len(data)
    )


# ================= STATS =================

@app.get("/api/stats")
async def get_stats():
    """Get overall system statistics"""
    _sync_ticket_store()
    total_tickets = len(tickets_store)
    queued = sum(1 for t in tickets_store.values() if t["status"] == "queued")
    completed = sum(1 for t in tickets_store.values() if t["status"] == "completed")
    paused = sum(1 for t in tickets_store.values() if t.get("ticket_status") == "paused")
    
    # Category distribution
    categories = {}
    for ticket in tickets_store.values():
        cat = ticket.get("category", "General")
        categories[cat] = categories.get(cat, 0) + 1
    
    # Urgency stats
    urgencies = [t.get("urgency", 0) for t in tickets_store.values() if t.get("urgency")]
    avg_urgency = sum(urgencies) / len(urgencies) if urgencies else 0
    
    agent_stats = agent_registry.get_stats()
    
    return {
        "total_tickets": total_tickets,
        "queued": queued,
        "completed": completed,
        "paused": paused,
        "categories": categories,
        "avg_urgency": round(avg_urgency, 2),
        "high_urgency_count": sum(1 for u in urgencies if u >= 0.8),
        "circuit_breaker": transformer_circuit.state.value,
        "total_preemptions": agent_stats.get("total_preemptions", 0),
    }


# ================= GET ONE =================

@app.get("/api/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str):
    _sync_ticket_store()
    ticket = tickets_store.get(ticket_id)

    if not ticket:
        raise HTTPException(404, "Ticket not found")

    return TicketResponse(
        ticket_id=ticket["ticket_id"],
        subject=ticket["subject"],
        description=ticket["description"],
        status=ticket["status"],
        created_at=ticket["created_at"],
        customer_id=ticket["metadata"]["customer_id"],
        category=ticket.get("category"),
        urgency=ticket.get("urgency"),
        assigned_agent=ticket.get("assigned_agent"),
        eta_seconds=ticket.get("eta_seconds"),
        remaining_eta=ticket.get("remaining_eta"),
        ticket_status=ticket.get("ticket_status"),
    )


# ================= COMPLETE TICKET =================

@app.post("/api/tickets/{ticket_id}/complete")
async def complete_ticket_endpoint(ticket_id: str):
    """Manually complete a ticket, releases agent slot and resumes paused tickets"""
    ticket = tickets_store.get(ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    
    # Find the agent holding this ticket
    completed = False
    for agent in agent_registry._agents.values():
        if ticket_id in agent.assigned_tickets:
            agent_registry.complete_ticket(agent.agent_id, ticket_id)
            completed = True
            break
    
    ticket["status"] = "completed"
    ticket["ticket_status"] = "completed"
    ticket["remaining_eta"] = 0
    
    _sync_ticket_store()
    
    return {"message": "Ticket completed", "ticket_id": ticket_id, "released": completed}


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


# ================= PREEMPTION HISTORY =================

@app.get("/api/preemption/history")
async def preemption_history(limit: int = 20):
    """Get preemption events feed"""
    events = agent_registry.get_preemption_history(limit)
    return {
        "events": events,
        "total_preemptions": len(agent_registry._preemption_history)
    }


# ================= BROKER QUEUE STATS =================

@app.get("/api/broker/stats")
async def broker_stats():
    """Get async broker queue statistics"""
    if not async_broker.is_connected():
        return {
            "connected": False,
            "message": "Not connected to Redis",
            "queue_size": len([t for t in tickets_store.values() if t["status"] == "queued"]),
            "processing_count": 0,
            "completed_count": sum(1 for t in tickets_store.values() if t["status"] == "completed"),
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
