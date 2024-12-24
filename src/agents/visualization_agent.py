import asyncio
import base64
from pathlib import Path
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import io
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from PIL import Image
from anthropic import Anthropic

from ..core.base import Agent, Task, TaskResult, Message

logger = logging.getLogger(__name__)

class VisualizationAgent(Agent):
    """Agent for handling charts, graphs, and data visualization tasks"""
    
    def __init__(
        self,
        agent_id: str,
        work_dir: str,
        api_keys: Dict[str, str],
        style_config: Dict[str, Any] = None
    ):
        super().__init__(
            agent_id=agent_id,
            capabilities=[
                "chart_analysis",
                "graph_generation",
                "data_visualization",
                "chart_extraction",
                "style_application",
                "chart_comparison"
            ]
        )
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Claude client for vision tasks
        self.anthropic = Anthropic(api_key=api_keys.get("anthropic"))
        
        # Set visualization style defaults
        self.style_config = style_config or {
            "style": "whitegrid",
            "palette": "deep",
            "font_scale": 1.2,
            "figure_size": (10, 6)
        }
        sns.set_theme(**self.style_config)
        
        # Initialize cache for processed charts
        self.chart_cache = {}
        
    async def process_task(self, task: Task) -> TaskResult:
        """Process visualization tasks"""
        try:
            if task.task_type == "chart_analysis":
                output = await self._analyze_chart(task.input_data, task.parameters)
            elif task.task_type == "graph_generation":
                output = await self._generate_graph(task.input_data, task.parameters)
            elif task.task_type == "data_visualization":
                output = await self._create_visualization(task.input_data, task.parameters)
            elif task.task_type == "chart_extraction":
                output = await self._extract_chart_data(task.input_data, task.parameters)
            elif task.task_type == "style_application":
                output = await self._apply_style(task.input_data, task.parameters)
            elif task.task_type == "chart_comparison":
                output = await self._compare_charts(task.input_data, task.parameters)
            else:
                raise ValueError(f"Unsupported task type: {task.task_type}")
            
            return TaskResult(
                task_id=task.task_id,
                status="success",
                output=output,
                agent_id=self.agent_id
            )
        except Exception as e:
            logger.error(f"Visualization error in task {task.task_id}: {str(e)}")
            return TaskResult(
                task_id=task.task_id,
                status="failed",
                error=str(e),
                agent_id=self.agent_id
            )
    
    async def _analyze_chart(self, image_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze chart using Claude's vision capabilities"""
        with open(image_path, "rb") as img_file:
            image_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        # Prepare the analysis prompt
        analysis_prompt = parameters.get("analysis_prompt", """
        Analyze this chart in detail. Please provide:
        1. Chart type and main purpose
        2. Key metrics and their values
        3. Trends or patterns
        4. Notable insights
        5. Data quality issues (if any)
        6. Recommendations for improvement
        """)
        
        response = await self.anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}},
                    {"type": "text", "text": analysis_prompt}
                ]
            }]
        )
        
        # Structure the analysis
        analysis = {
            "raw_analysis": response.content[0].text,
            "timestamp": datetime.now().isoformat(),
            "chart_path": image_path
        }
        
        # Cache the analysis
        self.chart_cache[image_path] = analysis
        
        return analysis
    
    async def _generate_graph(self, data: Union[pd.DataFrame, Dict], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a graph from data"""
        if isinstance(data, dict):
            data = pd.DataFrame(data)
        
        plt.figure(figsize=parameters.get("figure_size", self.style_config["figure_size"]))
        
        chart_type = parameters.get("chart_type", "line")
        if chart_type == "line":
            sns.lineplot(data=data, **parameters.get("plot_params", {}))
        elif chart_type == "bar":
            sns.barplot(data=data, **parameters.get("plot_params", {}))
        elif chart_type == "scatter":
            sns.scatterplot(data=data, **parameters.get("plot_params", {}))
        elif chart_type == "heatmap":
            sns.heatmap(data, **parameters.get("plot_params", {}))
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        
        # Apply styling
        plt.title(parameters.get("title", ""))
        plt.xlabel(parameters.get("xlabel", ""))
        plt.ylabel(parameters.get("ylabel", ""))
        
        # Save the graph
        output_path = self.work_dir / f"graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return {
            "graph_path": str(output_path),
            "data_shape": data.shape,
            "chart_type": chart_type,
            "parameters": parameters
        }
    
    async def _create_visualization(self, data: Any, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive data visualization"""
        if isinstance(data, str) and (Path(data).suffix == '.csv'):
            data = pd.read_csv(data)
        elif isinstance(data, str) and (Path(data).suffix == '.xlsx'):
            data = pd.read_excel(data)
        
        visualizations = []
        
        # Generate multiple chart types based on data characteristics
        if parameters.get("auto_generate", True):
            numerical_cols = data.select_dtypes(include=[np.number]).columns
            categorical_cols = data.select_dtypes(include=['object']).columns
            
            # Time series if datetime column exists
            if any(pd.api.types.is_datetime64_any_dtype(data[col]) for col in data.columns):
                time_col = next(col for col in data.columns if pd.api.types.is_datetime64_any_dtype(data[col]))
                for num_col in numerical_cols:
                    viz = await self._generate_graph(
                        data,
                        {
                            "chart_type": "line",
                            "plot_params": {"x": time_col, "y": num_col},
                            "title": f"{num_col} over Time"
                        }
                    )
                    visualizations.append(viz)
            
            # Distribution plots for numerical columns
            for col in numerical_cols:
                viz = await self._generate_graph(
                    data[col].to_frame(),
                    {
                        "chart_type": "histogram",
                        "title": f"Distribution of {col}"
                    }
                )
                visualizations.append(viz)
            
            # Bar plots for categorical columns
            for cat_col in categorical_cols:
                viz = await self._generate_graph(
                    data[cat_col].value_counts().reset_index(),
                    {
                        "chart_type": "bar",
                        "title": f"Distribution of {cat_col}"
                    }
                )
                visualizations.append(viz)
        
        # Custom visualizations
        custom_charts = parameters.get("custom_charts", [])
        for chart_spec in custom_charts:
            viz = await self._generate_graph(data, chart_spec)
            visualizations.append(viz)
        
        return {
            "visualizations": visualizations,
            "data_summary": data.describe().to_dict(),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _extract_chart_data(self, image_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from chart images using Claude"""
        with open(image_path, "rb") as img_file:
            image_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        extraction_prompt = parameters.get("extraction_prompt", """
        Please extract all numerical data from this chart and format it as a JSON object with the following structure:
        {
            "x_axis": [...],
            "y_axis": [...],
            "series": {
                "series_name": [...values...]
            }
        }
        Include any additional metadata about the chart that might be relevant.
        """)
        
        response = await self.anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}},
                    {"type": "text", "text": extraction_prompt}
                ]
            }]
        )
        
        # Parse the JSON response
        try:
            extracted_data = json.loads(response.content[0].text)
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw text
            extracted_data = {"raw_text": response.content[0].text}
        
        return {
            "extracted_data": extracted_data,
            "source_image": image_path,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _apply_style(self, chart_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply visual styling to an existing chart"""
        # Load the chart
        chart = plt.figure()
        img = plt.imread(chart_path)
        plt.imshow(img)
        
        # Apply styling
        style_params = {
            "title_font": parameters.get("title_font", "Arial"),
            "title_size": parameters.get("title_size", 14),
            "axis_font": parameters.get("axis_font", "Arial"),
            "axis_size": parameters.get("axis_size", 12),
            "grid": parameters.get("grid", True),
            "theme": parameters.get("theme", "default")
        }
        
        # Apply the style
        if style_params["theme"] != "default":
            plt.style.use(style_params["theme"])
        
        plt.title(parameters.get("title", ""), fontfamily=style_params["title_font"], 
                 fontsize=style_params["title_size"])
        
        # Save the styled chart
        output_path = self.work_dir / f"styled_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return {
            "original_path": chart_path,
            "styled_path": str(output_path),
            "applied_style": style_params
        }
    
    async def _compare_charts(self, chart_paths: List[str], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Compare multiple charts using Claude's vision capabilities"""
        # Prepare the images
        images_data = []
        for path in chart_paths:
            with open(path, "rb") as img_file:
                image_data = base64.b64encode(img_file.read()).decode('utf-8')
                images_data.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_data
                    }
                })
        
        comparison_prompt = parameters.get("comparison_prompt", """
        Compare these charts and provide:
        1. Key similarities and differences
        2. Trends present in both charts
        3. Notable discrepancies
        4. Recommendations for visualization improvements
        """)
        
        # Add the text prompt
        images_data.append({
            "type": "text",
            "text": comparison_prompt
        })
        
        response = await self.anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": images_data
            }]
        )
        
        return {
            "comparison_result": response.content[0].text,
            "charts_compared": chart_paths,
            "timestamp": datetime.now().isoformat()
        }
    
    async def handle_message(self, message: Message) -> Optional[Message]:
        """Handle incoming messages"""
        if message.message_type == "visualization_status":
            return Message(
                sender=self.agent_id,
                content={
                    "charts_processed": len(self.chart_cache),
                    "available_capabilities": self.capabilities,
                    "current_style": self.style_config
                },
                message_type="visualization_status_response"
            )
        return None
