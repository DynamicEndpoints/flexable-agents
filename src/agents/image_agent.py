import asyncio
import base64
from pathlib import Path
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import io
from PIL import Image as PILImage
import httpx
from anthropic import Anthropic

from ..core.base import Agent, Task, TaskResult, Message

logger = logging.getLogger(__name__)

class ImageAgent(Agent):
    """Agent for handling image processing and analysis using Claude's vision capabilities"""
    
    def __init__(
        self,
        agent_id: str,
        work_dir: str,
        api_keys: Dict[str, str],
        supported_formats: List[str] = None
    ):
        super().__init__(
            agent_id=agent_id,
            capabilities=[
                "image_analysis",
                "image_description",
                "creative_generation",
                "url_processing",
                "batch_processing",
                "image_comparison",
                "content_moderation",
                "text_extraction"
            ]
        )
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Claude client
        self.anthropic = Anthropic(api_key=api_keys.get("anthropic"))
        
        # Initialize HTTP client for URL processing
        self.http_client = httpx.AsyncClient()
        
        # Set supported image formats
        self.supported_formats = supported_formats or [
            "image/jpeg", "image/png", "image/gif", "image/webp"
        ]
        
        # Cache for processed images
        self.image_cache = {}
        
    async def process_task(self, task: Task) -> TaskResult:
        """Process image-related tasks"""
        try:
            if task.task_type == "image_analysis":
                output = await self._analyze_image(task.input_data, task.parameters)
            elif task.task_type == "image_description":
                output = await self._describe_image(task.input_data, task.parameters)
            elif task.task_type == "creative_generation":
                output = await self._generate_creative(task.input_data, task.parameters)
            elif task.task_type == "url_processing":
                output = await self._process_url(task.input_data, task.parameters)
            elif task.task_type == "batch_processing":
                output = await self._process_batch(task.input_data, task.parameters)
            elif task.task_type == "image_comparison":
                output = await self._compare_images(task.input_data, task.parameters)
            elif task.task_type == "content_moderation":
                output = await self._moderate_content(task.input_data, task.parameters)
            elif task.task_type == "text_extraction":
                output = await self._extract_text(task.input_data, task.parameters)
            else:
                raise ValueError(f"Unsupported task type: {task.task_type}")
            
            return TaskResult(
                task_id=task.task_id,
                status="success",
                output=output,
                agent_id=self.agent_id
            )
        except Exception as e:
            logger.error(f"Image processing error in task {task.task_id}: {str(e)}")
            return TaskResult(
                task_id=task.task_id,
                status="failed",
                error=str(e),
                agent_id=self.agent_id
            )
    
    async def _load_image(self, image_source: Union[str, bytes, Path]) -> Dict[str, Any]:
        """Load image from various sources and encode in base64"""
        if isinstance(image_source, str) and image_source.startswith(('http://', 'https://')):
            # Load from URL
            async with self.http_client as client:
                response = await client.get(image_source)
                image_data = response.content
        elif isinstance(image_source, (str, Path)):
            # Load from file path
            with open(image_source, "rb") as img_file:
                image_data = img_file.read()
        else:
            # Assume bytes
            image_data = image_source
        
        # Encode to base64
        base64_data = base64.b64encode(image_data).decode('utf-8')
        
        # Get image format
        img = PILImage.open(io.BytesIO(image_data))
        media_type = f"image/{img.format.lower()}"
        
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64_data
            }
        }
    
    async def _analyze_image(self, image_source: Union[str, bytes, Path], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze image content using Claude"""
        image_data = await self._load_image(image_source)
        
        analysis_prompt = parameters.get("analysis_prompt", """
        Analyze this image in detail. Please provide:
        1. Main subject and composition
        2. Key elements and objects
        3. Colors and lighting
        4. Mood and atmosphere
        5. Technical aspects
        6. Notable details
        """)
        
        response = await self.anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": [
                    image_data,
                    {"type": "text", "text": analysis_prompt}
                ]
            }]
        )
        
        analysis = {
            "analysis": response.content[0].text,
            "timestamp": datetime.now().isoformat(),
            "source": str(image_source)
        }
        
        # Cache the analysis
        self.image_cache[str(image_source)] = analysis
        
        return analysis
    
    async def _describe_image(self, image_source: Union[str, bytes, Path], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate natural language description of image"""
        image_data = await self._load_image(image_source)
        
        description_prompt = parameters.get("description_prompt", "Describe this image in detail.")
        style = parameters.get("style", "neutral")
        length = parameters.get("length", "medium")
        
        # Adjust prompt based on style and length
        if style == "creative":
            description_prompt = f"{description_prompt} Be creative and use vivid language."
        elif style == "technical":
            description_prompt = f"{description_prompt} Focus on technical details and precise observations."
        
        if length == "short":
            description_prompt += " Limit to 2-3 sentences."
        elif length == "long":
            description_prompt += " Provide an extensive description with multiple paragraphs."
        
        response = await self.anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": [
                    image_data,
                    {"type": "text", "text": description_prompt}
                ]
            }]
        )
        
        return {
            "description": response.content[0].text,
            "style": style,
            "length": length,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _generate_creative(self, image_source: Union[str, bytes, Path], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate creative content based on image"""
        image_data = await self._load_image(image_source)
        
        creative_type = parameters.get("type", "story")
        style = parameters.get("style", "default")
        
        if creative_type == "story":
            prompt = "Write a short story inspired by this image."
        elif creative_type == "poem":
            prompt = f"Write a {style} poem based on this image."
        elif creative_type == "dialogue":
            prompt = "Write a dialogue between characters in this image."
        else:
            prompt = parameters.get("custom_prompt", "Generate creative content based on this image.")
        
        response = await self.anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": [
                    image_data,
                    {"type": "text", "text": prompt}
                ]
            }]
        )
        
        return {
            "creative_content": response.content[0].text,
            "type": creative_type,
            "style": style,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _process_url(self, url: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process image from URL"""
        try:
            image_data = await self._load_image(url)
            
            # Process based on specified task
            task_type = parameters.get("task_type", "analysis")
            if task_type == "analysis":
                result = await self._analyze_image(url, parameters)
            elif task_type == "description":
                result = await self._describe_image(url, parameters)
            elif task_type == "creative":
                result = await self._generate_creative(url, parameters)
            else:
                raise ValueError(f"Unsupported URL processing task: {task_type}")
            
            return {
                "url": url,
                "task_type": task_type,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise ValueError(f"Failed to process URL {url}: {str(e)}")
    
    async def _process_batch(self, images: List[Union[str, bytes, Path]], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process multiple images in batch"""
        results = []
        errors = []
        
        for img in images:
            try:
                if parameters.get("task_type") == "analysis":
                    result = await self._analyze_image(img, parameters)
                elif parameters.get("task_type") == "description":
                    result = await self._describe_image(img, parameters)
                elif parameters.get("task_type") == "creative":
                    result = await self._generate_creative(img, parameters)
                else:
                    result = await self._analyze_image(img, parameters)
                
                results.append({
                    "source": str(img),
                    "result": result,
                    "success": True
                })
            except Exception as e:
                errors.append({
                    "source": str(img),
                    "error": str(e),
                    "success": False
                })
        
        return {
            "results": results,
            "errors": errors,
            "success_rate": len(results) / (len(results) + len(errors)),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _compare_images(self, images: List[Union[str, bytes, Path]], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Compare multiple images"""
        if len(images) < 2:
            raise ValueError("At least two images are required for comparison")
        
        # Load all images
        image_data_list = []
        for img in images:
            image_data = await self._load_image(img)
            image_data_list.append(image_data)
        
        comparison_prompt = parameters.get("comparison_prompt", """
        Compare these images and provide:
        1. Key similarities
        2. Notable differences
        3. Common elements
        4. Unique aspects of each image
        """)
        
        # Add text prompt to content
        content = image_data_list + [{"type": "text", "text": comparison_prompt}]
        
        response = await self.anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": content
            }]
        )
        
        return {
            "comparison": response.content[0].text,
            "images_compared": [str(img) for img in images],
            "timestamp": datetime.now().isoformat()
        }
    
    async def _moderate_content(self, image_source: Union[str, bytes, Path], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Moderate image content"""
        image_data = await self._load_image(image_source)
        
        moderation_prompt = """
        Analyze this image for potentially inappropriate or sensitive content.
        Consider:
        1. Violence or graphic content
        2. Adult or explicit content
        3. Hate symbols or offensive material
        4. Personal or sensitive information
        5. Copyright concerns
        
        Provide a detailed assessment and content rating.
        """
        
        response = await self.anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": [
                    image_data,
                    {"type": "text", "text": moderation_prompt}
                ]
            }]
        )
        
        return {
            "moderation_result": response.content[0].text,
            "source": str(image_source),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _extract_text(self, image_source: Union[str, bytes, Path], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text from images"""
        image_data = await self._load_image(image_source)
        
        extraction_prompt = parameters.get("extraction_prompt", """
        Extract and transcribe all text visible in this image.
        Please:
        1. Maintain original formatting where possible
        2. Note any unclear or uncertain text
        3. Preserve line breaks and spacing
        4. Include any relevant context about text placement
        """)
        
        response = await self.anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": [
                    image_data,
                    {"type": "text", "text": extraction_prompt}
                ]
            }]
        )
        
        return {
            "extracted_text": response.content[0].text,
            "source": str(image_source),
            "timestamp": datetime.now().isoformat()
        }
    
    async def handle_message(self, message: Message) -> Optional[Message]:
        """Handle incoming messages"""
        if message.message_type == "image_status":
            return Message(
                sender=self.agent_id,
                content={
                    "images_processed": len(self.image_cache),
                    "supported_formats": self.supported_formats,
                    "available_capabilities": self.capabilities
                },
                message_type="image_status_response"
            )
        return None
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.http_client.aclose()
