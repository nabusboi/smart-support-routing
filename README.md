# 🎫 Smart-Support Ticket Routing Engine

An intelligent, high-performance ticket routing system that uses **Heuristic Regex Classification** to categorize support requests and assign them to the best-suited agents in real-time.

---

## 🚀 Key Features

- **🧠 Heuristic Classification:** Automatically routes tickets into *Billing*, *Technical*, or *Legal* categories using optimized regex patterns.
- **⚡ Async Broker:** Uses Redis to handle high-volume ticket traffic without blocking the API. (Requires Redis server for full functionality)
- **🎯 Skill-Based Routing:** Assigns tickets based on agent expertise and current capacity.
- **🛡️ Circuit Breaker:** Protects system performance with automatic fallback logic.
- **📈 Dynamic Urgency:** Calculates priority scores (0-1) based on sentiment and urgency keywords.

---

## 🛠️ Tech Stack

- **Backend:** FastAPI (Python)
- **Frontend:** React (Vite, Tailwind CSS)
- **Messaging:** Redis
- **Tooling:** Uvicorn, Pydantic, NPM/Node.js

---

## 📋 Quick Start

### 1. Backend Setup
```bash
pip install -r requirements.txt
python app.py
```
*API will be available at `http://localhost:8001`*

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Frontend will be available at `http://localhost:5173`*

---

## 📂 Project Structure

- `frontend/`: React-based dashboard for ticket monitoring and management.
- `ml/`: Heuristic classification logic and verification scripts.
- `broker/`: Redis async message publisher.
- `routing/`: Skill-based assignment and system resilience logic.
- `app.py`: Main FastAPI entry point.
- `config.py`: System configuration.

---

## 📊 Performance
The heuristic regex classifier is verified on common support scenarios. You can improve performance by adding more keywords to `CATEGORY_PATTERNS` in `ml/classifier.py`.

---

*Built for high-scale support orchestration.*
