# 🚀 Smart-Support Ticket Routing Engine - Frontend

A modern React + Tailwind CSS frontend for the Smart-Support Ticket Routing Engine.

## Features

- **Real-time Ticket Management**: Create, view, and track support tickets
- **ML Integration**: Automatic category classification and urgency detection
- **Agent Panel**: View and manage support agents with skill-based routing
- **Queue Monitor**: Live system status and queue monitoring
- **ML Insights**: Visual analytics of ML classification results
- **Circuit Breaker Control**: Toggle ML model fallback behavior

## Tech Stack

- **Frontend Framework**: React 18 with Vite
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Backend**: FastAPI (Python)

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.8+
- Redis (optional, for full async broker support)

### Installation

1. **Install frontend dependencies:**
```
bash
cd frontend
npm install
```

2. **Install backend dependencies:**
```
bash
pip install -r requirements.txt
```

### Running the Application

#### Option 1: Run Both (Recommended)
```
bash
# Windows
run_all.bat

# Linux/Mac
bash run_all.sh
```

#### Option 2: Run Separately

**Backend:**
```
bash
python app.py
# API will be available at http://localhost:8000
# API Docs at http://localhost:8000/docs
```

**Frontend:**
```
bash
cd frontend
npm run dev
# Frontend will be available at http://localhost:5173
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check with queue size |
| POST | `/api/tickets` | Create ticket with ML classification |
| GET | `/api/tickets` | List all tickets |
| GET | `/api/tickets/{id}` | Get ticket by ID |
| GET | `/api/stats` | System statistics |
| GET | `/api/ml/status` | ML models status |
| POST | `/api/ml/classify` | Classify text with ML |
| POST | `/api/ml/circuit-breaker/toggle` | Toggle circuit breaker |
| GET | `/api/agents` | List all agents |
| POST | `/api/agents/register` | Register new agent |

## ML Classification

The backend automatically classifies tickets into:
- **Billing**: Invoice, payment, subscription issues
- **Technical**: Errors, bugs, performance issues
- **Legal**: Compliance, GDPR, contracts
- **General**: Other inquiries

Urgency is scored from 0-100% based on sentiment analysis.

## Demo Mode

If the backend API is not available, the frontend will run in demo mode with sample data.

## Screenshots

The dashboard includes:
1. **Ticket Form**: Submit tickets with real-time ML classification
2. **Ticket List**: Filter and search tickets with category/urgency indicators
3. **Queue Monitor**: Real-time system status and ML model health
4. **Agent Panel**: View agent skills and current workload
5. **ML Insights**: Visual analytics of classification results

## Hackathon Tips

1. **Showcase ML**: Use the ML Insights tab to demonstrate your classification accuracy
2. **Circuit Breaker**: Toggle the circuit breaker to show fallback behavior
3. **Agent Routing**: Register agents with different skills to see routing in action
4. **Demo Scenarios**:
   - Create a "broken" ticket → High urgency, Technical category
   - Create a "payment issue" ticket → Medium urgency, Billing category
   - Create a "legal question" ticket → Legal category
