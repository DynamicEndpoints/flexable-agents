import asyncio
import logging
from datetime import datetime, timedelta
import pandas as pd
import json
from pathlib import Path

from src.core.base import Task, AgentSystem
from src.agents.data_processor import DataProcessingAgent
from src.agents.api_agent import APIAgent
from src.agents.file_processor import FileProcessingAgent
from src.agents.ml_agent import MLAgent
from src.agents.db_agent import DatabaseAgent
from src.agents.monitoring_agent import MonitoringAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_monitoring(system: AgentSystem, monitor_agent: MonitoringAgent):
    """Setup monitoring configuration"""
    # Configure alert rules
    alert_config = {
        "cpu_usage": {
            "condition": "cpu.percent",
            "threshold": 80,
            "severity": "warning",
            "notification": {
                "method": "log"
            }
        },
        "memory_usage": {
            "condition": "memory.percent",
            "threshold": 90,
            "severity": "critical",
            "notification": {
                "method": "log"
            }
        }
    }
    
    await monitor_agent.handle_message(Message(
        sender="system",
        content=alert_config,
        message_type="alert_config"
    ))
    
    # Start monitoring task
    monitoring_task = Task(
        task_id="system_monitoring",
        task_type="system_metrics",
        priority=1,
        input_data=None,
        parameters={},
        deadline=None  # Continuous monitoring
    )
    
    system.submit_task(monitoring_task)

async def data_processing_workflow(
    system: AgentSystem,
    data_agent: DataProcessingAgent,
    ml_agent: MLAgent,
    db_agent: DatabaseAgent,
    file_agent: FileProcessingAgent
):
    """Complex data processing and ML workflow"""
    
    # Step 1: Load and preprocess data
    load_task = Task(
        task_id="load_data",
        task_type="file_read",
        priority=1,
        input_data="data/raw_data.csv",
        parameters={"file_type": "csv"},
        deadline=datetime.now() + timedelta(minutes=5)
    )
    
    system.submit_task(load_task)
    while not system.get_task_result("load_data"):
        await asyncio.sleep(0.1)
    
    load_result = system.get_task_result("load_data")
    if load_result.status == "failed":
        logger.error(f"Failed to load data: {load_result.error}")
        return
    
    # Step 2: Process and validate data
    data = pd.DataFrame(load_result.output)
    
    validation_task = Task(
        task_id="validate_data",
        task_type="data_validation",
        priority=2,
        input_data=data,
        parameters={
            "rules": {
                "age": {"type": "int", "range": [0, 120]},
                "income": {"type": "float", "range": [0, 1000000]},
                "email": {"type": "str", "unique": True}
            }
        },
        deadline=datetime.now() + timedelta(minutes=5)
    )
    
    system.submit_task(validation_task)
    while not system.get_task_result("validate_data"):
        await asyncio.sleep(0.1)
    
    validation_result = system.get_task_result("validate_data")
    if not validation_result.output["passed"]:
        logger.error(f"Data validation failed: {validation_result.output['violations']}")
        return
    
    # Step 3: Prepare data for ML
    prep_task = Task(
        task_id="prepare_data",
        task_type="data_preprocessing",
        priority=3,
        input_data=data,
        parameters={
            "handle_missing": True,
            "missing_strategy": "mean",
            "handle_categorical": True,
            "scale_features": True
        },
        deadline=datetime.now() + timedelta(minutes=10)
    )
    
    system.submit_task(prep_task)
    while not system.get_task_result("prepare_data"):
        await asyncio.sleep(0.1)
    
    prep_result = system.get_task_result("prepare_data")
    if prep_result.status == "failed":
        logger.error(f"Data preparation failed: {prep_result.error}")
        return
    
    processed_data = prep_result.output["processed_data"]
    
    # Step 4: Train ML model
    train_task = Task(
        task_id="train_model",
        task_type="train_model",
        priority=4,
        input_data=processed_data,
        parameters={
            "model_type": "random_forest_classifier",
            "target_column": "target",
            "model_params": {
                "n_estimators": 100,
                "max_depth": 10
            }
        },
        deadline=datetime.now() + timedelta(minutes=30)
    )
    
    system.submit_task(train_task)
    while not system.get_task_result("train_model"):
        await asyncio.sleep(0.1)
    
    train_result = system.get_task_result("train_model")
    if train_result.status == "failed":
        logger.error(f"Model training failed: {train_result.error}")
        return
    
    # Step 5: Analyze feature importance
    importance_task = Task(
        task_id="feature_importance",
        task_type="feature_importance",
        priority=5,
        input_data=None,
        parameters={"model_id": train_result.output["model_id"]},
        deadline=datetime.now() + timedelta(minutes=5)
    )
    
    system.submit_task(importance_task)
    while not system.get_task_result("feature_importance"):
        await asyncio.sleep(0.1)
    
    importance_result = system.get_task_result("feature_importance")
    
    # Step 6: Store results in database
    store_task = Task(
        task_id="store_results",
        task_type="execute",
        priority=6,
        input_data="""
            INSERT INTO model_results 
            (model_id, train_score, test_score, feature_importance)
            VALUES ($1, $2, $3, $4)
        """,
        parameters={
            "params": [
                train_result.output["model_id"],
                train_result.output["train_score"],
                train_result.output["test_score"],
                json.dumps(importance_result.output["feature_importance"])
            ]
        },
        deadline=datetime.now() + timedelta(minutes=5)
    )
    
    system.submit_task(store_task)
    while not system.get_task_result("store_results"):
        await asyncio.sleep(0.1)
    
    store_result = system.get_task_result("store_results")
    if store_result.status == "failed":
        logger.error(f"Failed to store results: {store_result.error}")
        return
    
    # Step 7: Save processed data and results
    save_task = Task(
        task_id="save_results",
        task_type="file_write",
        priority=7,
        input_data={
            "model_performance": {
                "train_score": train_result.output["train_score"],
                "test_score": train_result.output["test_score"]
            },
            "feature_importance": importance_result.output["feature_importance"]
        },
        parameters={
            "file_path": "results/model_analysis.json",
            "file_type": "json"
        },
        deadline=datetime.now() + timedelta(minutes=5)
    )
    
    system.submit_task(save_task)
    while not system.get_task_result("save_results"):
        await asyncio.sleep(0.1)
    
    save_result = system.get_task_result("save_results")
    if save_result.status == "failed":
        logger.error(f"Failed to save results: {save_result.error}")
        return
    
    logger.info("Data processing and ML workflow completed successfully!")

async def main():
    # Initialize the agent system
    system = AgentSystem()
    
    # Create work directories
    work_dir = Path("work_files")
    model_dir = work_dir / "models"
    log_dir = work_dir / "logs"
    for dir_path in [work_dir, model_dir, log_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Create and register agents
    data_agent = DataProcessingAgent("data_agent_1")
    api_agent = APIAgent(
        "api_agent_1",
        base_url="https://api.example.com",
        api_key="your_api_key"
    )
    file_agent = FileProcessingAgent("file_agent_1", str(work_dir))
    ml_agent = MLAgent("ml_agent_1", str(model_dir))
    db_agent = DatabaseAgent(
        "db_agent_1",
        connection_params={
            "host": "localhost",
            "port": 5432,
            "user": "user",
            "password": "password",
            "database": "mydb"
        }
    )
    monitor_agent = MonitoringAgent("monitor_agent_1", str(log_dir))
    
    # Register all agents
    for agent in [data_agent, api_agent, file_agent, ml_agent, db_agent, monitor_agent]:
        system.register_agent(agent)
    
    # Setup monitoring
    await setup_monitoring(system, monitor_agent)
    
    # Run the main workflow
    await data_processing_workflow(system, data_agent, ml_agent, db_agent, file_agent)
    
    # Cleanup
    if hasattr(api_agent, 'cleanup'):
        await api_agent.cleanup()
    if hasattr(db_agent, 'cleanup'):
        await db_agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
