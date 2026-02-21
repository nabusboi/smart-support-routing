"""
Background Worker for Ticket Processing (Milestone 3)
Integrates ML routing, circuit breakers, deduplication, and skill-based routing
"""
import asyncio
from datetime import datetime
from broker.async_broker import async_broker
from ml.router import ml_router
from routing.skill_routing import agent_registry, TicketRequest
from webhooks.notifications import webhook_notifier
from config import settings

print("🚀 Worker started with Milestone 3 features...")


async def process_ticket(ticket_data: dict) -> dict:
    """
    Process a single ticket through the ML pipeline.
    """
    ticket_id = ticket_data.get("ticket_id", "UNKNOWN")
    subject = ticket_data.get("subject", "")
    description = ticket_data.get("description", "")
    customer_id = ticket_data.get("metadata", {}).get("customer_id", "unknown")
    
    print(f"Processing ticket: {ticket_id}")
    
    # Step 1: ML Classification with circuit breaker and deduplication
    result = ml_router.classify(
        ticket_id=ticket_id,
        subject=subject,
        description=description,
        enable_dedup=True
    )
    
    # Build enriched ticket data
    enriched_ticket = {
        "ticket_id": ticket_id,
        "subject": subject,
        "description": description,
        "category": result.category,
        "urgency": result.urgency,
        "sentiment_score": result.sentiment_score,
        "customer_id": customer_id,
        "model_used": result.model_used,
        "processing_time_ms": result.processing_time_ms,
        "is_master_incident": result.is_master_incident,
        "master_incident_id": result.master_incident_id,
        "metadata": ticket_data.get("metadata", {}),
        "created_at": ticket_data.get("created_at", datetime.now().isoformat())
    }
    
    # Step 2: Handle Master Incident (suppress individual alerts)
    if result.is_master_incident and result.master_incident_id:
        print(f"🎯 Ticket {ticket_id} linked to Master Incident {result.master_incident_id}")
        webhook_sent = False
    else:
        # Step 3: Send webhook for high urgency tickets (S > 0.8)
        if result.urgency > settings.HIGH_URGENCY_THRESHOLD:
            webhook_sent = await webhook_notifier.send_alert(enriched_ticket)
            if webhook_sent:
                print(f"📢 Webhook sent for high urgency ticket: {ticket_id}")
        else:
            webhook_sent = False
    
    # Step 4: Skill-based routing
    ticket_request = TicketRequest(
        ticket_id=ticket_id,
        category=result.category,
        urgency=result.urgency,
        description=description,
        required_skills=[result.category.lower()]
    )
    
    agent_id = agent_registry.route_ticket(ticket_request)
    
    if agent_id:
        agent = agent_registry.get_agent(agent_id)
        print(f"📌 Ticket {ticket_id} routed to agent: {agent.name if agent else 'Unknown'}")
    else:
        print(f"⚠️ No available agent for ticket: {ticket_id}")
    
    return {
        "ticket_id": ticket_id,
        "status": "processed",
        "category": result.category,
        "urgency": result.urgency,
        "model_used": result.model_used,
        "is_master_incident": result.is_master_incident,
        "master_incident_id": result.master_incident_id,
        "webhook_sent": webhook_sent,
        "agent_id": agent_id,
        "processed_at": datetime.now().isoformat()
    }


async def main():
    """Main worker loop"""
    print("Initializing ML components...")
    
    # Register sample agents for skill-based routing
    sample_agents = [
        {"name": "Alice", "skills": {"billing": 0.9, "technical": 0.3, "legal": 0.1}},
        {"name": "Bob", "skills": {"technical": 0.95, "billing": 0.2, "legal": 0.1}},
        {"name": "Charlie", "skills": {"legal": 0.9, "billing": 0.3, "technical": 0.1}},
        {"name": "Diana", "skills": {"technical": 0.7, "billing": 0.8, "legal": 0.2}},
    ]
    
    for agent in sample_agents:
        agent_id = agent_registry.register_agent(
            name=agent["name"],
            skills=agent["skills"],
            capacity=3
        )
        print(f"Registered agent: {agent['name']} ({agent_id[:8]}...)")
    
    print("\nWorker ready! Waiting for tickets...\n")
    
    while True:
        try:
            # Consume ticket from Redis queue (blocking with timeout)
            # Note: consume_ticket is synchronous (not async), so no await
            ticket = async_broker.consume_ticket(timeout=5)
            
            if not ticket:
                continue
            
            # Convert dataclass to dict
            ticket_data = {
                "ticket_id": ticket.ticket_id,
                "subject": ticket.subject,
                "description": ticket.description,
                "category": ticket.category,
                "urgency": ticket.urgency,
                "sentiment_score": ticket.sentiment_score,
                "metadata": ticket.metadata,
                "created_at": ticket.created_at
            }
            
            # Process the ticket (async function)
            result = await process_ticket(ticket_data)
            
            # Mark as completed in broker (synchronous)
            async_broker.complete_ticket(ticket.ticket_id)
            
            print(f"✅ Completed: {ticket.ticket_id} | Category: {result['category']} | "
                  f"Urgency: {result['urgency']:.2f} | Model: {result['model_used']}")
            
            # Print stats periodically
            if async_broker.get_queue_size() == 0:
                dedup_stats = ml_router.get_deduplication_stats()
                circuit_status = ml_router.get_circuit_breaker_status()
                agent_stats = agent_registry.get_stats()
                
                print(f"\n📊 Stats:")
                print(f"   Deduplication: {dedup_stats}")
                print(f"   Circuit Breaker: {circuit_status}")
                print(f"   Agents: {agent_stats}")
                print()
            
        except Exception as e:
            print(f"❌ Worker error: {e}")
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
