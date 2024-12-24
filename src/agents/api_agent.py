from typing import Optional, Dict, Any
import aiohttp
import asyncio
import json
from datetime import datetime

from ..core.base import Agent, Task, TaskResult, Message
from ..utils.helpers import Timer, RateLimiter, retry_async

class APIAgent(Agent):
    """Agent for handling API interactions"""
    
    def __init__(self, agent_id: str, base_url: str, api_key: Optional[str] = None):
        super().__init__(
            agent_id=agent_id,
            capabilities=[
                "api_get",
                "api_post",
                "api_put",
                "api_delete",
                "api_batch"
            ]
        )
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.rate_limiter = RateLimiter(max_calls=100, time_window=60)  # 100 calls per minute
        self.session = None
        self.request_history = []
        
    async def initialize(self):
        """Initialize aiohttp session"""
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        )
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            
    async def process_task(self, task: Task) -> TaskResult:
        """Process API-related tasks"""
        with Timer(f"API task {task.task_id}") as timer:
            try:
                if not self.session:
                    await self.initialize()
                    
                await self.rate_limiter.acquire()
                
                if task.task_type == "api_batch":
                    output = await self._process_batch_request(task.input_data)
                else:
                    output = await self._make_request(
                        method=task.task_type.split('_')[1],
                        endpoint=task.input_data,
                        data=task.parameters.get('data'),
                        params=task.parameters.get('params')
                    )
                
                # Record request history
                self.request_history.append({
                    "task_id": task.task_id,
                    "method": task.task_type,
                    "timestamp": datetime.now(),
                    "success": True
                })
                
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    output=output,
                    processing_time=timer.duration,
                    agent_id=self.agent_id,
                    metadata={"endpoint": task.input_data}
                )
            except Exception as e:
                # Record failed request
                self.request_history.append({
                    "task_id": task.task_id,
                    "method": task.task_type,
                    "timestamp": datetime.now(),
                    "success": False,
                    "error": str(e)
                })
                
                return TaskResult(
                    task_id=task.task_id,
                    status="failed",
                    output=None,
                    processing_time=timer.duration,
                    agent_id=self.agent_id,
                    error=str(e)
                )
    
    async def handle_message(self, message: Message) -> Optional[Message]:
        """Handle incoming messages"""
        if message.message_type == "status_request":
            return Message(
                sender=self.agent_id,
                content={
                    "status": self.status,
                    "total_requests": len(self.request_history),
                    "success_rate": self._calculate_success_rate()
                },
                message_type="status_response"
            )
        elif message.message_type == "history_request":
            return Message(
                sender=self.agent_id,
                content=self.request_history,
                message_type="history_response"
            )
        return None
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make an API request with retry logic"""
        
        async def _request():
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            async with getattr(self.session, method.lower())(
                url,
                json=data,
                params=params
            ) as response:
                response.raise_for_status()
                return await response.json()
        
        return await retry_async(
            _request,
            max_retries=3,
            delay=1.0,
            backoff_factor=2.0,
            exceptions=(aiohttp.ClientError,)
        )
    
    async def _process_batch_request(self, requests: list) -> list:
        """Process multiple API requests in parallel"""
        tasks = []
        for req in requests:
            task = asyncio.create_task(
                self._make_request(
                    method=req["method"],
                    endpoint=req["endpoint"],
                    data=req.get("data"),
                    params=req.get("params")
                )
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [
            {"success": not isinstance(r, Exception), "result": str(r) if isinstance(r, Exception) else r}
            for r in results
        ]
    
    def _calculate_success_rate(self) -> float:
        """Calculate the success rate of API requests"""
        if not self.request_history:
            return 0.0
        successful_requests = sum(1 for req in self.request_history if req["success"])
        return successful_requests / len(self.request_history)
