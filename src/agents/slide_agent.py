import asyncio
import base64
from pathlib import Path
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import fitz  # PyMuPDF
import io
from PIL import Image
import re
from anthropic import Anthropic

from ..core.base import Agent, Task, TaskResult, Message

logger = logging.getLogger(__name__)

class SlideAgent(Agent):
    """Agent for handling slide decks and presentations"""
    
    def __init__(
        self,
        agent_id: str,
        work_dir: str,
        api_keys: Dict[str, str],
        max_pages_per_request: int = 100
    ):
        super().__init__(
            agent_id=agent_id,
            capabilities=[
                "slide_analysis",
                "slide_extraction",
                "slide_narration",
                "content_extraction",
                "slide_comparison",
                "slide_summarization"
            ]
        )
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Claude client
        self.anthropic = Anthropic(api_key=api_keys.get("anthropic"))
        
        # Configuration
        self.max_pages_per_request = max_pages_per_request
        
        # Cache for processed slides
        self.slide_cache = {}
        
    async def process_task(self, task: Task) -> TaskResult:
        """Process slide-related tasks"""
        try:
            if task.task_type == "slide_analysis":
                output = await self._analyze_slides(task.input_data, task.parameters)
            elif task.task_type == "slide_extraction":
                output = await self._extract_slides(task.input_data, task.parameters)
            elif task.task_type == "slide_narration":
                output = await self._narrate_slides(task.input_data, task.parameters)
            elif task.task_type == "content_extraction":
                output = await self._extract_content(task.input_data, task.parameters)
            elif task.task_type == "slide_comparison":
                output = await self._compare_slides(task.input_data, task.parameters)
            elif task.task_type == "slide_summarization":
                output = await self._summarize_slides(task.input_data, task.parameters)
            else:
                raise ValueError(f"Unsupported task type: {task.task_type}")
            
            return TaskResult(
                task_id=task.task_id,
                status="success",
                output=output,
                agent_id=self.agent_id
            )
        except Exception as e:
            logger.error(f"Slide processing error in task {task.task_id}: {str(e)}")
            return TaskResult(
                task_id=task.task_id,
                status="failed",
                error=str(e),
                agent_id=self.agent_id
            )
    
    async def _analyze_slides(self, pdf_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze slide deck using Claude's vision capabilities"""
        # Load and encode the PDF
        with open(pdf_path, "rb") as pdf_file:
            pdf_data = base64.b64encode(pdf_file.read()).decode('utf-8')
        
        analysis_prompt = parameters.get("analysis_prompt", """
        Analyze this slide deck in detail. Please provide:
        1. Overview and main themes
        2. Key metrics and data points
        3. Visual elements and their effectiveness
        4. Structure and flow
        5. Key takeaways
        6. Areas for improvement
        """)
        
        response = await self.anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_data}},
                    {"type": "text", "text": analysis_prompt}
                ]
            }]
        )
        
        analysis = {
            "analysis": response.content[0].text,
            "timestamp": datetime.now().isoformat(),
            "deck_path": pdf_path
        }
        
        # Cache the analysis
        self.slide_cache[pdf_path] = analysis
        
        return analysis
    
    async def _extract_slides(self, pdf_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extract individual slides from a PDF presentation"""
        # Open the PDF
        pdf_document = fitz.open(pdf_path)
        extracted_slides = []
        
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            
            # Extract images
            image_list = page.get_images(full=True)
            
            # Extract text
            text = page.get_text()
            
            # Save page as image
            pix = page.get_pixmap()
            img_path = self.work_dir / f"slide_{page_num + 1}.png"
            pix.save(str(img_path))
            
            extracted_slides.append({
                "page_number": page_num + 1,
                "text_content": text,
                "image_path": str(img_path),
                "image_count": len(image_list)
            })
        
        return {
            "slides": extracted_slides,
            "total_slides": len(extracted_slides),
            "source_pdf": pdf_path
        }
    
    async def _narrate_slides(self, pdf_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a detailed narration of the slide deck"""
        # Load and encode the PDF
        with open(pdf_path, "rb") as pdf_file:
            pdf_data = base64.b64encode(pdf_file.read()).decode('utf-8')
        
        narration_prompt = parameters.get("narration_prompt", """
        You are presenting this slide deck to an audience. Please provide a detailed narration of each slide, including:
        1. Description of visual elements
        2. Explanation of data and charts
        3. Key messages and insights
        4. Transitions between slides
        
        Structure your response like this:
        <narration>
            <slide_narration id=1>
            [Your narration for slide 1]
            </slide_narration>
            
            <slide_narration id=2>
            [Your narration for slide 2]
            </slide_narration>
            ... and so on
        </narration>
        """)
        
        response = await self.anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_data}},
                    {"type": "text", "text": narration_prompt}
                ]
            }]
        )
        
        # Parse the narration
        narration_text = response.content[0].text
        slides_pattern = r"<slide_narration id=(\d+)>(.*?)</slide_narration>"
        slides_narration = re.findall(slides_pattern, narration_text, re.DOTALL)
        
        structured_narration = {
            int(slide_num): narration.strip()
            for slide_num, narration in slides_narration
        }
        
        return {
            "narration": structured_narration,
            "total_slides": len(structured_narration),
            "source_pdf": pdf_path,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _extract_content(self, pdf_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extract specific content types from slides"""
        content_types = parameters.get("content_types", ["text", "charts", "tables", "images"])
        
        # Load and encode the PDF
        with open(pdf_path, "rb") as pdf_file:
            pdf_data = base64.b64encode(pdf_file.read()).decode('utf-8')
        
        extraction_prompt = f"""
        Please extract the following content types from this slide deck:
        {', '.join(content_types)}
        
        For each content type, provide:
        1. Location (slide number)
        2. Description
        3. Relevant data or text
        4. Context and significance
        
        Format the response as JSON.
        """
        
        response = await self.anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_data}},
                    {"type": "text", "text": extraction_prompt}
                ]
            }]
        )
        
        try:
            extracted_content = json.loads(response.content[0].text)
        except json.JSONDecodeError:
            extracted_content = {"raw_text": response.content[0].text}
        
        return {
            "extracted_content": extracted_content,
            "content_types": content_types,
            "source_pdf": pdf_path,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _compare_slides(self, pdf_paths: List[str], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Compare multiple slide decks"""
        comparisons = []
        
        for i, pdf1 in enumerate(pdf_paths):
            for pdf2 in pdf_paths[i+1:]:
                # Load and encode both PDFs
                with open(pdf1, "rb") as f1, open(pdf2, "rb") as f2:
                    pdf1_data = base64.b64encode(f1.read()).decode('utf-8')
                    pdf2_data = base64.b64encode(f2.read()).decode('utf-8')
                
                comparison_prompt = parameters.get("comparison_prompt", """
                Compare these two slide decks and provide:
                1. Common themes and messages
                2. Key differences in content and approach
                3. Strengths and weaknesses of each
                4. Overall effectiveness comparison
                """)
                
                response = await self.anthropic.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=4000,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf1_data}},
                            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf2_data}},
                            {"type": "text", "text": comparison_prompt}
                        ]
                    }]
                )
                
                comparisons.append({
                    "deck1": pdf1,
                    "deck2": pdf2,
                    "comparison": response.content[0].text
                })
        
        return {
            "comparisons": comparisons,
            "decks_compared": pdf_paths,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _summarize_slides(self, pdf_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive summary of the slide deck"""
        # Load and encode the PDF
        with open(pdf_path, "rb") as pdf_file:
            pdf_data = base64.b64encode(pdf_file.read()).decode('utf-8')
        
        summary_prompt = parameters.get("summary_prompt", """
        Please provide a comprehensive summary of this slide deck, including:
        1. Executive Summary (2-3 sentences)
        2. Key Points (bullet points)
        3. Important Data and Metrics
        4. Main Conclusions
        5. Action Items or Next Steps
        
        Format the response as a structured JSON object.
        """)
        
        response = await self.anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_data}},
                    {"type": "text", "text": summary_prompt}
                ]
            }]
        )
        
        try:
            summary = json.loads(response.content[0].text)
        except json.JSONDecodeError:
            summary = {"raw_text": response.content[0].text}
        
        return {
            "summary": summary,
            "source_pdf": pdf_path,
            "timestamp": datetime.now().isoformat()
        }
    
    async def handle_message(self, message: Message) -> Optional[Message]:
        """Handle incoming messages"""
        if message.message_type == "slide_status":
            return Message(
                sender=self.agent_id,
                content={
                    "decks_processed": len(self.slide_cache),
                    "available_capabilities": self.capabilities,
                    "max_pages_per_request": self.max_pages_per_request
                },
                message_type="slide_status_response"
            )
        return None
