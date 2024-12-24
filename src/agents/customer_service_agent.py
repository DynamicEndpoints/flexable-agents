import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
from anthropic import Anthropic

from ..core.base import Agent, Task, TaskResult, Message

logger = logging.getLogger(__name__)

class CustomerServiceAgent(Agent):
    """Agent for handling customer service inquiries using Claude's tool-calling capabilities"""
    
    def __init__(
        self,
        agent_id: str,
        work_dir: str,
        api_keys: Dict[str, str],
        db_config: Dict[str, Any] = None
    ):
        super().__init__(
            agent_id=agent_id,
            capabilities=[
                "customer_info",
                "order_management",
                "product_info",
                "issue_tracking",
                "feedback_collection",
                "returns_processing",
                "shipping_status",
                "payment_info"
            ]
        )
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Claude client
        self.anthropic = Anthropic(api_key=api_keys.get("anthropic"))
        
        # Initialize database connection if provided
        self.db_config = db_config
        
        # Define available tools
        self.tools = [
            {
                "name": "get_customer_info",
                "description": "Retrieves customer information based on their customer ID.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "The unique identifier for the customer."
                        }
                    },
                    "required": ["customer_id"]
                }
            },
            {
                "name": "get_order_details",
                "description": "Retrieves the details of a specific order.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The unique identifier for the order."
                        }
                    },
                    "required": ["order_id"]
                }
            },
            {
                "name": "cancel_order",
                "description": "Cancels an order based on the order ID.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The unique identifier for the order to cancel."
                        }
                    },
                    "required": ["order_id"]
                }
            },
            {
                "name": "track_shipment",
                "description": "Tracks a shipment based on tracking number.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tracking_number": {
                            "type": "string",
                            "description": "The shipment tracking number."
                        }
                    },
                    "required": ["tracking_number"]
                }
            },
            {
                "name": "process_return",
                "description": "Initiates a return for an order.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The order ID for the return."
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for the return."
                        }
                    },
                    "required": ["order_id", "reason"]
                }
            },
            {
                "name": "get_product_info",
                "description": "Retrieves product information.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "The unique identifier for the product."
                        }
                    },
                    "required": ["product_id"]
                }
            },
            {
                "name": "create_support_ticket",
                "description": "Creates a new support ticket.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "The customer ID."
                        },
                        "issue_type": {
                            "type": "string",
                            "description": "Type of issue."
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the issue."
                        }
                    },
                    "required": ["customer_id", "issue_type", "description"]
                }
            },
            {
                "name": "get_payment_info",
                "description": "Retrieves payment information for an order.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The order ID."
                        }
                    },
                    "required": ["order_id"]
                }
            }
        ]
        
        # Initialize synthetic data
        self._init_synthetic_data()
    
    def _init_synthetic_data(self):
        """Initialize synthetic data for demonstration"""
        self.customers = {
            "C1": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "123-456-7890",
                "address": "123 Main St, City, State 12345"
            },
            "C2": {
                "name": "Jane Smith",
                "email": "jane@example.com",
                "phone": "987-654-3210",
                "address": "456 Oak Ave, Town, State 67890"
            }
        }
        
        self.orders = {
            "O1": {
                "id": "O1",
                "customer_id": "C1",
                "product": "Laptop Pro",
                "quantity": 1,
                "price": 1299.99,
                "status": "Shipped",
                "tracking": "TRK123456"
            },
            "O2": {
                "id": "O2",
                "customer_id": "C2",
                "product": "Wireless Headphones",
                "quantity": 2,
                "price": 199.99,
                "status": "Processing",
                "tracking": None
            }
        }
        
        self.products = {
            "P1": {
                "id": "P1",
                "name": "Laptop Pro",
                "description": "High-performance laptop",
                "price": 1299.99,
                "stock": 50
            },
            "P2": {
                "id": "P2",
                "name": "Wireless Headphones",
                "description": "Premium wireless headphones",
                "price": 199.99,
                "stock": 100
            }
        }
        
        self.support_tickets = {}
        self.returns = {}
    
    async def process_task(self, task: Task) -> TaskResult:
        """Process customer service tasks"""
        try:
            if task.task_type == "customer_inquiry":
                output = await self._handle_customer_inquiry(task.input_data, task.parameters)
            else:
                output = await self._process_tool_call(task.task_type, task.input_data)
            
            return TaskResult(
                task_id=task.task_id,
                status="success",
                output=output,
                agent_id=self.agent_id
            )
        except Exception as e:
            logger.error(f"Error processing task {task.task_id}: {str(e)}")
            return TaskResult(
                task_id=task.task_id,
                status="failed",
                error=str(e),
                agent_id=self.agent_id
            )
    
    async def _handle_customer_inquiry(self, inquiry: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer inquiry using Claude"""
        messages = [{"role": "user", "content": inquiry}]
        
        response = await self.anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4096,
            tools=self.tools,
            messages=messages
        )
        
        # Process tool calls if needed
        while response.stop_reason == "tool_use":
            tool_use = next(block for block in response.content if block.type == "tool_use")
            tool_name = tool_use.name
            tool_input = tool_use.input
            
            # Process tool call
            tool_result = await self._process_tool_call(tool_name, tool_input)
            
            # Add tool result to messages
            messages.extend([
                {"role": "assistant", "content": response.content},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": str(tool_result)
                        }
                    ]
                }
            ])
            
            # Get next response
            response = await self.anthropic.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4096,
                tools=self.tools,
                messages=messages
            )
        
        final_response = next(
            (block.text for block in response.content if hasattr(block, "text")),
            None
        )
        
        return {
            "response": final_response,
            "tools_used": [msg["content"][0]["tool_use_id"] for msg in messages if isinstance(msg.get("content"), list)],
            "timestamp": datetime.now().isoformat()
        }
    
    async def _process_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """Process tool calls"""
        if tool_name == "get_customer_info":
            return self.customers.get(tool_input["customer_id"], "Customer not found")
        
        elif tool_name == "get_order_details":
            return self.orders.get(tool_input["order_id"], "Order not found")
        
        elif tool_name == "cancel_order":
            order = self.orders.get(tool_input["order_id"])
            if order and order["status"] != "Shipped":
                order["status"] = "Cancelled"
                return {"success": True, "message": "Order cancelled successfully"}
            return {"success": False, "message": "Order cannot be cancelled"}
        
        elif tool_name == "track_shipment":
            tracking = tool_input["tracking_number"]
            order = next((o for o in self.orders.values() if o.get("tracking") == tracking), None)
            if order:
                return {
                    "status": order["status"],
                    "estimated_delivery": "2024-01-01",  # Simulated
                    "current_location": "Distribution Center"  # Simulated
                }
            return "Tracking number not found"
        
        elif tool_name == "process_return":
            order = self.orders.get(tool_input["order_id"])
            if order and order["status"] == "Shipped":
                return_id = f"R{len(self.returns) + 1}"
                self.returns[return_id] = {
                    "id": return_id,
                    "order_id": tool_input["order_id"],
                    "reason": tool_input["reason"],
                    "status": "Initiated",
                    "timestamp": datetime.now().isoformat()
                }
                return {"success": True, "return_id": return_id}
            return {"success": False, "message": "Order not eligible for return"}
        
        elif tool_name == "get_product_info":
            return self.products.get(tool_input["product_id"], "Product not found")
        
        elif tool_name == "create_support_ticket":
            ticket_id = f"T{len(self.support_tickets) + 1}"
            self.support_tickets[ticket_id] = {
                "id": ticket_id,
                "customer_id": tool_input["customer_id"],
                "issue_type": tool_input["issue_type"],
                "description": tool_input["description"],
                "status": "Open",
                "created_at": datetime.now().isoformat()
            }
            return {"success": True, "ticket_id": ticket_id}
        
        elif tool_name == "get_payment_info":
            order = self.orders.get(tool_input["order_id"])
            if order:
                return {
                    "order_id": order["id"],
                    "amount": order["price"],
                    "status": "Paid",  # Simulated
                    "payment_method": "Credit Card"  # Simulated
                }
            return "Order not found"
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def handle_message(self, message: Message) -> Optional[Message]:
        """Handle incoming messages"""
        if message.message_type == "customer_service_status":
            return Message(
                sender=self.agent_id,
                content={
                    "active_tickets": len([t for t in self.support_tickets.values() if t["status"] == "Open"]),
                    "total_orders": len(self.orders),
                    "total_returns": len(self.returns),
                    "capabilities": self.capabilities
                },
                message_type="customer_service_status_response"
            )
        return None
