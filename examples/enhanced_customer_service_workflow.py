import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, List

from src.core.base import Task, AgentSystem, Message
from src.agents.enhanced_customer_service_agent import EnhancedCustomerServiceAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_multilingual_inquiries(
    system: AgentSystem,
    agent: EnhancedCustomerServiceAgent,
    inquiries: List[Dict[str, str]]
) -> Dict[str, Any]:
    """Process customer inquiries in multiple languages"""
    results = []
    
    for idx, inquiry in enumerate(inquiries, 1):
        logger.info(f"Processing inquiry {idx} in {inquiry['language']}")
        
        task = Task(
            task_id=f"inquiry_{idx}",
            task_type="customer_inquiry",
            input_data=inquiry["text"],
            parameters={
                "customer_id": inquiry.get("customer_id"),
                "language": inquiry["language"]
            }
        )
        
        system.submit_task(task)
        while not system.get_task_result(task.task_id):
            await asyncio.sleep(0.1)
        
        result = system.get_task_result(task.task_id)
        if result.status == "success":
            results.append({
                "inquiry": inquiry,
                "response": result.output["response"],
                "detected_language": result.output["language"],
                "sentiment": result.output["sentiment"],
                "interaction_id": result.output["interaction_id"],
                "tools_used": result.output["tools_used"],
                "timestamp": result.output["timestamp"]
            })
            logger.info(f"Successfully processed inquiry {idx}")
        else:
            logger.error(f"Failed to process inquiry {idx}: {result.error}")
    
    return results

async def handle_negative_sentiment(
    system: AgentSystem,
    agent: EnhancedCustomerServiceAgent,
    interaction_id: str,
    sentiment: Dict[str, float]
) -> Dict[str, Any]:
    """Handle interactions with negative sentiment"""
    logger.info(f"Handling negative sentiment for interaction {interaction_id}")
    
    # Create support ticket
    ticket_task = Task(
        task_id=f"ticket_{interaction_id}",
        task_type="create_support_ticket",
        input_data={
            "customer_id": "C1",  # Example customer ID
            "issue_type": "customer_satisfaction",
            "description": f"Negative sentiment detected in interaction {interaction_id}. Sentiment scores: {sentiment}"
        }
    )
    
    system.submit_task(ticket_task)
    while not system.get_task_result(ticket_task.task_id):
        await asyncio.sleep(0.1)
    
    ticket_result = system.get_task_result(ticket_task.task_id)
    
    # Schedule priority follow-up
    followup_task = Task(
        task_id=f"followup_{interaction_id}",
        task_type="schedule_followup",
        input_data={
            "customer_id": "C1",
            "issue_type": "satisfaction",
            "followup_days": 1
        }
    )
    
    system.submit_task(followup_task)
    while not system.get_task_result(followup_task.task_id):
        await asyncio.sleep(0.1)
    
    followup_result = system.get_task_result(followup_task.task_id)
    
    return {
        "ticket": ticket_result.output,
        "followup": followup_result.output
    }

async def search_relevant_articles(
    system: AgentSystem,
    agent: EnhancedCustomerServiceAgent,
    inquiry: str
) -> List[Dict[str, Any]]:
    """Search knowledge base for relevant articles"""
    search_task = Task(
        task_id=f"kb_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        task_type="search_knowledge_base",
        input_data={
            "query": inquiry
        }
    )
    
    system.submit_task(search_task)
    while not system.get_task_result(search_task.task_id):
        await asyncio.sleep(0.1)
    
    result = system.get_task_result(search_task.task_id)
    return result.output

def generate_analytics(results: List[Dict[str, Any]], output_dir: Path):
    """Generate analytics and visualizations"""
    # Convert results to DataFrame
    df = pd.DataFrame(results)
    
    # Sentiment analysis over time
    plt.figure(figsize=(12, 6))
    sentiment_scores = pd.DataFrame([r["sentiment"] for r in results])
    sentiment_scores["timestamp"] = pd.to_datetime([r["timestamp"] for r in results])
    plt.plot(sentiment_scores["timestamp"], sentiment_scores["compound"], marker='o')
    plt.title("Sentiment Trends Over Time")
    plt.xlabel("Time")
    plt.ylabel("Compound Sentiment Score")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "sentiment_trends.png")
    plt.close()
    
    # Language distribution
    plt.figure(figsize=(10, 6))
    language_counts = df["detected_language"].value_counts()
    sns.barplot(x=language_counts.index, y=language_counts.values)
    plt.title("Distribution of Customer Languages")
    plt.xlabel("Language")
    plt.ylabel("Count")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "language_distribution.png")
    plt.close()
    
    # Tool usage analysis
    tool_counts = {}
    for r in results:
        for tool in r["tools_used"]:
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
    
    plt.figure(figsize=(12, 6))
    sns.barplot(x=list(tool_counts.keys()), y=list(tool_counts.values()))
    plt.title("Tool Usage Distribution")
    plt.xlabel("Tool")
    plt.ylabel("Usage Count")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "tool_usage.png")
    plt.close()
    
    # Generate summary statistics
    summary = {
        "total_interactions": len(results),
        "language_distribution": language_counts.to_dict(),
        "average_sentiment": sentiment_scores["compound"].mean(),
        "negative_interactions": len(sentiment_scores[sentiment_scores["compound"] < -0.5]),
        "tool_usage": tool_counts,
        "timestamp": datetime.now().isoformat()
    }
    
    return summary

async def enhanced_customer_service_workflow(
    system: AgentSystem,
    agent: EnhancedCustomerServiceAgent,
    output_dir: Path
) -> Dict[str, Any]:
    """Run enhanced customer service workflow"""
    
    # Example multi-language inquiries
    inquiries = [
        {
            "text": "What's the status of my order O2?",
            "language": "en",
            "customer_id": "C1"
        },
        {
            "text": "¿Cómo puedo devolver mi pedido O1?",
            "language": "es",
            "customer_id": "C2"
        },
        {
            "text": "Comment puis-je annuler ma commande O2?",
            "language": "fr",
            "customer_id": "C1"
        },
        {
            "text": "Wo ist meine Bestellung O1?",
            "language": "de",
            "customer_id": "C2"
        },
        {
            "text": "This product is terrible! I want a refund!",
            "language": "en",
            "customer_id": "C1"
        }
    ]
    
    # Process inquiries
    logger.info("Processing multi-language inquiries...")
    results = await process_multilingual_inquiries(system, agent, inquiries)
    
    # Handle negative sentiments
    logger.info("Handling negative sentiments...")
    for result in results:
        if result["sentiment"]["compound"] < -0.5:
            await handle_negative_sentiment(
                system,
                agent,
                result["interaction_id"],
                result["sentiment"]
            )
    
    # Search knowledge base for each inquiry
    logger.info("Searching knowledge base...")
    kb_results = {}
    for inquiry in inquiries:
        articles = await search_relevant_articles(system, agent, inquiry["text"])
        kb_results[inquiry["text"]] = articles
    
    # Process scheduled follow-ups
    logger.info("Processing follow-ups...")
    await agent.process_followups()
    
    # Generate analytics
    logger.info("Generating analytics...")
    analytics = generate_analytics(results, output_dir)
    
    # Save results
    workflow_results = {
        "interactions": results,
        "knowledge_base_results": kb_results,
        "analytics": analytics,
        "timestamp": datetime.now().isoformat()
    }
    
    results_file = output_dir / f"workflow_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(workflow_results, f, indent=2, ensure_ascii=False)
    
    return workflow_results

async def main():
    # Initialize agent system
    system = AgentSystem()
    
    # Create work directories
    work_dir = Path("work_files")
    cs_dir = work_dir / "customer_service"
    analytics_dir = cs_dir / "analytics"
    
    for dir_path in [work_dir, cs_dir, analytics_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize enhanced customer service agent
    cs_agent = EnhancedCustomerServiceAgent(
        agent_id="enhanced_cs_1",
        work_dir=str(cs_dir),
        api_keys={
            "anthropic": "your_anthropic_key"
        }
    )
    
    # Register agent
    system.register_agent(cs_agent)
    
    # Run workflow
    results = await enhanced_customer_service_workflow(
        system,
        cs_agent,
        analytics_dir
    )
    
    # Log summary
    logger.info("\nWorkflow Summary:")
    logger.info(f"Total Interactions: {results['analytics']['total_interactions']}")
    logger.info(f"Language Distribution: {results['analytics']['language_distribution']}")
    logger.info(f"Average Sentiment: {results['analytics']['average_sentiment']:.2f}")
    logger.info(f"Negative Interactions: {results['analytics']['negative_interactions']}")
    logger.info(f"Most Used Tools: {dict(sorted(results['analytics']['tool_usage'].items(), key=lambda x: x[1], reverse=True))}")
    logger.info(f"\nAnalytics saved to: {analytics_dir}")

if __name__ == "__main__":
    asyncio.run(main())
