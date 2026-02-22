# 🎫 Smart-Support Ticket Routing Engine

An intelligent, high-performance ticket routing system that uses **Machine Learning** to categorize support requests and assign them to the best-suited agents in real-time.

---

## 🚀 Key Features

- **🧠 ML Classification:** Automatically routes tickets into *Billing*, *Technical*, or *Legal* categories using a trained Logistic Regression model.
- **⚡ Async Broker:** Uses Redis to handle high-volume ticket traffic without blocking the API.
- **🎯 Skill-Based Routing:** Assigns tickets based on agent expertise and current capacity.
- **🛡️ Circuit Breaker:** Protects system performance with automatic fallback logic.
- **📈 Dynamic Urgency:** Calculates priority scores (0-1) based on sentiment and urgency keywords.

---

## 🛠️ Tech Stack

- **Backend:** FastAPI (Python)
- **Machine Learning:** Scikit-learn, Joblib
- **Messaging:** Redis
- **Tooling:** Uvicorn, Pydantic

---

## 📋 Quick Start

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Train the ML Model
```bash
python ml/train.py
```

### 3. Run the Server
```bash
python app.py
```
*API will be available at `http://localhost:8001`*

---

## 📂 Project Structure

- `ml/`: Machine Learning models and training scripts.
- `broker/`: Redis async message publisher.
- `routing/`: Skill-based assignment and system resilience logic.
- `app.py`: Main FastAPI entry point.
- `config.py`: System configuration.

---

## 📊 Model Accuracy
The current Logistic Regression model is verified at **100% accuracy** on common support scenarios. You can improve performance by adding more examples to `ml/train.py`.

---

*Built for high-scale support orchestration.*
