"""Enhanced core base classes with MCP compatibility for Flexible Agents."""

from typing import Dict, List, Any, Optional, Union, Callable, Type
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import asyncio
import logging
from datetime import datetime
import json
import uuid
from contextlib import asynccontextmanager
import time
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Base class for agent communication"""
    sender: str
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    message_type: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """Representation of a task to be processed"""
    task_id: str
    task_type: str
    priority: int
    input_data: Any
    parameters: Dict[str, Any]
    deadline: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    

@dataclass
class TaskResult:
    """Result of a processed task"""
    task_id: str
    status: str
    output: Any
    processing_time: float
    agent_id: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    completed_at: datetime = field(default_factory=datetime.now)


@dataclass
class MCPToolMetadata:
    """Metadata for MCP tool integration"""
    tool_name: str
    description: str
    parameters_schema: Dict[str, Any]
    returns_schema: Optional[Dict[str, Any]] = None
    examples: List[Dict[str, Any]] = field(default_factory=list)
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)


class AgentError(Exception):
    """Base exception for agent-related errors"""
    def __init__(self, message: str, agent_id: str = None, error_code: str = None):
        super().__init__(message)
        self.agent_id = agent_id
        self.error_code = error_code
        self.timestamp = datetime.now()


class TaskExecutionError(AgentError):
    """Exception raised during task execution"""
    def __init__(self, message: str, task_id: str, agent_id: str = None):
        super().__init__(message, agent_id, "TASK_EXECUTION_ERROR")
        self.task_id = task_id


class Agent(ABC):
    """Enhanced base class for all agents with MCP compatibility"""
    
    def __init__(
        self, 
        agent_id: str, 
        capabilities: List[str],
        config: Optional[Dict[str, Any]] = None,
        mcp_tools: Optional[List[MCPToolMetadata]] = None
    ):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.config = config or {}
        self.status = "initialized"
        self.message_queue = asyncio.Queue()
        self.task_queue = asyncio.Queue()
        self.results: Dict[str, TaskResult] = {}
        self.performance_metrics: Dict[str, Any] = {
            "tasks_processed": 0,
            "tasks_successful": 0,
            "tasks_failed": 0,
            "average_processing_time": 0.0,
            "last_activity": None
        }
        
        # MCP-specific attributes
        self.mcp_tools = mcp_tools or []
        self.tool_handlers: Dict[str, Callable] = {}
        
        # Initialize agent
        self._initialize()
        
    def _initialize(self):
        """Initialize agent-specific components"""
        logger.info(f"Initializing agent {self.agent_id} with capabilities: {self.capabilities}")
        
    @abstractmethod
    async def process_task(self, task: Task) -> TaskResult:
        """Process a given task"""
        pass
    
    @abstractmethod
    async def handle_message(self, message: Message) -> Optional[Message]:
        """Handle incoming messages"""
        pass
    
    async def execute_with_timeout(
        self, 
        coro: Callable, 
        timeout: float = 300.0,
        *args, 
        **kwargs
    ) -> Any:
        """Execute a coroutine with timeout"""
        try:
            return await asyncio.wait_for(coro(*args, **kwargs), timeout=timeout)
        except asyncio.TimeoutError:
            raise TaskExecutionError(
                f"Task execution timed out after {timeout}s",
                task_id=kwargs.get('task_id', 'unknown'),
                agent_id=self.agent_id
            )
    
    async def process_task_safe(self, task: Task) -> TaskResult:
        """Safely process a task with error handling and metrics"""
        start_time = time.time()
        
        try:
            # Update metrics
            self.performance_metrics["last_activity"] = datetime.now()
            self.performance_metrics["tasks_processed"] += 1
            
            # Set status to busy
            old_status = self.status
            self.status = "busy"
            
            # Process the task
            result = await self.execute_with_timeout(
                self.process_task,
                timeout=self.config.get('task_timeout', 300.0),
                task=task
            )
            
            # Update success metrics
            self.performance_metrics["tasks_successful"] += 1
            
            # Update processing time
            processing_time = time.time() - start_time
            avg_time = self.performance_metrics["average_processing_time"]
            total_tasks = self.performance_metrics["tasks_processed"]
            self.performance_metrics["average_processing_time"] = (
                (avg_time * (total_tasks - 1) + processing_time) / total_tasks
            )
            
            logger.info(f"Task {task.task_id} completed successfully by {self.agent_id}")
            return result
            
        except Exception as e:
            # Update failure metrics
            self.performance_metrics["tasks_failed"] += 1
            
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            logger.error(f"Task {task.task_id} failed in agent {self.agent_id}: {error_msg}")
            logger.debug(traceback.format_exc())
            
            return TaskResult(
                task_id=task.task_id,
                status="failed",
                output=None,
                processing_time=processing_time,
                agent_id=self.agent_id,
                error=error_msg,
                metadata={"exception_type": type(e).__name__}
            )
        finally:
            # Restore status
            self.status = old_status
    
    def register_mcp_tool(self, metadata: MCPToolMetadata, handler: Callable):
        """Register an MCP tool handler"""
        self.mcp_tools.append(metadata)
        self.tool_handlers[metadata.tool_name] = handler
        logger.info(f"Registered MCP tool: {metadata.tool_name} for agent {self.agent_id}")
    
    async def execute_mcp_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute an MCP tool"""
        if tool_name not in self.tool_handlers:
            raise AgentError(f"Tool {tool_name} not found", self.agent_id)
            
        handler = self.tool_handlers[tool_name]
        
        try:
            if asyncio.iscoroutinefunction(handler):
                return await handler(**kwargs)
            else:
                return handler(**kwargs)
        except Exception as e:
            raise TaskExecutionError(
                f"Error executing tool {tool_name}: {str(e)}",
                task_id=kwargs.get('task_id', tool_name),
                agent_id=self.agent_id
            )
    
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
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        return self.performance_metrics.copy()
    
    def get_mcp_tools_info(self) -> List[Dict[str, Any]]:
        """Get information about registered MCP tools"""
        return [
            {
                "name": tool.tool_name,
                "description": tool.description,
                "parameters_schema": tool.parameters_schema,
                "returns_schema": tool.returns_schema,
                "category": tool.category,
                "tags": tool.tags,
                "examples": tool.examples
            }
            for tool in self.mcp_tools
        ]


class AgentSystem:
    """Enhanced agent system with MCP compatibility and improved management"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.agents: Dict[str, Agent] = {}
        self.task_queue = asyncio.PriorityQueue()
        self.message_bus = asyncio.Queue()
        self.results: Dict[str, TaskResult] = {}
        
        # System metrics
        self.system_metrics = {
            "start_time": datetime.now(),
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "agents_registered": 0,
            "messages_routed": 0
        }
        
        # Task management
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_history: List[TaskResult] = []
        
        logger.info("Initialized enhanced AgentSystem with MCP compatibility")
        
    def register_agent(self, agent: Agent):
        """Register a new agent in the system"""
        if agent.agent_id in self.agents:
            logger.warning(f"Agent {agent.agent_id} already registered, replacing")
            
        self.agents[agent.agent_id] = agent
        self.system_metrics["agents_registered"] += 1
        
        logger.info(
            f"Registered agent: {agent.agent_id} with capabilities: {agent.capabilities}"
        )
        
        # Log MCP tools if any
        if agent.mcp_tools:
            tool_names = [tool.tool_name for tool in agent.mcp_tools]
            logger.info(f"Agent {agent.agent_id} has MCP tools: {tool_names}")
        
    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
        else:
            logger.warning(f"Agent {agent_id} not found for unregistration")
    
    async def submit_task(self, task: Task) -> str:
        """Submit a new task to the system"""
        task_id = task.task_id or str(uuid.uuid4())
        task.task_id = task_id
        
        await self.task_queue.put((task.priority, task))
        self.system_metrics["total_tasks"] += 1
        
        logger.info(f"Submitted task: {task_id} with priority {task.priority}")
        return task_id
        
    async def route_message(self, sender: str, recipient: str, message: Message):
        """Route a message between agents"""
        if recipient in self.agents:
            await self.agents[recipient].message_queue.put((sender, message))
            self.system_metrics["messages_routed"] += 1
            logger.debug(f"Routed message from {sender} to {recipient}")
        else:
            logger.warning(f"Recipient agent {recipient} not found")
            
    async def process_tasks(self):
        """Enhanced task processing loop with better error handling"""
        logger.info("Starting task processing loop")
        
        while True:
            try:
                priority, task = await self.task_queue.get()
                
                # Find suitable agent
                agent = self._find_suitable_agent(task)
                if not agent:
                    error_msg = f"No suitable agent found for task type: {task.task_type}"
                    logger.error(error_msg)
                    
                    result = TaskResult(
                        task_id=task.task_id,
                        status="failed",
                        output=None,
                        agent_id="system",
                        processing_time=0,
                        error=error_msg
                    )
                    
                    self._record_task_result(result)
                    continue
                
                # Process task safely
                result = await agent.process_task_safe(task)
                self._record_task_result(result)
                
            except Exception as e:
                logger.error(f"Critical error in task processing loop: {str(e)}")
                logger.debug(traceback.format_exc())
            finally:
                self.task_queue.task_done()
    
    def _record_task_result(self, result: TaskResult):
        """Record task result and update metrics"""
        self.results[result.task_id] = result
        self.task_history.append(result)
        
        # Update system metrics
        if result.status == "success":
            self.system_metrics["successful_tasks"] += 1
        else:
            self.system_metrics["failed_tasks"] += 1
            
        # Keep only last 1000 task results in history
        if len(self.task_history) > 1000:
            self.task_history = self.task_history[-1000:]
                
    def _find_suitable_agent(self, task: Task) -> Optional[Agent]:
        """Find an agent capable of handling the given task"""
        available_agents = [
            agent for agent in self.agents.values()
            if task.task_type in agent.capabilities and agent.status != "busy"
        ]
        
        if not available_agents:
            return None
            
        # Simple load balancing - choose agent with lowest task count
        return min(available_agents, key=lambda a: a.performance_metrics["tasks_processed"])
        
    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get the result of a specific task"""
        return self.results.get(task_id)
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[str]:
        """List all registered agent IDs"""
        return list(self.agents.keys())
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics"""
        uptime = (datetime.now() - self.system_metrics["start_time"]).total_seconds()
        
        return {
            **self.system_metrics,
            "uptime_seconds": uptime,
            "agent_count": len(self.agents),
            "pending_tasks": self.task_queue.qsize(),
            "pending_messages": self.message_bus.qsize()
        }
    
    def get_all_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get all MCP tools from all agents"""
        all_tools = []
        for agent in self.agents.values():
            tools = agent.get_mcp_tools_info()
            for tool in tools:
                tool["agent_id"] = agent.agent_id
                all_tools.append(tool)
        return all_tools
        
    async def run(self):
        """Run the agent system"""
        logger.info("Starting AgentSystem")
        
        # Start task processor
        task_processor = asyncio.create_task(self.process_tasks())
        
        # Start message processor
        message_processor = asyncio.create_task(self._process_messages())
        
        try:
            await asyncio.gather(task_processor, message_processor)
        except Exception as e:
            logger.error(f"Error in AgentSystem.run: {str(e)}")
            raise
        finally:
            logger.info("AgentSystem stopped")
        
    async def _process_messages(self):
        """Process messages between agents"""
        logger.info("Starting message processing loop")
        
        while True:
            try:
                sender_id, (recipient_id, message) = await self.message_bus.get()
                await self.route_message(sender_id, recipient_id, message)
                self.message_bus.task_done()
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                logger.debug(traceback.format_exc())
    
    async def shutdown(self):
        """Gracefully shutdown the system"""
        logger.info("Shutting down AgentSystem")
        
        # Cancel running tasks
        for task in self.running_tasks.values():
            if not task.done():
                task.cancel()
                
        # Wait for queues to be processed
        await self.task_queue.join()
        await self.message_bus.join()
        
        logger.info("AgentSystem shutdown complete")


# Utility functions for MCP integration
def create_mcp_tool_metadata(
    name: str,
    description: str,
    parameters: Dict[str, Any],
    returns: Optional[Dict[str, Any]] = None,
    category: Optional[str] = None,
    tags: List[str] = None,
    examples: List[Dict[str, Any]] = None
) -> MCPToolMetadata:
    """Helper function to create MCP tool metadata"""
    return MCPToolMetadata(
        tool_name=name,
        description=description,
        parameters_schema=parameters,
        returns_schema=returns,
        category=category,
        tags=tags or [],
        examples=examples or []
    )


def mcp_tool(
    name: str = None,
    description: str = None,
    category: str = None,
    tags: List[str] = None,
    examples: List[Dict[str, Any]] = None
):
    """Decorator for marking methods as MCP tools"""
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"Tool: {tool_name}"
        
        # Store metadata on function
        func._mcp_tool_name = tool_name
        func._mcp_tool_description = tool_description
        func._mcp_tool_category = category
        func._mcp_tool_tags = tags or []
        func._mcp_tool_examples = examples or []
        
        return func
    return decorator
