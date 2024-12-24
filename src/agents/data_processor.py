from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
from datetime import datetime

from ..core.base import Agent, Task, TaskResult, Message
from ..utils.helpers import Timer, chunk_list

class DataProcessingAgent(Agent):
    """Agent for processing and analyzing data"""
    
    def __init__(self, agent_id: str):
        super().__init__(
            agent_id=agent_id,
            capabilities=[
                "data_analysis",
                "data_transformation",
                "data_validation",
                "statistical_analysis"
            ]
        )
        self.processing_history: List[Dict[str, Any]] = []
        
    async def process_task(self, task: Task) -> TaskResult:
        """Process data-related tasks"""
        with Timer(f"Data task {task.task_id}") as timer:
            try:
                if task.task_type == "data_analysis":
                    output = self._analyze_data(task.input_data)
                elif task.task_type == "data_transformation":
                    output = self._transform_data(task.input_data, task.parameters)
                elif task.task_type == "data_validation":
                    output = self._validate_data(task.input_data, task.parameters)
                elif task.task_type == "statistical_analysis":
                    output = self._statistical_analysis(task.input_data)
                else:
                    raise ValueError(f"Unsupported task type: {task.task_type}")
                
                # Record processing history
                self.processing_history.append({
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "timestamp": datetime.now(),
                    "processing_time": timer.duration
                })
                
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    output=output,
                    processing_time=timer.duration,
                    agent_id=self.agent_id,
                    metadata={"history_length": len(self.processing_history)}
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
                content={
                    "status": self.status,
                    "tasks_processed": len(self.processing_history),
                    "capabilities": self.capabilities
                },
                message_type="status_response"
            )
        elif message.message_type == "history_request":
            return Message(
                sender=self.agent_id,
                content=self.processing_history,
                message_type="history_response"
            )
        return None
    
    def _analyze_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze a pandas DataFrame"""
        analysis = {
            "shape": data.shape,
            "columns": list(data.columns),
            "missing_values": data.isnull().sum().to_dict(),
            "data_types": data.dtypes.astype(str).to_dict(),
            "numeric_summary": data.describe().to_dict() if not data.empty else {},
            "correlation": data.corr().to_dict() if not data.empty else {}
        }
        return analysis
    
    def _transform_data(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> pd.DataFrame:
        """Transform data based on parameters"""
        df = data.copy()
        
        if parameters.get("normalize", False):
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = (df[numeric_cols] - df[numeric_cols].mean()) / df[numeric_cols].std()
            
        if parameters.get("fill_missing"):
            strategy = parameters["fill_missing"]
            if strategy == "mean":
                df = df.fillna(df.mean())
            elif strategy == "median":
                df = df.fillna(df.median())
            elif strategy == "mode":
                df = df.fillna(df.mode().iloc[0])
                
        if parameters.get("drop_columns"):
            df = df.drop(columns=parameters["drop_columns"])
            
        return df
    
    def _validate_data(self, data: pd.DataFrame, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against a set of rules"""
        validation_results = {
            "passed": True,
            "violations": []
        }
        
        for column, rule in rules.items():
            if column not in data.columns:
                validation_results["violations"].append(f"Column {column} not found")
                validation_results["passed"] = False
                continue
                
            if "type" in rule:
                if not all(isinstance(x, eval(rule["type"])) for x in data[column].dropna()):
                    validation_results["violations"].append(
                        f"Column {column} contains invalid types"
                    )
                    validation_results["passed"] = False
                    
            if "range" in rule:
                min_val, max_val = rule["range"]
                if not all(min_val <= x <= max_val for x in data[column].dropna()):
                    validation_results["violations"].append(
                        f"Column {column} contains values outside range [{min_val}, {max_val}]"
                    )
                    validation_results["passed"] = False
                    
            if "unique" in rule and rule["unique"]:
                if not data[column].is_unique:
                    validation_results["violations"].append(
                        f"Column {column} contains duplicate values"
                    )
                    validation_results["passed"] = False
                    
        return validation_results
    
    def _statistical_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform statistical analysis on data"""
        numeric_data = data.select_dtypes(include=[np.number])
        
        analysis = {
            "basic_stats": data.describe().to_dict(),
            "correlation_matrix": numeric_data.corr().to_dict(),
            "skewness": numeric_data.skew().to_dict(),
            "kurtosis": numeric_data.kurtosis().to_dict(),
            "missing_percentage": (data.isnull().sum() / len(data) * 100).to_dict()
        }
        
        # Add categorical column analysis
        categorical_cols = data.select_dtypes(include=['object', 'category']).columns
        if not categorical_cols.empty:
            analysis["categorical_analysis"] = {
                col: data[col].value_counts().to_dict()
                for col in categorical_cols
            }
            
        return analysis
