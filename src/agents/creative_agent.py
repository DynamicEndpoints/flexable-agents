import asyncio
import base64
from pathlib import Path
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import httpx
from anthropic import Anthropic

from ..core.base import Agent, Task, TaskResult, Message

logger = logging.getLogger(__name__)

class CreativeAgent(Agent):
    """Agent for generating creative content from images using Claude's capabilities"""
    
    def __init__(
        self,
        agent_id: str,
        work_dir: str,
        api_keys: Dict[str, str],
        creative_styles: List[str] = None
    ):
        super().__init__(
            agent_id=agent_id,
            capabilities=[
                "poetry_generation",
                "story_creation",
                "descriptive_writing",
                "creative_analysis",
                "metaphor_generation",
                "emotional_interpretation",
                "character_development",
                "scene_setting"
            ]
        )
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Claude client
        self.anthropic = Anthropic(api_key=api_keys.get("anthropic"))
        
        # Initialize HTTP client for URL processing
        self.http_client = httpx.AsyncClient()
        
        # Set creative styles
        self.creative_styles = creative_styles or [
            "romantic", "dramatic", "whimsical", "mysterious",
            "philosophical", "humorous", "melancholic", "epic"
        ]
        
        # Cache for generated content
        self.content_cache = {}
        
    async def process_task(self, task: Task) -> TaskResult:
        """Process creative tasks"""
        try:
            if task.task_type == "poetry_generation":
                output = await self._generate_poetry(task.input_data, task.parameters)
            elif task.task_type == "story_creation":
                output = await self._create_story(task.input_data, task.parameters)
            elif task.task_type == "descriptive_writing":
                output = await self._write_description(task.input_data, task.parameters)
            elif task.task_type == "creative_analysis":
                output = await self._analyze_creatively(task.input_data, task.parameters)
            elif task.task_type == "metaphor_generation":
                output = await self._generate_metaphors(task.input_data, task.parameters)
            elif task.task_type == "emotional_interpretation":
                output = await self._interpret_emotions(task.input_data, task.parameters)
            elif task.task_type == "character_development":
                output = await self._develop_characters(task.input_data, task.parameters)
            elif task.task_type == "scene_setting":
                output = await self._set_scene(task.input_data, task.parameters)
            else:
                raise ValueError(f"Unsupported task type: {task.task_type}")
            
            return TaskResult(
                task_id=task.task_id,
                status="success",
                output=output,
                agent_id=self.agent_id
            )
        except Exception as e:
            logger.error(f"Creative generation error in task {task.task_id}: {str(e)}")
            return TaskResult(
                task_id=task.task_id,
                status="failed",
                error=str(e),
                agent_id=self.agent_id
            )
    
    async def _load_image(self, image_source: Union[str, bytes, Path]) -> Dict[str, Any]:
        """Load image from file or URL and encode in base64"""
        try:
            if isinstance(image_source, str) and image_source.startswith(('http://', 'https://')):
                async with self.http_client as client:
                    response = await client.get(image_source)
                    image_data = response.content
            elif isinstance(image_source, (str, Path)):
                with open(image_source, "rb") as img_file:
                    image_data = img_file.read()
            else:
                image_data = image_source
            
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",  # Assuming JPEG for simplicity
                    "data": base64_data
                }
            }
        except Exception as e:
            raise ValueError(f"Failed to load image: {str(e)}")
    
    async def _generate_poetry(self, image_source: Union[str, bytes, Path], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate poetry based on image"""
        image_data = await self._load_image(image_source)
        
        poetry_type = parameters.get("type", "sonnet")
        style = parameters.get("style", "romantic")
        
        prompts = {
            "sonnet": "Write a sonnet (14 lines, traditional form) based on this image.",
            "haiku": "Write a haiku series based on this image.",
            "free_verse": "Write a free verse poem inspired by this image.",
            "ballad": "Write a ballad telling the story of this image.",
            "limerick": "Write a playful limerick based on this image."
        }
        
        prompt = prompts.get(poetry_type, prompts["sonnet"])
        if style != "default":
            prompt = f"{prompt} Use a {style} style."
        
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
            "poetry": response.content[0].text,
            "type": poetry_type,
            "style": style,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _create_story(self, image_source: Union[str, bytes, Path], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a story based on image"""
        image_data = await self._load_image(image_source)
        
        genre = parameters.get("genre", "general")
        length = parameters.get("length", "short")
        perspective = parameters.get("perspective", "third_person")
        
        prompt = f"""Write a {length} story inspired by this image. 
        Genre: {genre}
        Perspective: {perspective}
        
        Include:
        1. Vivid descriptions
        2. Character development
        3. Engaging plot
        4. Meaningful conclusion
        """
        
        response = await self.anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=3000,
            messages=[{
                "role": "user",
                "content": [
                    image_data,
                    {"type": "text", "text": prompt}
                ]
            }]
        )
        
        return {
            "story": response.content[0].text,
            "genre": genre,
            "length": length,
            "perspective": perspective,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _write_description(self, image_source: Union[str, bytes, Path], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate descriptive writing based on image"""
        image_data = await self._load_image(image_source)
        
        style = parameters.get("style", "vivid")
        focus = parameters.get("focus", "all")
        length = parameters.get("length", "medium")
        
        prompt = f"""Write a {length} {style} description of this image.
        Focus on: {focus}
        
        Make the description:
        1. Engaging and colorful
        2. Rich in sensory details
        3. Well-structured
        4. Emotionally evocative
        """
        
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
            "description": response.content[0].text,
            "style": style,
            "focus": focus,
            "length": length,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _analyze_creatively(self, image_source: Union[str, bytes, Path], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform creative analysis of image"""
        image_data = await self._load_image(image_source)
        
        aspects = parameters.get("aspects", ["symbolism", "mood", "themes", "artistic_elements"])
        depth = parameters.get("depth", "detailed")
        
        prompt = f"""Analyze this image creatively, exploring:
        {', '.join(aspects)}
        
        Provide a {depth} analysis that:
        1. Uncovers deeper meanings
        2. Explores symbolic elements
        3. Discusses emotional impact
        4. Connects to broader themes
        """
        
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
            "analysis": response.content[0].text,
            "aspects": aspects,
            "depth": depth,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _generate_metaphors(self, image_source: Union[str, bytes, Path], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metaphors based on image"""
        image_data = await self._load_image(image_source)
        
        style = parameters.get("style", "poetic")
        count = parameters.get("count", 5)
        
        prompt = f"""Generate {count} unique metaphors inspired by this image.
        Style: {style}
        
        For each metaphor:
        1. Explain the comparison
        2. Highlight the significance
        3. Connect to deeper meaning
        """
        
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
            "metaphors": response.content[0].text,
            "style": style,
            "count": count,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _interpret_emotions(self, image_source: Union[str, bytes, Path], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Interpret emotional content of image"""
        image_data = await self._load_image(image_source)
        
        depth = parameters.get("depth", "deep")
        aspects = parameters.get("aspects", ["mood", "atmosphere", "emotional_impact"])
        
        prompt = f"""Interpret the emotional content of this image with {depth} analysis.
        Focus on: {', '.join(aspects)}
        
        Consider:
        1. Overall emotional atmosphere
        2. Specific emotional elements
        3. Psychological impact
        4. Universal emotional themes
        """
        
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
            "interpretation": response.content[0].text,
            "depth": depth,
            "aspects": aspects,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _develop_characters(self, image_source: Union[str, bytes, Path], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Develop characters based on image"""
        image_data = await self._load_image(image_source)
        
        count = parameters.get("count", 1)
        depth = parameters.get("depth", "detailed")
        
        prompt = f"""Develop {count} character(s) inspired by this image.
        Provide {depth} character profiles including:
        1. Physical description
        2. Personality traits
        3. Background story
        4. Motivations and desires
        5. Conflicts and challenges
        """
        
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
            "characters": response.content[0].text,
            "count": count,
            "depth": depth,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _set_scene(self, image_source: Union[str, bytes, Path], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed scene setting based on image"""
        image_data = await self._load_image(image_source)
        
        style = parameters.get("style", "descriptive")
        focus = parameters.get("focus", ["atmosphere", "physical_details", "sensory_elements"])
        
        prompt = f"""Create a detailed scene setting based on this image.
        Style: {style}
        Focus on: {', '.join(focus)}
        
        Include:
        1. Physical environment
        2. Atmosphere and mood
        3. Sensory details
        4. Time and context
        5. Environmental elements
        """
        
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
            "scene": response.content[0].text,
            "style": style,
            "focus": focus,
            "timestamp": datetime.now().isoformat()
        }
    
    async def handle_message(self, message: Message) -> Optional[Message]:
        """Handle incoming messages"""
        if message.message_type == "creative_status":
            return Message(
                sender=self.agent_id,
                content={
                    "content_generated": len(self.content_cache),
                    "available_styles": self.creative_styles,
                    "capabilities": self.capabilities
                },
                message_type="creative_status_response"
            )
        return None
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.http_client.aclose()
