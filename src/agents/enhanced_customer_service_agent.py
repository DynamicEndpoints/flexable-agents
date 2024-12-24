import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import json
from anthropic import Anthropic
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from googletrans import Translator

from ..core.base import Agent, Task, TaskResult, Message

logger = logging.getLogger(__name__)

class EnhancedCustomerServiceAgent(Agent):
    """Enhanced agent for handling customer service with sentiment analysis and multi-language support"""
    
    def __init__(
        self,
        agent_id: str,
        work_dir: str,
        api_keys: Dict[str, str],
        db_config: Dict[str, Any] = None,
        supported_languages: List[str] = None
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
                "payment_info",
                "sentiment_analysis",
                "language_translation",
                "automated_followup",
                "satisfaction_survey",
                "escalation_handling",
                "knowledge_base"
            ]
        )
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize clients
        self.anthropic = Anthropic(api_key=api_keys.get("anthropic"))
        self.translator = Translator()
        
        # Initialize NLTK for sentiment analysis
        try:
            nltk.download('vader_lexicon', quiet=True)
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
        except Exception as e:
            logger.error(f"Failed to initialize sentiment analyzer: {e}")
            self.sentiment_analyzer = None
        
        # Set supported languages
        self.supported_languages = supported_languages or [
            "en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh-cn", "ru"
        ]
        
        # Initialize database connection
        self.db_config = db_config
        
        # Enhanced tools
        self.tools = [
            # ... (previous tools) ...
            {
                "name": "analyze_sentiment",
                "description": "Analyzes the sentiment of customer messages.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to analyze."
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "translate_message",
                "description": "Translates text between languages.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to translate."
                        },
                        "target_language": {
                            "type": "string",
                            "description": "Target language code."
                        }
                    },
                    "required": ["text", "target_language"]
                }
            },
            {
                "name": "schedule_followup",
                "description": "Schedules an automated follow-up.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Customer ID."
                        },
                        "issue_type": {
                            "type": "string",
                            "description": "Type of issue."
                        },
                        "followup_days": {
                            "type": "integer",
                            "description": "Days until follow-up."
                        }
                    },
                    "required": ["customer_id", "issue_type", "followup_days"]
                }
            },
            {
                "name": "send_satisfaction_survey",
                "description": "Sends a customer satisfaction survey.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Customer ID."
                        },
                        "interaction_id": {
                            "type": "string",
                            "description": "Interaction ID."
                        }
                    },
                    "required": ["customer_id", "interaction_id"]
                }
            },
            {
                "name": "escalate_issue",
                "description": "Escalates an issue to a higher support tier.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {
                            "type": "string",
                            "description": "Support ticket ID."
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for escalation."
                        },
                        "priority": {
                            "type": "string",
                            "description": "Priority level."
                        }
                    },
                    "required": ["ticket_id", "reason", "priority"]
                }
            },
            {
                "name": "search_knowledge_base",
                "description": "Searches the knowledge base for relevant articles.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query."
                        },
                        "category": {
                            "type": "string",
                            "description": "Article category."
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
        
        # Initialize synthetic data
        self._init_synthetic_data()
        
        # Initialize interaction history
        self.interaction_history = {}
        
        # Initialize follow-up queue
        self.followup_queue = []
        
        # Initialize satisfaction surveys
        self.satisfaction_surveys = {}
        
        # Initialize knowledge base
        self._init_knowledge_base()
    
    def _init_synthetic_data(self):
        """Initialize synthetic data including multi-language support"""
        # ... (previous synthetic data) ...
        
        # Add language preferences
        self.customer_languages = {
            "C1": "en",
            "C2": "es"
        }
        
        # Add interaction history
        self.interactions = {}
        
        # Add escalation tiers
        self.escalation_tiers = {
            "T1": "First Line Support",
            "T2": "Technical Support",
            "T3": "Senior Support",
            "T4": "Management"
        }
    
    def _init_knowledge_base(self):
        """Initialize knowledge base articles"""
        self.knowledge_base = {
            "returns": [
                {
                    "id": "KB001",
                    "title": "Return Policy",
                    "content": "Our return policy allows returns within 30 days...",
                    "category": "returns"
                }
            ],
            "shipping": [
                {
                    "id": "KB002",
                    "title": "Shipping Methods",
                    "content": "We offer standard and express shipping...",
                    "category": "shipping"
                }
            ],
            "technical": [
                {
                    "id": "KB003",
                    "title": "Product Troubleshooting",
                    "content": "Common solutions for technical issues...",
                    "category": "technical"
                }
            ]
        }
    
    async def process_task(self, task: Task) -> TaskResult:
        """Process enhanced customer service tasks"""
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
        """Handle customer inquiry with enhanced features"""
        # Detect language and translate if needed
        detected_lang = self.translator.detect(inquiry).lang
        translated_inquiry = inquiry
        if detected_lang != "en":
            translated_inquiry = self.translator.translate(inquiry, dest="en").text
        
        # Analyze sentiment
        sentiment = self.sentiment_analyzer.polarity_scores(translated_inquiry) if self.sentiment_analyzer else None
        
        # Process with Claude
        messages = [{"role": "user", "content": translated_inquiry}]
        response = await self.anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4096,
            tools=self.tools,
            messages=messages
        )
        
        # Process tool calls
        tool_results = []
        while response.stop_reason == "tool_use":
            tool_use = next(block for block in response.content if block.type == "tool_use")
            tool_result = await self._process_tool_call(tool_use.name, tool_use.input)
            tool_results.append({"tool": tool_use.name, "result": tool_result})
            
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
        
        # Translate response if needed
        if detected_lang != "en":
            final_response = self.translator.translate(
                final_response,
                dest=detected_lang
            ).text
        
        # Record interaction
        interaction_id = f"I{len(self.interactions) + 1}"
        self.interactions[interaction_id] = {
            "inquiry": inquiry,
            "detected_language": detected_lang,
            "sentiment": sentiment,
            "response": final_response,
            "tool_results": tool_results,
            "timestamp": datetime.now().isoformat()
        }
        
        # Schedule follow-up if sentiment is negative
        if sentiment and sentiment["compound"] < -0.5:
            self.followup_queue.append({
                "interaction_id": interaction_id,
                "scheduled_date": datetime.now() + timedelta(days=1),
                "priority": "high"
            })
        
        # Send satisfaction survey
        if parameters.get("customer_id"):
            survey_id = f"S{len(self.satisfaction_surveys) + 1}"
            self.satisfaction_surveys[survey_id] = {
                "customer_id": parameters["customer_id"],
                "interaction_id": interaction_id,
                "status": "sent",
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "response": final_response,
            "language": detected_lang,
            "sentiment": sentiment,
            "interaction_id": interaction_id,
            "tools_used": [result["tool"] for result in tool_results],
            "timestamp": datetime.now().isoformat()
        }
    
    async def _process_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """Process enhanced tool calls"""
        if tool_name == "analyze_sentiment":
            if self.sentiment_analyzer:
                return self.sentiment_analyzer.polarity_scores(tool_input["text"])
            return {"error": "Sentiment analyzer not initialized"}
        
        elif tool_name == "translate_message":
            translation = self.translator.translate(
                tool_input["text"],
                dest=tool_input["target_language"]
            )
            return {
                "translated_text": translation.text,
                "source_language": translation.src,
                "target_language": translation.dest
            }
        
        elif tool_name == "schedule_followup":
            followup_id = f"F{len(self.followup_queue) + 1}"
            followup = {
                "id": followup_id,
                "customer_id": tool_input["customer_id"],
                "issue_type": tool_input["issue_type"],
                "scheduled_date": datetime.now() + timedelta(days=tool_input["followup_days"]),
                "status": "scheduled"
            }
            self.followup_queue.append(followup)
            return {"followup_id": followup_id}
        
        elif tool_name == "send_satisfaction_survey":
            survey_id = f"S{len(self.satisfaction_surveys) + 1}"
            survey = {
                "id": survey_id,
                "customer_id": tool_input["customer_id"],
                "interaction_id": tool_input["interaction_id"],
                "status": "sent",
                "timestamp": datetime.now().isoformat()
            }
            self.satisfaction_surveys[survey_id] = survey
            return {"survey_id": survey_id}
        
        elif tool_name == "escalate_issue":
            ticket = self.support_tickets.get(tool_input["ticket_id"])
            if ticket:
                ticket["escalated"] = True
                ticket["escalation_reason"] = tool_input["reason"]
                ticket["priority"] = tool_input["priority"]
                ticket["escalation_timestamp"] = datetime.now().isoformat()
                return {"success": True, "ticket": ticket}
            return {"success": False, "message": "Ticket not found"}
        
        elif tool_name == "search_knowledge_base":
            category = tool_input.get("category")
            articles = []
            if category:
                articles = self.knowledge_base.get(category, [])
            else:
                articles = [
                    article
                    for category_articles in self.knowledge_base.values()
                    for article in category_articles
                ]
            
            # Simple keyword matching (in real system, use proper search)
            matching_articles = [
                article for article in articles
                if tool_input["query"].lower() in article["content"].lower()
            ]
            return matching_articles
        
        else:
            # Handle basic tools from parent class
            return await super()._process_tool_call(tool_name, tool_input)
    
    async def handle_message(self, message: Message) -> Optional[Message]:
        """Handle enhanced messages"""
        if message.message_type == "customer_service_status":
            return Message(
                sender=self.agent_id,
                content={
                    "active_tickets": len([t for t in self.support_tickets.values() if t["status"] == "Open"]),
                    "pending_followups": len(self.followup_queue),
                    "sent_surveys": len(self.satisfaction_surveys),
                    "supported_languages": self.supported_languages,
                    "capabilities": self.capabilities
                },
                message_type="customer_service_status_response"
            )
        return None
    
    async def process_followups(self):
        """Process pending follow-ups"""
        current_time = datetime.now()
        pending_followups = [
            f for f in self.followup_queue
            if f["scheduled_date"] <= current_time and f["status"] == "scheduled"
        ]
        
        for followup in pending_followups:
            # Create follow-up task
            task = Task(
                task_id=f"followup_{followup['id']}",
                task_type="customer_inquiry",
                input_data=f"Following up on your previous issue ({followup['issue_type']}). Has it been resolved to your satisfaction?",
                parameters={"customer_id": followup["customer_id"]}
            )
            
            # Process follow-up
            result = await self.process_task(task)
            
            # Update followup status
            followup["status"] = "completed"
            followup["result"] = result.output
    
    async def cleanup(self):
        """Cleanup resources"""
        # Process any remaining follow-ups
        await self.process_followups()
        
        # Close any open tickets that are resolved
        for ticket in self.support_tickets.values():
            if ticket["status"] == "Open" and datetime.now() - datetime.fromisoformat(ticket["created_at"]) > timedelta(days=7):
                ticket["status"] = "Closed"
                ticket["closed_at"] = datetime.now().isoformat()
        
        # Archive old interactions
        cutoff_date = datetime.now() - timedelta(days=30)
        archived_interactions = {
            k: v for k, v in self.interactions.items()
            if datetime.fromisoformat(v["timestamp"]) < cutoff_date
        }
        
        # Save archives
        archive_file = self.work_dir / f"interactions_archive_{datetime.now().strftime('%Y%m')}.json"
        with open(archive_file, "w") as f:
            json.dump(archived_interactions, f, indent=2)
