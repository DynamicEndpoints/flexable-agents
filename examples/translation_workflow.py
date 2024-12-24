import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json
import pandas as pd

from src.core.base import Task, AgentSystem, Message
from src.agents.translation_agent import TranslationAgent
from src.agents.file_processor import FileProcessingAgent
from src.agents.db_agent import DatabaseAgent
from src.agents.monitoring_agent import MonitoringAgent
from src.agents.ml_agent import MLAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_monitoring(system: AgentSystem, monitor_agent: MonitoringAgent):
    """Setup monitoring for translation workflow"""
    alert_config = {
        "translation_time": {
            "condition": "duration > 300",  # Alert if translation takes more than 5 minutes
            "severity": "warning",
            "notification": {"method": "log"}
        },
        "quality_score": {
            "condition": "score < 0.8",  # Alert if translation quality below 80%
            "severity": "warning",
            "notification": {"method": "log"}
        },
        "error_rate": {
            "condition": "errors > 5",  # Alert if more than 5 errors in batch
            "severity": "critical",
            "notification": {"method": "log"}
        }
    }
    
    await monitor_agent.handle_message(Message(
        sender="system",
        content=alert_config,
        message_type="alert_config"
    ))

async def document_translation_workflow(
    system: AgentSystem,
    translation_agent: TranslationAgent,
    file_agent: FileProcessingAgent,
    db_agent: DatabaseAgent,
    ml_agent: MLAgent,
    monitor_agent: MonitoringAgent
):
    """Complex document translation and analysis workflow"""
    
    # Step 1: Process input documents
    input_task = Task(
        task_id="process_inputs",
        task_type="batch_process",
        input_data="data/input_documents",
        parameters={
            "file_types": [".pdf", ".docx", ".txt"],
            "recursive": True
        },
        deadline=datetime.now() + timedelta(minutes=10)
    )
    
    system.submit_task(input_task)
    while not system.get_task_result("process_inputs"):
        await asyncio.sleep(0.1)
    
    input_result = system.get_task_result("process_inputs")
    if input_result.status == "failed":
        logger.error(f"Failed to process input documents: {input_result.error}")
        return
    
    documents = input_result.output["files"]
    
    # Step 2: Detect languages and group documents
    language_tasks = []
    for doc in documents:
        task = Task(
            task_id=f"detect_lang_{doc}",
            task_type="language_detection",
            input_data=doc,
            parameters={},
            deadline=datetime.now() + timedelta(minutes=5)
        )
        language_tasks.append(task)
        system.submit_task(task)
    
    # Wait for language detection
    lang_results = {}
    for task in language_tasks:
        while not system.get_task_result(task.task_id):
            await asyncio.sleep(0.1)
        result = system.get_task_result(task.task_id)
        if result.status == "success":
            lang_results[task.input_data] = result.output
    
    # Group documents by source language
    grouped_docs = {}
    for doc, lang in lang_results.items():
        if lang not in grouped_docs:
            grouped_docs[lang] = []
        grouped_docs[lang].append(doc)
    
    # Step 3: Batch translation for each language group
    translation_results = []
    for source_lang, docs in grouped_docs.items():
        batch_task = Task(
            task_id=f"translate_batch_{source_lang}",
            task_type="batch_translation",
            input_data=docs,
            parameters={
                "source_lang": source_lang,
                "target_lang": "en",  # Translating everything to English
                "service": "deepl",
                "preserve_formatting": True
            },
            deadline=datetime.now() + timedelta(hours=1)
        )
        
        system.submit_task(batch_task)
        while not system.get_task_result(batch_task.task_id):
            await asyncio.sleep(0.1)
        
        result = system.get_task_result(batch_task.task_id)
        if result.status == "success":
            translation_results.extend(result.output["successful_translations"])
    
    # Step 4: Quality assessment
    quality_results = []
    for trans in translation_results:
        quality_task = Task(
            task_id=f"quality_{trans['original']}",
            task_type="quality_check",
            input_data={
                "original": trans["original"],
                "translated": trans["translated"]
            },
            parameters={
                "source_lang": lang_results[trans["original"]],
                "target_lang": "en"
            },
            deadline=datetime.now() + timedelta(minutes=10)
        )
        
        system.submit_task(quality_task)
        while not system.get_task_result(quality_task.task_id):
            await asyncio.sleep(0.1)
        
        result = system.get_task_result(quality_task.task_id)
        if result.status == "success":
            quality_results.append(result.output)
    
    # Step 5: Extract insights using ML
    ml_task = Task(
        task_id="analyze_translations",
        task_type="text_analysis",
        input_data={
            "translations": translation_results,
            "quality_scores": quality_results
        },
        parameters={
            "analysis_types": ["sentiment", "topic", "complexity"]
        },
        deadline=datetime.now() + timedelta(minutes=30)
    )
    
    system.submit_task(ml_task)
    while not system.get_task_result("analyze_translations"):
        await asyncio.sleep(0.1)
    
    analysis_result = system.get_task_result("analyze_translations")
    
    # Step 6: Store results in database
    store_task = Task(
        task_id="store_results",
        task_type="batch_insert",
        input_data={
            "translations": [{
                "original_file": t["original"],
                "translated_file": t["translated"],
                "source_language": lang_results[t["original"]],
                "target_language": "en",
                "quality_score": next(q["overall_score"] for q in quality_results 
                                   if q["original_file"] == t["original"]),
                "translation_date": datetime.now().isoformat()
            } for t in translation_results],
            "analysis": analysis_result.output
        },
        parameters={
            "table": "translation_projects",
            "batch_size": 100
        },
        deadline=datetime.now() + timedelta(minutes=5)
    )
    
    system.submit_task(store_task)
    while not system.get_task_result("store_results"):
        await asyncio.sleep(0.1)
    
    store_result = system.get_task_result("store_results")
    
    # Generate summary report
    summary = {
        "total_documents": len(documents),
        "languages_processed": list(grouped_docs.keys()),
        "successful_translations": len([t for t in translation_results if t["success"]]),
        "failed_translations": len([t for t in translation_results if not t["success"]]),
        "average_quality_score": sum(q["overall_score"] for q in quality_results) / len(quality_results),
        "analysis_summary": analysis_result.output["summary"] if analysis_result.status == "success" else None,
        "completion_time": datetime.now().isoformat()
    }
    
    return summary

async def main():
    # Initialize the agent system
    system = AgentSystem()
    
    # Create work directories
    work_dir = Path("work_files")
    translation_dir = work_dir / "translations"
    model_dir = work_dir / "models"
    log_dir = work_dir / "logs"
    for dir_path in [work_dir, translation_dir, model_dir, log_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize agents
    translation_agent = TranslationAgent(
        agent_id="translator_1",
        work_dir=str(translation_dir),
        api_keys={
            "deepl": "your_deepl_key",
            "anthropic": "your_anthropic_key"
        }
    )
    
    file_agent = FileProcessingAgent(
        agent_id="file_processor_1",
        work_dir=str(work_dir)
    )
    
    db_agent = DatabaseAgent(
        agent_id="db_agent_1",
        connection_params={
            "host": "localhost",
            "port": 5432,
            "user": "user",
            "password": "password",
            "database": "translations_db"
        }
    )
    
    ml_agent = MLAgent(
        agent_id="ml_agent_1",
        model_dir=str(model_dir)
    )
    
    monitor_agent = MonitoringAgent(
        agent_id="monitor_1",
        log_dir=str(log_dir)
    )
    
    # Register all agents
    for agent in [translation_agent, file_agent, db_agent, ml_agent, monitor_agent]:
        system.register_agent(agent)
    
    # Setup monitoring
    await setup_monitoring(system, monitor_agent)
    
    # Run the workflow
    summary = await document_translation_workflow(
        system,
        translation_agent,
        file_agent,
        db_agent,
        ml_agent,
        monitor_agent
    )
    
    # Save workflow summary
    with open(work_dir / "workflow_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    logger.info("Translation workflow completed successfully!")
    logger.info(f"Summary: {json.dumps(summary, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
