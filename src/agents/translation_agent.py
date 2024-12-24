from typing import Optional, Dict, Any, List, Union
import asyncio
import aiohttp
from datetime import datetime
import json
from pathlib import Path
import base64
from PIL import Image
import pytesseract
import pdf2image
import io
import os
import logging
from langdetect import detect
import deepl
from googletrans import Translator
from anthropic import Anthropic

from ..core.base import Agent, Task, TaskResult, Message
from ..utils.helpers import Timer, RateLimiter, Cache

logger = logging.getLogger(__name__)

class TranslationAgent(Agent):
    """Agent for handling professional document translation across multiple languages"""
    
    def __init__(
        self,
        agent_id: str,
        work_dir: str,
        api_keys: Dict[str, str],
        supported_languages: List[str] = None
    ):
        super().__init__(
            agent_id=agent_id,
            capabilities=[
                "document_translation",
                "text_translation",
                "language_detection",
                "document_ocr",
                "quality_check",
                "batch_translation"
            ]
        )
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize translation services
        self.api_keys = api_keys
        self.deepl_client = deepl.Translator(api_keys.get("deepl"))
        self.google_translator = Translator()
        self.anthropic_client = Anthropic(api_key=api_keys.get("anthropic"))
        
        # Set up caching and rate limiting
        self.cache = Cache(ttl=3600)  # 1-hour cache
        self.rate_limiter = RateLimiter(max_calls=100, time_window=60)
        
        # Translation history
        self.translation_history: List[Dict[str, Any]] = []
        
        # Supported languages (ISO 639-1 codes)
        self.supported_languages = supported_languages or [
            "en", "es", "fr", "de", "it", "pt", "nl", "ru", "zh", "ja", "ko"
        ]
        
    async def process_task(self, task: Task) -> TaskResult:
        """Process translation tasks"""
        with Timer(f"Translation task {task.task_id}") as timer:
            try:
                if task.task_type == "document_translation":
                    output = await self._translate_document(task.input_data, task.parameters)
                elif task.task_type == "text_translation":
                    output = await self._translate_text(task.input_data, task.parameters)
                elif task.task_type == "language_detection":
                    output = self._detect_language(task.input_data)
                elif task.task_type == "document_ocr":
                    output = await self._perform_ocr(task.input_data, task.parameters)
                elif task.task_type == "quality_check":
                    output = await self._check_translation_quality(task.input_data, task.parameters)
                elif task.task_type == "batch_translation":
                    output = await self._process_batch_translation(task.input_data, task.parameters)
                else:
                    raise ValueError(f"Unsupported task type: {task.task_type}")
                
                # Record translation
                self.translation_history.append({
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "timestamp": datetime.now(),
                    "source_language": task.parameters.get("source_lang"),
                    "target_language": task.parameters.get("target_lang"),
                    "success": True
                })
                
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    output=output,
                    processing_time=timer.duration,
                    agent_id=self.agent_id,
                    metadata={"translation_count": len(self.translation_history)}
                )
            except Exception as e:
                logger.error(f"Translation error in task {task.task_id}: {str(e)}")
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
        if message.message_type == "translation_status":
            return Message(
                sender=self.agent_id,
                content={
                    "translations_completed": len(self.translation_history),
                    "supported_languages": self.supported_languages,
                    "available_services": list(self.api_keys.keys())
                },
                message_type="translation_status_response"
            )
        elif message.message_type == "translation_history":
            return Message(
                sender=self.agent_id,
                content=self.translation_history,
                message_type="translation_history_response"
            )
        return None
    
    async def _translate_document(self, document_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Translate a document while preserving formatting"""
        source_lang = parameters.get("source_lang")
        target_lang = parameters.get("target_lang")
        service = parameters.get("service", "deepl")
        preserve_formatting = parameters.get("preserve_formatting", True)
        
        if not source_lang:
            # Detect source language
            source_lang = self._detect_language(document_path)
        
        # Extract text while preserving formatting
        if document_path.endswith('.pdf'):
            text_content = await self._extract_text_from_pdf(document_path, preserve_formatting)
        else:
            text_content = await self._extract_text_from_document(document_path, preserve_formatting)
        
        # Translate text
        translated_content = await self._translate_text(text_content, {
            "source_lang": source_lang,
            "target_lang": target_lang,
            "service": service
        })
        
        # Save translated document
        output_path = self._save_translated_document(
            translated_content,
            document_path,
            target_lang,
            preserve_formatting
        )
        
        return {
            "translated_path": str(output_path),
            "source_language": source_lang,
            "target_language": target_lang,
            "service_used": service
        }
    
    async def _translate_text(self, text: str, parameters: Dict[str, Any]) -> str:
        """Translate text using specified service"""
        source_lang = parameters.get("source_lang")
        target_lang = parameters.get("target_lang")
        service = parameters.get("service", "deepl")
        
        # Check cache first
        cache_key = f"{text}:{source_lang}:{target_lang}:{service}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        await self.rate_limiter.acquire()
        
        if service == "deepl":
            result = self.deepl_client.translate_text(
                text,
                source_lang=source_lang,
                target_lang=target_lang
            )
            translated_text = result.text
        elif service == "google":
            result = self.google_translator.translate(
                text,
                src=source_lang,
                dest=target_lang
            )
            translated_text = result.text
        elif service == "anthropic":
            # Use Claude for more nuanced translations
            prompt = f"""
            Translate the following text from {source_lang} to {target_lang}.
            Preserve any special formatting, technical terms, and cultural context.
            
            Text to translate:
            {text}
            """
            
            response = self.anthropic_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            translated_text = response.content[0].text
        else:
            raise ValueError(f"Unsupported translation service: {service}")
        
        # Cache the result
        self.cache.set(cache_key, translated_text)
        
        return translated_text
    
    def _detect_language(self, text: str) -> str:
        """Detect the language of the text"""
        try:
            return detect(text)
        except:
            logger.warning(f"Could not detect language for text: {text[:100]}...")
            return "en"  # Default to English
    
    async def _perform_ocr(self, image_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform OCR on an image or scanned document"""
        # Load image
        image = Image.open(image_path)
        
        # Set OCR language if specified
        lang = parameters.get("language", "eng")
        
        # Perform OCR
        text = pytesseract.image_to_string(image, lang=lang)
        
        # Get bounding boxes for text regions
        boxes = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
        
        # Structure the results
        results = []
        for i in range(len(boxes['text'])):
            if boxes['text'][i].strip():
                results.append({
                    'text': boxes['text'][i],
                    'confidence': boxes['conf'][i],
                    'bbox': {
                        'x': boxes['left'][i],
                        'y': boxes['top'][i],
                        'w': boxes['width'][i],
                        'h': boxes['height'][i]
                    }
                })
        
        return {
            "full_text": text,
            "text_regions": results,
            "detected_language": self._detect_language(text)
        }
    
    async def _check_translation_quality(
        self,
        translation_data: Dict[str, str],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check translation quality using various metrics"""
        original_text = translation_data["original"]
        translated_text = translation_data["translated"]
        
        # Use Claude to evaluate translation quality
        prompt = f"""
        Evaluate the quality of this translation:
        
        Original ({parameters['source_lang']}):
        {original_text}
        
        Translation ({parameters['target_lang']}):
        {translated_text}
        
        Please assess:
        1. Accuracy (preservation of meaning)
        2. Fluency (natural in target language)
        3. Terminology consistency
        4. Cultural appropriateness
        
        Provide a score out of 100 for each aspect and overall quality.
        """
        
        response = self.anthropic_client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        quality_assessment = response.content[0].text
        
        # Also perform automated checks
        automated_checks = {
            "length_ratio": len(translated_text) / len(original_text),
            "preserved_elements": self._check_preserved_elements(
                original_text,
                translated_text,
                parameters.get("preserve_elements", [])
            )
        }
        
        return {
            "human_assessment": quality_assessment,
            "automated_checks": automated_checks,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _process_batch_translation(
        self,
        documents: List[str],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process multiple documents for translation"""
        results = []
        failed = []
        
        for doc_path in documents:
            try:
                result = await self._translate_document(doc_path, parameters)
                results.append({
                    "original": doc_path,
                    "translated": result["translated_path"],
                    "success": True
                })
            except Exception as e:
                failed.append({
                    "original": doc_path,
                    "error": str(e),
                    "success": False
                })
        
        return {
            "successful_translations": results,
            "failed_translations": failed,
            "success_rate": len(results) / len(documents)
        }
    
    async def _extract_text_from_pdf(self, pdf_path: str, preserve_formatting: bool) -> str:
        """Extract text from PDF while optionally preserving formatting"""
        # Convert PDF to images
        images = pdf2image.convert_from_path(pdf_path)
        
        text_content = []
        for img in images:
            # Perform OCR on each page
            text = pytesseract.image_to_string(img)
            if preserve_formatting:
                # Get layout information
                layout = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                text = self._reconstruct_layout(text, layout)
            text_content.append(text)
        
        return "\n\n".join(text_content)
    
    async def _extract_text_from_document(self, doc_path: str, preserve_formatting: bool) -> str:
        """Extract text from various document formats"""
        # Implementation depends on document type
        # This is a simplified version
        with open(doc_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _save_translated_document(
        self,
        translated_content: str,
        original_path: str,
        target_lang: str,
        preserve_formatting: bool
    ) -> Path:
        """Save translated content to a new document"""
        original_path = Path(original_path)
        output_path = self.work_dir / f"{original_path.stem}_{target_lang}{original_path.suffix}"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_content)
        
        return output_path
    
    def _check_preserved_elements(
        self,
        original: str,
        translated: str,
        elements_to_preserve: List[str]
    ) -> Dict[str, bool]:
        """Check if specified elements were preserved in translation"""
        results = {}
        for element in elements_to_preserve:
            if element.startswith('regex:'):
                # Handle regex patterns
                pattern = element[6:]
                results[element] = bool(re.search(pattern, translated))
            else:
                # Direct string matching
                results[element] = element in translated
        return results
    
    def _reconstruct_layout(self, text: str, layout: Dict[str, Any]) -> str:
        """Reconstruct document layout from OCR data"""
        # This is a simplified version
        # In a real implementation, you would use the layout information
        # to preserve formatting, spacing, and structure
        return text
