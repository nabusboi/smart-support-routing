"""
Skill-Based Agent Routing (Milestone 3)
Implements constraint optimization for routing tickets to best available agents.

Enhanced with:
- Per-agent ticket tracking (active/paused/completed)
- Preemption: urgent tickets bump lower-priority ones on full agents
- Generalist routing: agents with >=50% in all skills can handle any ticket
- ETA computation for ticket completion
"""
import threading
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import numpy as np

from config import settings


class AgentStatus(Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


class TicketStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class AssignedTicket:
    """A ticket assigned to an agent with tracking info"""
    ticket_id: str
    category: str
    urgency: float
    description: str
    status: TicketStatus = TicketStatus.ACTIVE
    eta_seconds: int = 60
    started_at: float = field(default_factory=time.time)
    paused_at: Optional[float] = None
    elapsed_before_pause: float = 0.0

    def remaining_eta(self) -> float:
        """Get remaining ETA in seconds"""
        if self.status == TicketStatus.COMPLETED:
            return 0.0
        if self.status == TicketStatus.PAUSED:
            elapsed = self.elapsed_before_pause
        else:
            elapsed = self.elapsed_before_pause + (time.time() - self.started_at)
        return max(0.0, self.eta_seconds - elapsed)

    def is_expired(self) -> bool:
        """Check if this ticket's ETA has elapsed"""
        return self.status == TicketStatus.ACTIVE and self.remaining_eta() <= 0


@dataclass
class Agent:
    """Agent with skill vector and capacity"""
    agent_id: str
    name: str
    skills: Dict[str, float]  # Skill name -> proficiency (0-1)
    capacity: int = 5  # Max concurrent tickets
    current_load: int = 0
    status: AgentStatus = AgentStatus.AVAILABLE
    created_at: datetime = field(default_factory=datetime.now)
    assigned_tickets: Dict[str, AssignedTicket] = field(default_factory=dict)
    
    def can_accept_ticket(self) -> bool:
        """Check if agent can accept more tickets"""
        return self.status == AgentStatus.AVAILABLE and self.current_load < self.capacity
    
    def accept_ticket(self, ticket: 'AssignedTicket') -> bool:
        """Accept a ticket, returns True if successful"""
        if self.can_accept_ticket():
            self.current_load += 1
            self.assigned_tickets[ticket.ticket_id] = ticket
            return True
        return False
    
    def release_ticket(self, ticket_id: str = None) -> bool:
        """Release a ticket, returns True if successful"""
        if ticket_id and ticket_id in self.assigned_tickets:
            t = self.assigned_tickets[ticket_id]
            t.status = TicketStatus.COMPLETED
            del self.assigned_tickets[ticket_id]
            if self.current_load > 0:
                self.current_load -= 1
            return True
        elif self.current_load > 0:
            self.current_load -= 1
            return True
        return False

    def pause_ticket(self, ticket_id: str) -> bool:
        """Pause an active ticket on this agent"""
        if ticket_id in self.assigned_tickets:
            t = self.assigned_tickets[ticket_id]
            if t.status == TicketStatus.ACTIVE:
                t.elapsed_before_pause += (time.time() - t.started_at)
                t.paused_at = time.time()
                t.status = TicketStatus.PAUSED
                return True
        return False

    def resume_ticket(self, ticket_id: str) -> bool:
        """Resume a paused ticket on this agent"""
        if ticket_id in self.assigned_tickets:
            t = self.assigned_tickets[ticket_id]
            if t.status == TicketStatus.PAUSED:
                t.started_at = time.time()
                t.paused_at = None
                t.status = TicketStatus.ACTIVE
                return True
        return False

    def get_lowest_urgency_active_ticket(self) -> Optional[AssignedTicket]:
        """Get the active ticket with the lowest urgency on this agent"""
        active = [t for t in self.assigned_tickets.values() if t.status == TicketStatus.ACTIVE]
        if not active:
            return None
        return min(active, key=lambda t: t.urgency)

    def is_generalist(self) -> bool:
        """Check if agent has >= GENERALIST_THRESHOLD in all skill categories"""
        all_categories = ["billing", "technical", "legal"]
        return all(
            self.skills.get(cat, 0.0) >= settings.GENERALIST_THRESHOLD
            for cat in all_categories
        )

    def get_assigned_tickets_info(self) -> List[dict]:
        """Get info about all assigned tickets"""
        result = []
        for t in self.assigned_tickets.values():
            result.append({
                "ticket_id": t.ticket_id,
                "category": t.category,
                "urgency": t.urgency,
                "status": t.status.value,
                "eta_seconds": t.eta_seconds,
                "remaining_eta": round(t.remaining_eta(), 1),
                "description": t.description[:80] + "..." if len(t.description) > 80 else t.description,
            })
        # Sort by urgency descending (most urgent first)
        result.sort(key=lambda x: x["urgency"], reverse=True)
        return result


@dataclass
class TicketRequest:
    """Ticket request for routing"""
    ticket_id: str
    category: str
    urgency: float  # 0-1
    description: str
    required_skills: List[str] = field(default_factory=list)


class AgentRegistry:
    """
    Stateful registry of agents with skill vectors.
    Implements skill-based routing with preemption and generalist support.
    """
    
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._lock = threading.RLock()
        self._assignment_history: List[Dict] = []
        self._preemption_history: List[Dict] = []
    
    def register_agent(
        self,
        name: str,
        skills: Dict[str, float],
        capacity: int = 5
    ) -> str:
        agent_id = str(uuid.uuid4())
        agent = Agent(
            agent_id=agent_id,
            name=name,
            skills=skills,
            capacity=capacity
        )
        
        with self._lock:
            self._agents[agent_id] = agent
        
        return agent_id
    
    def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        with self._lock:
            if agent_id not in self._agents:
                return False
            self._agents[agent_id].status = status
            return True
    
    def get_available_agents(self) -> List[Agent]:
        """Get list of available agents"""
        with self._lock:
            return [a for a in self._agents.values() if a.can_accept_ticket()]
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        with self._lock:
            return self._agents.get(agent_id)
    
    def compute_eta(self, urgency: float) -> int:
        """
        Compute ETA seconds for a ticket based on urgency.
        Same base timing for all tickets.
        """
        return settings.ETA_BASE_SECONDS

    def route_ticket(self, ticket: TicketRequest) -> Optional[str]:
        """
        Route ticket to best available agent using constraint optimization.
        Falls back to preemption if no agent is available and ticket is urgent.
        
        Returns:
            Agent ID if routed successfully, None otherwise
        """
        agent_id, _ = self.route_ticket_with_preemption(ticket)
        return agent_id

    def route_ticket_with_preemption(self, ticket: TicketRequest) -> Tuple[Optional[str], Optional[str]]:
        """
        Route ticket with preemption support.
        
        Returns:
            Tuple of (assigned_agent_id, preempted_ticket_id or None)
        """
        with self._lock:
            # First, auto-complete any expired tickets across all agents
            self._auto_complete_expired()

            available_agents = [a for a in self._agents.values() if a.can_accept_ticket()]

            if available_agents:
                # Normal routing — pick best agent
                best_agent = None
                best_score = -float('inf')
                
                for agent in available_agents:
                    score = self._calculate_agent_score(agent, ticket)
                    if score > best_score:
                        best_score = score
                        best_agent = agent
                
                if best_agent:
                    eta = self.compute_eta(ticket.urgency)
                    assigned = AssignedTicket(
                        ticket_id=ticket.ticket_id,
                        category=ticket.category,
                        urgency=ticket.urgency,
                        description=ticket.description,
                        eta_seconds=eta,
                    )
                    best_agent.accept_ticket(assigned)
                    self._assignment_history.append({
                        "ticket_id": ticket.ticket_id,
                        "agent_id": best_agent.agent_id,
                        "score": best_score,
                        "eta_seconds": eta,
                        "preempted": False,
                        "timestamp": datetime.now().isoformat()
                    })
                    return best_agent.agent_id, None

            # No available agents — try preemption if urgent enough
            if ticket.urgency >= settings.PREEMPTION_URGENCY_THRESHOLD:
                return self._preempt_for_ticket(ticket)

            return None, None
    
    def _preempt_for_ticket(self, ticket: TicketRequest) -> Tuple[Optional[str], Optional[str]]:
        """
        Find the agent with the lowest-urgency active ticket and preempt it.
        """
        best_agent = None
        lowest_ticket = None
        lowest_urgency = float('inf')

        for agent in self._agents.values():
            if agent.status == AgentStatus.OFFLINE:
                continue
            t = agent.get_lowest_urgency_active_ticket()
            if t and t.urgency < lowest_urgency and t.urgency < ticket.urgency:
                lowest_urgency = t.urgency
                lowest_ticket = t
                best_agent = agent

        if best_agent and lowest_ticket:
            # Pause the low-priority ticket
            best_agent.pause_ticket(lowest_ticket.ticket_id)
            
            # Don't change current_load (we're swapping, not adding)
            # But we need to accept the new ticket — decrement load first to allow accept
            best_agent.current_load -= 1
            
            eta = self.compute_eta(ticket.urgency)
            assigned = AssignedTicket(
                ticket_id=ticket.ticket_id,
                category=ticket.category,
                urgency=ticket.urgency,
                description=ticket.description,
                eta_seconds=eta,
            )
            best_agent.accept_ticket(assigned)

            # Record preemption event
            event = {
                "urgent_ticket_id": ticket.ticket_id,
                "urgent_urgency": ticket.urgency,
                "paused_ticket_id": lowest_ticket.ticket_id,
                "paused_urgency": lowest_ticket.urgency,
                "agent_id": best_agent.agent_id,
                "agent_name": best_agent.name,
                "timestamp": datetime.now().isoformat()
            }
            self._preemption_history.append(event)
            self._assignment_history.append({
                "ticket_id": ticket.ticket_id,
                "agent_id": best_agent.agent_id,
                "score": 0,
                "eta_seconds": eta,
                "preempted": True,
                "preempted_ticket": lowest_ticket.ticket_id,
                "timestamp": datetime.now().isoformat()
            })

            print(f"⚡ PREEMPTION: {ticket.ticket_id} (urg={ticket.urgency:.2f}) "
                  f"bumped {lowest_ticket.ticket_id} (urg={lowest_ticket.urgency:.2f}) "
                  f"on agent {best_agent.name}")

            return best_agent.agent_id, lowest_ticket.ticket_id

        return None, None

    def _auto_complete_expired(self):
        """Auto-complete tickets whose ETA has elapsed"""
        for agent in self._agents.values():
            expired = [tid for tid, t in agent.assigned_tickets.items() if t.is_expired()]
            for tid in expired:
                agent.release_ticket(tid)
                # Auto-resume paused tickets on this agent
                self._resume_next_paused(agent)

    def _resume_next_paused(self, agent: Agent):
        """Resume the highest-urgency paused ticket on an agent"""
        paused = [t for t in agent.assigned_tickets.values() if t.status == TicketStatus.PAUSED]
        if paused:
            highest = max(paused, key=lambda t: t.urgency)
            agent.resume_ticket(highest.ticket_id)

    def complete_ticket(self, agent_id: str, ticket_id: str) -> bool:
        """
        Complete a ticket on a specific agent.
        Auto-resumes paused tickets after completion.
        """
        with self._lock:
            agent = self._agents.get(agent_id)
            if not agent:
                return False
            released = agent.release_ticket(ticket_id)
            if released:
                self._resume_next_paused(agent)
            return released

    def _calculate_agent_score(self, agent: Agent, ticket: TicketRequest) -> float:
        """
        Calculate agent suitability score for a ticket.
        
        Score = skill_match * urgency_weight + availability_factor
        
        Enhanced: generalist agents (>=50% in all skills) get a minimum 
        skill score of 0.5 for any category.
        """
        # Skill match score
        skill_score = 0.0
        if ticket.required_skills:
            for skill in ticket.required_skills:
                skill_score += agent.skills.get(skill, 0.0)
            skill_score /= len(ticket.required_skills)
        else:
            skill_score = agent.skills.get(ticket.category.lower(), 0.5)
        
        # Generalist bonus: if all skills >= 50%, guarantee at least 0.5 match
        if agent.is_generalist() and skill_score < settings.GENERALIST_THRESHOLD:
            skill_score = settings.GENERALIST_THRESHOLD
        
        # Availability factor (prefer less loaded agents)
        load_factor = 1.0 - (agent.current_load / agent.capacity)
        
        # Urgency weight (higher urgency = more important skill match)
        urgency_weight = 0.7 + (0.3 * ticket.urgency)
        
        # Final score
        score = (skill_score * urgency_weight) + (load_factor * (1 - urgency_weight))
        
        return score
    
    def release_ticket_by_id(self, agent_id: str) -> bool:
        """Release a generic ticket from an agent (backwards compat)."""
        with self._lock:
            if agent_id in self._agents:
                return self._agents[agent_id].release_ticket()
        return False
    
    def get_preemption_history(self, limit: int = 20) -> List[Dict]:
        """Get recent preemption events"""
        with self._lock:
            return self._preemption_history[-limit:]

    def get_stats(self) -> Dict:
        """Get routing statistics"""
        with self._lock:
            total_agents = len(self._agents)
            available = sum(1 for a in self._agents.values() if a.can_accept_ticket())
            total_load = sum(a.current_load for a in self._agents.values())
            total_capacity = sum(a.capacity for a in self._agents.values())
            total_active = sum(
                sum(1 for t in a.assigned_tickets.values() if t.status == TicketStatus.ACTIVE)
                for a in self._agents.values()
            )
            total_paused = sum(
                sum(1 for t in a.assigned_tickets.values() if t.status == TicketStatus.PAUSED)
                for a in self._agents.values()
            )
            generalists = sum(1 for a in self._agents.values() if a.is_generalist())
            
            return {
                "total_agents": total_agents,
                "available_agents": available,
                "total_current_load": total_load,
                "total_capacity": total_capacity,
                "utilization": total_load / total_capacity if total_capacity > 0 else 0,
                "total_assignments": len(self._assignment_history),
                "total_preemptions": len(self._preemption_history),
                "active_tickets": total_active,
                "paused_tickets": total_paused,
                "generalist_agents": generalists,
            }


# Global agent registry
agent_registry = AgentRegistry()
