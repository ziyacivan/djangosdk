import random
from djangosdk.agents import Agent
from djangosdk.agents.mixins import HasTools
from djangosdk.tools import tool

# Mock order database — replace with real ORM queries in production
ORDERS = {
    "ORD-001": {"status": "shipped", "item": "Django T-Shirt", "estimated_delivery": "2026-04-02"},
    "ORD-002": {"status": "processing", "item": "Python Mug", "estimated_delivery": "2026-04-05"},
    "ORD-003": {"status": "delivered", "item": "AI Book", "estimated_delivery": "2026-03-28"},
}


class SupportAgent(Agent, HasTools):
    provider = "anthropic"
    model = "claude-3-5-haiku-20241022"
    system_prompt = (
        "You are a friendly customer support agent for an online store. "
        "Use your tools to look up order information before answering. "
        "Always be helpful and empathetic."
    )
    temperature = 0.3

    @tool
    def lookup_order(self, order_id: str) -> dict:
        """Retrieves order details by order ID (e.g. ORD-001)."""
        order = ORDERS.get(order_id.upper())
        if not order:
            return {"error": f"Order {order_id} not found."}
        return {"order_id": order_id, **order}

    @tool
    def get_weather(self, city: str) -> dict:
        """Gets current weather for a city (used for delivery delay estimates)."""
        # Mock weather — replace with real weather API
        conditions = ["sunny", "cloudy", "rainy", "stormy"]
        return {
            "city": city,
            "condition": random.choice(conditions),
            "temperature_c": random.randint(5, 30),
        }

    @tool
    def cancel_order(self, order_id: str, reason: str) -> dict:
        """Cancels an order that hasn't been shipped yet."""
        order = ORDERS.get(order_id.upper())
        if not order:
            return {"error": f"Order {order_id} not found."}
        if order["status"] == "shipped":
            return {"error": "Cannot cancel a shipped order. Please use the return process."}
        if order["status"] == "delivered":
            return {"error": "Order already delivered. Please initiate a return."}
        # In production: order.status = "cancelled"; order.save()
        ORDERS[order_id.upper()]["status"] = "cancelled"
        return {"success": True, "order_id": order_id, "reason": reason}
