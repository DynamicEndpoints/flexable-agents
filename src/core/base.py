from typing import Dict, List, Any, Optional, Union, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import asyncio
import logging
from datetime import datetime
import json
import uuid
from contextlib import asynccontextmanager
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

@dataclass
class Message:
    """Base class for agent communication"""
    sender: str
    content: Any
    timestamp: datetime = datetime.now()
    message_type: str = "general"
    metadata: Dict[str, Any] = None

@dataclass
class Task:
    """Representation of a task to be processed"""
    task_id: str
    task_type: str
    priority: int
    input_data: Any
    parameters: Dict[str, Any]
    deadline: Optional[datetime] = None
    dependencies: List[str] = None
    
@dataclass
class TaskResult:
    """Result of a processed task"""
    task_id: str
    status: str
    output: Any
    processing_time: float
    agent_id: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

class Agent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, agent_id: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.status = "initialized"
        self.message_queue = asyncio.Queue()
        self.task_queue = asyncio.Queue()
        self.results: Dict[str, TaskResult] = {}
        
    @abstractmethod
    async def process_task(self, task: Task) -> TaskResult:
        """Process a given task"""
        pass
    
    @abstractmethod
    async def handle_message(self, message: Message) -> Optional[Message]:
        """Handle incoming messages"""
        pass
    
    async def send_message(self, recipient: str, content: Any, message_type: str = "general"):
        """Send a message to another agent"""
        message = Message(
            sender=self.agent_id,
            content=content,
            message_type=message_type
        )
        await self.message_queue.put((recipient, message))
        
    async def receive_message(self) -> Optional[Message]:
        """Receive a message from the message queue"""
        if not self.message_queue.empty():
            return await self.message_queue.get()
        return None

class AgentSystem:
    """Main system for managing agents and task distribution"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.task_queue = asyncio.PriorityQueue()
        self.message_bus = asyncio.Queue()
        self.results: Dict[str, TaskResult] = {}
        
    def register_agent(self, agent: Agent):
        """Register a new agent in the system"""
        self.agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.agent_id} with capabilities: {agent.capabilities}")
        
    def submit_task(self, task: Task):
        """Submit a new task to the system"""
        self.task_queue.put_nowait((task.priority, task))
        logger.info(f"Submitted task: {task.task_id} with priority {task.priority}")
        
    async def route_message(self, sender: str, recipient: str, message: Message):
        """Route a message between agents"""
        if recipient in self.agents:
            await self.agents[recipient].message_queue.put((sender, message))
            logger.debug(f"Routed message from {sender} to {recipient}")
        else:
            logger.warning(f"Recipient agent {recipient} not found")
            
    async def process_tasks(self):
        """Main task processing loop"""
        while True:
            priority, task = await self.task_queue.get()
            try:
                agent = self._find_suitable_agent(task)
                if agent:
                    result = await agent.process_task(task)
                    self.results[task.task_id] = result
                    logger.info(f"Task {task.task_id} completed by agent {agent.agent_id}")
                else:
                    logger.error(f"No suitable agent found for task type: {task.task_type}")
                    self.results[task.task_id] = TaskResult(
                        task_id=task.task_id,
                        status="failed",
                        output=None,
                        agent_id="system",
                        processing_time=0,
                        error="No suitable agent found"
                    )
            except Exception as e:
                logger.error(f"Error processing task {task.task_id}: {str(e)}")
                self.results[task.task_id] = TaskResult(
                    task_id=task.task_id,
                    status="failed",
                    output=None,
                    agent_id="system",
                    processing_time=0,
                    error=str(e)
                )
            finally:
                self.task_queue.task_done()
                
    def _find_suitable_agent(self, task: Task) -> Optional[Agent]:
        """Find an agent capable of handling the given task"""
        available_agents = [
            agent for agent in self.agents.values()
            if task.task_type in agent.capabilities and agent.status != "busy"
        ]
        
        if not available_agents:
            return None
            
        # Simple round-robin selection for now
        return available_agents[0]
        
    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get the result of a specific task"""
        return self.results.get(task_id)
        
    async def run(self):
        """Run the agent system"""
        task_processor = asyncio.create_task(self.process_tasks())
        message_processor = asyncio.create_task(self._process_messages())
        
        await asyncio.gather(task_processor, message_processor)
        
    async def _process_messages(self):
        """Process messages between agents"""
        while True:
            sender_id, (recipient_id, message) = await self.message_bus.get()
            await self.route_message(sender_id, recipient_id, message)
            self.message_bus.task_done()

# Import enhanced MCP-compatible classes
try:
    from .base_mcp import (
        Agent as MCPAgent,
        AgentSystem as MCPAgentSystem,
        MCPToolMetadata,
        AgentError,
        TaskExecutionError,
        create_mcp_tool_metadata,
        mcp_tool
    )
    
    # Provide MCP-enhanced classes as alternatives
    EnhancedAgent = MCPAgent
    EnhancedAgentSystem = MCPAgentSystem
    
except ImportError as e:
    logger.warning(f"MCP enhanced classes not available: {e}")
    # Fallback to basic classes
    EnhancedAgent = None
    EnhancedAgentSystem = None

# Export all classes for compatibility
__all__ = [
    "Message", "Task", "TaskResult", "Agent", "AgentSystem",
    "EnhancedAgent", "EnhancedAgentSystem", "MCPToolMetadata", 
    "AgentError", "TaskExecutionError", "create_mcp_tool_metadata", "mcp_tool"
]
