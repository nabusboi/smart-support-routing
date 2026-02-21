# Smart-Support Ticket Routing Engine - Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [How It Works](#how-it-works)
4. [Project Structure](#project-structure)
5. [Components](#components)
   - [ML Module](#ml-module)
   - [Queue Module](#queue-module)
   - [Routing Module](#routing-module)
6. [How to Run](#how-to-run)
7. [How It Can Be Improved](#how-it-can-be-improved)
8. [Implementation Status](#implementation-status)
9. [API Endpoints](#api-endpoints)

---

## Overview

The **Smart-Support Ticket Routing Engine** is an intelligent system that automatically routes support tickets to the appropriate agents based on:
- **Category Classification**: Billing, Technical, Legal, or General
- **Urgency Detection**: Sentiment analysis to determine priority (0-1 scale)
- **Deduplication**: Semantic similarity detection to identify duplicate tickets
- **Agent Routing**: Skill-based assignment using constraint optimization

---

## Architecture

The system follows a three-milestone approach:

### Milestone 1: Minimum Viable Router (MVR)
- Baseline keyword-based classifier
- Regex-based urgency detection
- In-memory priority queue
- FastAPI REST API

### Milestone 2: Intelligent Queue
- Transformer-based classifier (DistilBERT)
- Sentiment analysis for urgency scoring
- Redis async broker
- 202 Accepted pattern with background workers
- Slack/Discord webhook integration for high-urgency tickets

### Milestone 3: Autonomous Orchestrator
- Sentence embeddings for semantic deduplication
- Cosine similarity for ticket clustering
- Circuit breaker pattern for ML model failover
- Skill-based agent routing

---

## Project Structure

```
hack_2026/
├── config.py                 # Configuration settings (Pydantic)
├── requirements.txt          # Python dependencies
├── TODO.md                   # Implementation plan
├── ml/
│   ├── __init__.py
│   ├── classifier.py         # Baseline classifier (keyword-based)
│   ├── transformer_model.py  # Transformer-based classifier
│   └── embeddings.py         # Sentence embeddings for deduplication
├── queue/
│   ├── __init__.py
│   ├── priority_queue.py     # In-memory priority queue (heapq)
│   └── async_broker.py       # Redis/RabbitMQ integration
└── routing/
    ├── __init__.py
    ├── circuit_breaker.py    # Circuit breaker pattern
    └── skill_routing.py      # Skill-based agent routing
```

---

## How It Works

### 1. Ticket Classification

**Baseline Classifier** (`ml/classifier.py`):
- Uses keyword matching to categorize tickets into:
  - **Billing**: invoice, payment, refund, subscription
  - **Technical**: error, bug, crash, API issues
  - **Legal**: compliance, GDPR, privacy, contract
  - **General**: Default category when no keywords match
- Detects urgency using regex patterns (urgent, broken, crash, etc.)

**Transformer Classifier** (`ml/transformer_model.py`):
- Uses DistilBERT model for sentiment analysis
- Generates continuous urgency score S ∈ [0, 1]
- Higher negative sentiment = higher urgency

### 2. Priority Queue

**In-Memory Priority Queue** (`queue/priority_queue.py`):
- Uses Python's `heapq` for efficient priority operations
- Thread-safe with `threading.RLock`
- Orders by priority (descending), then by timestamp (ascending)
- Supports: enqueue, dequeue, peek, update_priority

**Async Broker** (`queue/async_broker.py`):
- Redis-based message queue
- 202 Accepted pattern: returns immediately, processes in background
- Atomic locks for concurrent request handling
- Dead letter queue for failed tickets

### 3. Deduplication

**Embedding Service** (`ml/embeddings.py`):
- Uses `sentence-transformers` (all-MiniLM-L6-v2 model)
- Computes cosine similarity between ticket embeddings
- Threshold-based duplicate detection (default: 0.9)
- Master Incident detection for clustered issues

### 4. Circuit Breaker

**Circuit Breaker** (`routing/circuit_breaker.py`):
- Three states: CLOSED, OPEN, HALF_OPEN
- Monitors ML model latency
- Automatically failover to baseline if transformer latency > 500ms
- Configurable failure thresholds

### 5. Skill-Based Routing

**Agent Registry** (`routing/skill_routing.py`):
- Agents have skill vectors with proficiency scores (0-1)
- Constraint optimization for ticket assignment
- Score = skill_match × urgency_weight + availability_factor
- Supports: register, update status, route, release

---

## Components

### ML Module

| File | Purpose | Milestone |
|------|---------|-----------|
| `classifier.py` | Keyword-based classification + regex urgency | 1 |
| `transformer_model.py` | DistilBERT sentiment analysis | 2 |
| `embeddings.py` | Sentence embeddings + cosine similarity | 3 |

### Queue Module

| File | Purpose | Milestone |
|------|---------|-----------|
| `priority_queue.py` | Thread-safe in-memory heap | 1 |
| `async_broker.py` | Redis async processing | 2 |

### Routing Module

| File | Purpose | Milestone |
|------|---------|-----------|
| `circuit_breaker.py` | ML model failover | 3 |
| `skill_routing.py` | Agent assignment optimization | 3 |

---

## How to Run

### Prerequisites

1. **Python 3.8+**
2. **Redis Server** (for async broker)

### Installation

```
bash
# Clone the repository
cd hack_2026

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install PyTorch (CPU version)
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Configuration

Edit `config.py` to customize settings:

```
python
# API Settings
API_HOST: str = "0.0.0.0"
API_PORT: int = 8000
DEBUG: bool = True

# Redis Settings
REDIS_HOST: str = "localhost"
REDIS_PORT: int = 6379

# ML Model Settings
TRANSFORMER_MODEL: str = "distilbert-base-uncased-finetuned-sst-2-english"
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

# Urgency Settings
HIGH_URGENCY_THRESHOLD: float = 0.8
CIRCUIT_BREAKER_THRESHOLD_MS: int = 500
```

### Running the Application

```
bash
# Start Redis (if using async broker)
redis-server

# Start FastAPI server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Or run directly
python app.py
```

### Testing

```
bash
# Test the API
curl -X GET http://localhost:8000/health

# Submit a ticket
curl -X POST http://localhost:8000/api/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Payment failed",
    "description": "My credit card payment failed, please help urgently!",
    "customer_id": "cust_123"
  }'
```

---

## How It Can Be Improved

### 1. Model Improvements
- **Fine-tune the classifier**: Train on domain-specific ticket data
- **Add more categories**: Support additional ticket types (Sales, HR, etc.)
- **Multi-label classification**: Allow tickets in multiple categories

### 2. Queue Improvements
- **Add RabbitMQ support**: Alternative message broker
- **Persistent queue**: Use Redis streams for durability
- **Rate limiting**: Prevent abuse with token bucket algorithm

### 3. Routing Improvements
- **Load balancing**: Distribute tickets evenly among agents
- **SLA tracking**: Monitor response times and compliance
- **Escalation logic**: Auto-escalate tickets after X hours

### 4. Infrastructure
- **Add API layer**: Create FastAPI endpoints in `api/tickets.py`
- **Add webhooks**: Implement `webhooks/notifications.py`
- **Database**: Add PostgreSQL for ticket persistence
- **Monitoring**: Add Prometheus metrics and Grafana dashboards
- **Caching**: Use Redis for caching embeddings

### 5. Security
- **Authentication**: Add JWT/OAuth2 for API security
- **Rate limiting**: Prevent API abuse
- **Input validation**: Sanitize ticket content

---

## Implementation Status

### ✅ Milestone 1: Minimum Viable Router
- [x] Project structure
- [x] Baseline classifier (Billing/Technical/Legal)
- [x] Regex-based urgency detection
- [x] FastAPI REST API skeleton
- [x] In-memory priority queue
- [x] Ticket submission endpoint

### ⚠️ Milestone 2: Intelligent Queue
- [x] Transformer-based classifier (code exists)
- [x] Sentiment analysis for urgency
- [x] Redis async broker (code exists)
- [ ] 202 Accepted pattern integration
- [ ] Slack/Discord webhook integration

### 🔲 Milestone 3: Autonomous Orchestrator
- [x] Sentence embeddings (code exists)
- [x] Cosine similarity deduplication
- [ ] Master Incident detection logic
- [x] Circuit breaker pattern (code exists)
- [x] Skill-based agent routing (code exists)
- [ ] Constraint optimization for agent assignment

---

## API Endpoints

The API should include the following endpoints (to be implemented in `api/tickets.py`):

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/tickets` | Submit a new ticket |
| GET | `/api/tickets/{id}` | Get ticket by ID |
| GET | `/api/tickets` | List all tickets |
| PUT | `/api/tickets/{id}/priority` | Update ticket priority |
| DELETE | `/api/tickets/{id}` | Delete a ticket |
| POST | `/api/tickets/{id}/classify` | Re-classify a ticket |
| GET | `/api/agents` | List available agents |
| POST | `/api/agents` | Register a new agent |
| POST | `/api/tickets/{id}/assign` | Manually assign ticket |

---

## Example Usage

### Submit a Ticket

```
python
import httpx

response = httpx.post(
    "http://localhost:8000/api/tickets",
    json={
        "subject": "Cannot access my account",
        "description": "I've been trying to log in but keep getting a 500 error. This is urgent!",
        "customer_id": "cust_456"
    }
)
print(response.json())
# Output: {"ticket_id": "abc-123", "status": "pending", "category": "Technical", "urgency": 0.9}
```

### Using the Classifier

```
python
from ml.classifier import classifier

category, urgency = classifier.classify(
    "My invoice is wrong, please refund my payment"
)
print(f"Category: {category}, Urgency: {urgency}")
# Output: Category: Billing, Urgency: 0.5
```

### Using the Priority Queue

```
python
from queue.priority_queue import PriorityQueue, Ticket

queue = PriorityQueue()
ticket = Ticket(
    priority=0.8,
    timestamp=1234567890.0,
    ticket_id="t1",
    subject="Help!",
    description="Need help",
    category="Technical",
    urgency=0.8
)
queue.enqueue(ticket)
next_ticket = queue.dequeue()
```

### Agent Routing

```
python
from routing.skill_routing import agent_registry, TicketRequest

# Register agents
agent1_id = agent_registry.register_agent(
    name="John Doe",
    skills={"Billing": 0.9, "Technical": 0.5, "Legal": 0.3},
    capacity=5
)

# Route a ticket
ticket = TicketRequest(
    ticket_id="t1",
    category="Billing",
    urgency=0.7,
    description="Invoice issue"
)
agent_id = agent_registry.route_ticket(ticket)
print(f"Routed to agent: {agent_id}")
```

---

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - Ensure Redis is running: `redis-server`
   - Check connection settings in `config.py`

2. **Model Download Slow**
   - First run downloads ML models (~500MB)
   - Consider using pre-downloaded models

3. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`

4. **Port Already in Use**
   - Change port in `config.py` or use: `uvicorn app:app --port 8001`

---

## License

This project is for educational purposes.

---

*Generated for Smart-Support Ticket Routing Engine*
