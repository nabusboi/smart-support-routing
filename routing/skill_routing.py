"""
Skill-Based Agent Routing (Milestone 3)
Implements constraint optimization for routing tickets to best available agents
"""
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import numpy as np


class AgentStatus(Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


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
    
    def can_accept_ticket(self) -> bool:
        """Check if agent can accept more tickets"""
        return self.status == AgentStatus.AVAILABLE and self.current_load < self.capacity
    
    def accept_ticket(self) -> bool:
        """Accept a ticket, returns True if successful"""
        if self.can_accept_ticket():
            self.current_load += 1
            return True
        return False
    
    def release_ticket(self) -> bool:
        """Release a ticket, returns True if successful"""
        if self.current_load > 0:
            self.current_load -= 1
            return True
        return False


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
    Implements skill-based routing using constraint optimization.
    """
    
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._lock = threading.RLock()
        self._assignment_history: List[Dict] = []
    
    def register_agent(
        self,
        name: str,
        skills: Dict[str, float],
        capacity: int = 5
    ) -> str:
        """
        Register a new agent.
        
        Args:
            name: Agent name
            skills: Dictionary of skill name to proficiency (0-1)
            capacity: Maximum concurrent tickets
            
        Returns:
            Agent ID
        """
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
        """
        Update agent status.
        
        Args:
            agent_id: Agent ID
            status: New status
            
        Returns:
            True if updated, False if agent not found
        """
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
    
    def route_ticket(self, ticket: TicketRequest) -> Optional[str]:
        """
        Route ticket to best available agent using constraint optimization.
        
        Solves: maximize skill match while minimizing current load
        
        Args:
            ticket: Ticket request to route
            
        Returns:
            Agent ID if routed successfully, None otherwise
        """
        available_agents = self.get_available_agents()
        
        if not available_agents:
            return None
        
        # Calculate scores for each agent
        best_agent = None
        best_score = -float('inf')
        
        for agent in available_agents:
            score = self._calculate_agent_score(agent, ticket)
            if score > best_score:
                best_score = score
                best_agent = agent
        
        if best_agent:
            best_agent.accept_ticket()
            self._assignment_history.append({
                "ticket_id": ticket.ticket_id,
                "agent_id": best_agent.agent_id,
                "score": best_score,
                "timestamp": datetime.now().isoformat()
            })
            return best_agent.agent_id
        
        return None
    
    def _calculate_agent_score(self, agent: Agent, ticket: TicketRequest) -> float:
        """
        Calculate agent suitability score for a ticket.
        
        Score = skill_match * urgency_weight + availability_factor
        
        Args:
            agent: The agent
            ticket: The ticket request
            
        Returns:
            Score (higher is better)
        """
        # Skill match score
        skill_score = 0.0
        if ticket.required_skills:
            for skill in ticket.required_skills:
                skill_score += agent.skills.get(skill, 0.0)
            skill_score /= len(ticket.required_skills)
        else:
            # Use category as default skill
            skill_score = agent.skills.get(ticket.category.lower(), 0.5)
        
        # Availability factor (prefer less loaded agents)
        load_factor = 1.0 - (agent.current_load / agent.capacity)
        
        # Urgency weight (higher urgency = more important skill match)
        urgency_weight = 0.7 + (0.3 * ticket.urgency)
        
        # Final score
        score = (skill_score * urgency_weight) + (load_factor * (1 - urgency_weight))
        
        return score
    
    def release_ticket(self, agent_id: str) -> bool:
        """
        Release a ticket from an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if released, False if agent not found
        """
        with self._lock:
            if agent_id in self._agents:
                return self._agents[agent_id].release_ticket()
        return False
    
    def get_stats(self) -> Dict:
        """Get routing statistics"""
        with self._lock:
            total_agents = len(self._agents)
            available = sum(1 for a in self._agents.values() if a.can_accept_ticket())
            total_load = sum(a.current_load for a in self._agents.values())
            total_capacity = sum(a.capacity for a in self._agents.values())
            
            return {
                "total_agents": total_agents,
                "available_agents": available,
                "total_current_load": total_load,
                "total_capacity": total_capacity,
                "utilization": total_load / total_capacity if total_capacity > 0 else 0,
                "total_assignments": len(self._assignment_history)
            }


# Global agent registry
agent_registry = AgentRegistry()
