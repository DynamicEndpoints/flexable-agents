from typing import Optional, Dict, Any, List, Union
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_squared_error, classification_report
import joblib
from datetime import datetime
import pickle
from pathlib import Path

from ..core.base import Agent, Task, TaskResult, Message
from ..utils.helpers import Timer

class MLAgent(Agent):
    """Agent for machine learning tasks"""
    
    def __init__(self, agent_id: str, model_dir: str):
        super().__init__(
            agent_id=agent_id,
            capabilities=[
                "train_model",
                "predict",
                "evaluate_model",
                "feature_importance",
                "model_optimization",
                "data_preprocessing"
            ]
        )
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.models: Dict[str, Any] = {}
        self.model_metrics: Dict[str, Dict[str, Any]] = {}
        self.preprocessing_pipeline: Dict[str, Any] = {}
        
    async def process_task(self, task: Task) -> TaskResult:
        """Process machine learning tasks"""
        with Timer(f"ML task {task.task_id}") as timer:
            try:
                if task.task_type == "train_model":
                    output = self._train_model(task.input_data, task.parameters)
                elif task.task_type == "predict":
                    output = self._make_predictions(task.input_data, task.parameters)
                elif task.task_type == "evaluate_model":
                    output = self._evaluate_model(task.input_data, task.parameters)
                elif task.task_type == "feature_importance":
                    output = self._analyze_feature_importance(task.input_data, task.parameters)
                elif task.task_type == "model_optimization":
                    output = self._optimize_model(task.input_data, task.parameters)
                elif task.task_type == "data_preprocessing":
                    output = self._preprocess_data(task.input_data, task.parameters)
                else:
                    raise ValueError(f"Unsupported task type: {task.task_type}")
                
                return TaskResult(
                    task_id=task.task_id,
                    status="success",
                    output=output,
                    processing_time=timer.duration,
                    agent_id=self.agent_id,
                    metadata={"model_type": task.parameters.get("model_type")}
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
        if message.message_type == "model_status":
            return Message(
                sender=self.agent_id,
                content={
                    "active_models": list(self.models.keys()),
                    "model_metrics": self.model_metrics
                },
                message_type="model_status_response"
            )
        elif message.message_type == "save_model_request":
            model_id = message.content.get("model_id")
            if model_id in self.models:
                self._save_model(model_id)
                return Message(
                    sender=self.agent_id,
                    content={"status": "saved", "model_id": model_id},
                    message_type="save_model_response"
                )
        return None
    
    def _train_model(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Train a machine learning model"""
        model_type = parameters["model_type"]
        model_id = parameters.get("model_id", f"{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        target_column = parameters["target_column"]
        
        # Split features and target
        X = data.drop(columns=[target_column])
        y = data[target_column]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=parameters.get("test_size", 0.2),
            random_state=parameters.get("random_state", 42)
        )
        
        # Preprocess data
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        if model_type == "random_forest_classifier":
            model = RandomForestClassifier(**parameters.get("model_params", {}))
        elif model_type == "random_forest_regressor":
            model = RandomForestRegressor(**parameters.get("model_params", {}))
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        model.fit(X_train_scaled, y_train)
        
        # Save model and preprocessing
        self.models[model_id] = model
        self.preprocessing_pipeline[model_id] = {
            "scaler": scaler,
            "feature_columns": list(X.columns)
        }
        
        # Evaluate model
        train_score = model.score(X_train_scaled, y_train)
        test_score = model.score(X_test_scaled, y_test)
        
        self.model_metrics[model_id] = {
            "train_score": train_score,
            "test_score": test_score,
            "model_type": model_type,
            "training_date": datetime.now().isoformat()
        }
        
        return {
            "model_id": model_id,
            "train_score": train_score,
            "test_score": test_score,
            "feature_columns": list(X.columns)
        }
    
    def _make_predictions(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Make predictions using a trained model"""
        model_id = parameters["model_id"]
        
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
            
        model = self.models[model_id]
        preprocessing = self.preprocessing_pipeline[model_id]
        
        # Ensure data has required features
        required_features = preprocessing["feature_columns"]
        if not all(col in data.columns for col in required_features):
            raise ValueError("Input data missing required features")
            
        # Preprocess data
        X = data[required_features]
        X_scaled = preprocessing["scaler"].transform(X)
        
        # Make predictions
        predictions = model.predict(X_scaled)
        probabilities = None
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(X_scaled)
        
        return {
            "predictions": predictions.tolist(),
            "probabilities": probabilities.tolist() if probabilities is not None else None,
            "model_id": model_id
        }
    
    def _evaluate_model(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate model performance"""
        model_id = parameters["model_id"]
        target_column = parameters["target_column"]
        
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
            
        X = data.drop(columns=[target_column])
        y_true = data[target_column]
        
        # Make predictions
        predictions = self._make_predictions(X, {"model_id": model_id})["predictions"]
        
        # Calculate metrics
        metrics = {}
        model_type = self.model_metrics[model_id]["model_type"]
        
        if "classifier" in model_type:
            metrics["accuracy"] = accuracy_score(y_true, predictions)
            metrics["classification_report"] = classification_report(y_true, predictions)
        else:
            metrics["mse"] = mean_squared_error(y_true, predictions)
            metrics["rmse"] = np.sqrt(metrics["mse"])
        
        return metrics
    
    def _analyze_feature_importance(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze feature importance"""
        model_id = parameters["model_id"]
        
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
            
        model = self.models[model_id]
        feature_columns = self.preprocessing_pipeline[model_id]["feature_columns"]
        
        importance = model.feature_importances_
        feature_importance = dict(zip(feature_columns, importance))
        
        return {
            "feature_importance": feature_importance,
            "top_features": dict(sorted(
                feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10])
        }
    
    def _optimize_model(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize model hyperparameters"""
        from sklearn.model_selection import GridSearchCV
        
        model_type = parameters["model_type"]
        param_grid = parameters["param_grid"]
        target_column = parameters["target_column"]
        
        X = data.drop(columns=[target_column])
        y = data[target_column]
        
        # Create base model
        if model_type == "random_forest_classifier":
            model = RandomForestClassifier()
        elif model_type == "random_forest_regressor":
            model = RandomForestRegressor()
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        # Perform grid search
        grid_search = GridSearchCV(
            model,
            param_grid,
            cv=parameters.get("cv", 5),
            scoring=parameters.get("scoring", None),
            n_jobs=parameters.get("n_jobs", -1)
        )
        
        grid_search.fit(X, y)
        
        return {
            "best_params": grid_search.best_params_,
            "best_score": grid_search.best_score_,
            "cv_results": grid_search.cv_results_
        }
    
    def _preprocess_data(self, data: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess data for model training or prediction"""
        # Handle missing values
        if parameters.get("handle_missing", True):
            strategy = parameters.get("missing_strategy", "mean")
            if strategy == "mean":
                data = data.fillna(data.mean())
            elif strategy == "median":
                data = data.fillna(data.median())
            elif strategy == "mode":
                data = data.fillna(data.mode().iloc[0])
            elif strategy == "drop":
                data = data.dropna()
        
        # Handle categorical variables
        if parameters.get("handle_categorical", True):
            categorical_columns = data.select_dtypes(include=['object']).columns
            data = pd.get_dummies(data, columns=categorical_columns)
        
        # Scale numerical features
        if parameters.get("scale_features", True):
            numerical_columns = data.select_dtypes(include=['float64', 'int64']).columns
            scaler = StandardScaler()
            data[numerical_columns] = scaler.fit_transform(data[numerical_columns])
        
        return {
            "processed_data": data,
            "feature_columns": list(data.columns)
        }
    
    def _save_model(self, model_id: str):
        """Save model and preprocessing pipeline to disk"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
            
        model_path = self.model_dir / f"{model_id}_model.pkl"
        pipeline_path = self.model_dir / f"{model_id}_pipeline.pkl"
        metrics_path = self.model_dir / f"{model_id}_metrics.json"
        
        # Save model
        joblib.dump(self.models[model_id], model_path)
        
        # Save preprocessing pipeline
        with open(pipeline_path, 'wb') as f:
            pickle.dump(self.preprocessing_pipeline[model_id], f)
            
        # Save metrics
        with open(metrics_path, 'w') as f:
            json.dump(self.model_metrics[model_id], f)
