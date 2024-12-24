from typing import Optional
import asyncio
from datetime import datetime
import time

from ..core.base import Agent, Task, TaskResult, Message
from ..utils.helpers import Timer

class TextProcessingAgent(Agent):
    """Example agent that processes text-based tasks"""
    
    def __init__(self, agent_id: str):
        super().__init__(
            agent_id=agent_id,
            capabilities=["text_analysis", "text_transformation"]
        )
        
    async def process_task(self, task: Task) -> TaskResult:
        """Process text-based tasks"""
        with Timer(f"Task {task.task_id} processing") as timer:
            try:
                if task.task_type == "text_analysis":
                    output = self._analyze_text(task.input_data)
                elif task.task_type == "text_transformation":
                    output = self._transform_text(task.input_data, task.parameters)
                else:
                    raise ValueError(f"Unsupported task type: {task.task_type}")
                
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    output=output,
                    processing_time=timer.duration,
                    agent_id=self.agent_id
                )
            except Exception as e:
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
                content={"status": self.status},
                message_type="status_response"
            )
        return None
    
    def _analyze_text(self, text: str) -> dict:
        """Analyze text and return statistics"""
        words = text.split()
        return {
            "word_count": len(words),
            "char_count": len(text),
            "avg_word_length": sum(len(word) for word in words) / len(words) if words else 0,
            "unique_words": len(set(words))
        }
    
    def _transform_text(self, text: str, parameters: dict) -> str:
        """Transform text based on parameters"""
        if parameters.get("to_upper", False):
            text = text.upper()
        if parameters.get("to_lower", False):
            text = text.lower()
        if parameters.get("reverse", False):
            text = text[::-1]
        return text
