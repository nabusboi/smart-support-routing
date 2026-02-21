"""
Webhook notifications for high urgency tickets (Milestone 2)
Sends alerts to Slack and Discord when urgency score S > 0.8
"""
import os
import json
import asyncio
from typing import Dict, Any, Optional
import httpx

from config import settings


class WebhookNotifier:
    """
    Sends webhook notifications to Slack and Discord for high urgency tickets.
    """
    
    def __init__(self):
        self.slack_url = settings.SLACK_WEBHOOK_URL
        self.discord_url = settings.DISCORD_WEBHOOK_URL
    
    async def send_alert(self, ticket: Dict[str, Any]) -> bool:
        """
        Send alert notification for high urgency ticket.
        
        Args:
            ticket: Ticket information dictionary
            
        Returns:
            True if at least one notification was sent successfully
        """
        urgency = ticket.get("urgency", 0)
        
        # Only send alerts for high urgency tickets (S > 0.8)
        if urgency <= 0.8:
            return False
        
        sent = False
        
        # Send to Slack
        if self.slack_url:
            if await self._send_slack(ticket):
                sent = True
        
        # Send to Discord
        if self.discord_url:
            if await self._send_discord(ticket):
                sent = True
        
        return sent
    
    async def _send_slack(self, ticket: Dict[str, Any]) -> bool:
        """
        Send notification to Slack.
        
        Args:
            ticket: Ticket information
            
        Returns:
            True if successful
        """
        if not self.slack_url:
            return False
        
        # Determine severity emoji
        urgency = ticket.get("urgency", 0)
        if urgency >= 0.95:
            emoji = "🔥"  # Critical
        elif urgency >= 0.9:
            emoji = "🚨"  # Emergency
        else:
            emoji = "⚠️"  # Warning
        
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} High Urgency Ticket Alert"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Ticket ID:*\n{ticket.get('ticket_id', 'N/A')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Urgency Score:*\n{ticket.get('urgency', 0):.2f}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Category:*\n" + ticket.get("category", "General")
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Customer:*\n" + ticket.get("customer_id", "Unknown")
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Subject:*\n{ticket.get('subject', 'No subject')}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Description:*\n{ticket.get('description', 'No description')[:500]}"
                    }
                }
            ]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.slack_url,
                    json=payload,
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Slack webhook error: {e}")
            return False
    
    async def _send_discord(self, ticket: Dict[str, Any]) -> bool:
        """
        Send notification to Discord.
        
        Args:
            ticket: Ticket information
            
        Returns:
            True if successful
        """
        if not self.discord_url:
            return False
        
        urgency = ticket.get("urgency", 0)
        
        # Determine color based on urgency (red for high)
        # Discord colors: 0xff0000 = red
        color = 0xFF0000 if urgency >= 0.9 else 0xFFA500  # Red or Orange
        
        # Determine severity label
        if urgency >= 0.95:
            severity = "CRITICAL"
        elif urgency >= 0.9:
            severity = "HIGH"
        else:
            severity = "MEDIUM"
        
        payload = {
            "embeds": [
                {
                    "title": f"🚨 High Urgency Ticket - {severity}",
                    "color": color,
                    "fields": [
                        {
                            "name": "Ticket ID",
                            "value": ticket.get("ticket_id", "N/A"),
                            "inline": True
                        },
                        {
                            "name": "Urgency Score",
                            "value": f"{ticket.get('urgency', 0):.2f}",
                            "inline": True
                        },
                        {
                            "name": "Category",
                            "value": ticket.get("category", "General"),
                            "inline": True
                        },
                        {
                            "name": "Customer ID",
                            "value": ticket.get("customer_id", "Unknown"),
                            "inline": True
                        },
                        {
                            "name": "Subject",
                            "value": ticket.get("subject", "No subject"),
                            "inline": False
                        },
                        {
                            "name": "Description",
                            "value": ticket.get("description", "No description")[:1000],
                            "inline": False
                        }
                    ],
                    "footer": {
                        "text": "Smart-Support Ticket Routing Engine"
                    }
                }
            ]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.discord_url,
                    json=payload,
                    timeout=10.0
                )
                return response.status_code == 204 or response.status_code == 200
        except Exception as e:
            print(f"Discord webhook error: {e}")
            return False


# Singleton instance
webhook_notifier = WebhookNotifier()
