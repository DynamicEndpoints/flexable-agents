import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json
import pandas as pd

from src.core.base import Task, AgentSystem, Message
from src.agents.visualization_agent import VisualizationAgent
from src.agents.slide_agent import SlideAgent
from src.agents.db_agent import DatabaseAgent
from src.agents.monitoring_agent import MonitoringAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def presentation_analysis_workflow(
    system: AgentSystem,
    viz_agent: VisualizationAgent,
    slide_agent: SlideAgent,
    db_agent: DatabaseAgent,
    monitor_agent: MonitoringAgent,
    presentation_path: str
):
    """Analyze a presentation deck with charts and graphs"""
    
    # Step 1: Initial slide deck analysis
    analysis_task = Task(
        task_id="analyze_deck",
        task_type="slide_analysis",
        input_data=presentation_path,
        parameters={
            "analysis_prompt": """
            Analyze this presentation deck with special attention to:
            1. Charts and graphs present
            2. Key metrics and their trends
            3. Visual effectiveness
            4. Data presentation clarity
            """
        },
        deadline=datetime.now() + timedelta(minutes=10)
    )
    
    system.submit_task(analysis_task)
    while not system.get_task_result("analyze_deck"):
        await asyncio.sleep(0.1)
    
    analysis_result = system.get_task_result("analyze_deck")
    if analysis_result.status == "failed":
        logger.error(f"Failed to analyze deck: {analysis_result.error}")
        return
    
    # Step 2: Extract slides and identify charts
    extract_task = Task(
        task_id="extract_slides",
        task_type="slide_extraction",
        input_data=presentation_path,
        parameters={},
        deadline=datetime.now() + timedelta(minutes=5)
    )
    
    system.submit_task(extract_task)
    while not system.get_task_result("extract_slides"):
        await asyncio.sleep(0.1)
    
    extract_result = system.get_task_result("extract_slides")
    slides = extract_result.output["slides"]
    
    # Step 3: Analyze each chart
    chart_analyses = []
    for slide in slides:
        if slide.get("image_count", 0) > 0:
            chart_task = Task(
                task_id=f"analyze_chart_{slide['page_number']}",
                task_type="chart_analysis",
                input_data=slide["image_path"],
                parameters={
                    "analysis_prompt": """
                    Analyze this chart in detail:
                    1. Chart type and purpose
                    2. Key metrics and values
                    3. Trends and patterns
                    4. Data quality
                    5. Visual effectiveness
                    """
                },
                deadline=datetime.now() + timedelta(minutes=5)
            )
            
            system.submit_task(chart_task)
            while not system.get_task_result(chart_task.task_id):
                await asyncio.sleep(0.1)
            
            result = system.get_task_result(chart_task.task_id)
            if result.status == "success":
                chart_analyses.append({
                    "slide_number": slide["page_number"],
                    "analysis": result.output
                })
    
    # Step 4: Extract data from charts
    chart_data = []
    for analysis in chart_analyses:
        extract_task = Task(
            task_id=f"extract_data_{analysis['slide_number']}",
            task_type="chart_extraction",
            input_data=slides[analysis['slide_number']-1]["image_path"],
            parameters={},
            deadline=datetime.now() + timedelta(minutes=5)
        )
        
        system.submit_task(extract_task)
        while not system.get_task_result(extract_task.task_id):
            await asyncio.sleep(0.1)
        
        result = system.get_task_result(extract_task.task_id)
        if result.status == "success":
            chart_data.append({
                "slide_number": analysis["slide_number"],
                "data": result.output["extracted_data"]
            })
    
    # Step 5: Generate enhanced visualizations
    enhanced_charts = []
    for data in chart_data:
        if isinstance(data["data"], dict) and "x_axis" in data["data"]:
            viz_task = Task(
                task_id=f"enhance_chart_{data['slide_number']}",
                task_type="graph_generation",
                input_data={
                    "x": data["data"]["x_axis"],
                    "y": data["data"]["y_axis"]
                },
                parameters={
                    "chart_type": "line",
                    "title": f"Enhanced Chart from Slide {data['slide_number']}",
                    "style": {
                        "theme": "modern",
                        "colors": "deep"
                    }
                },
                deadline=datetime.now() + timedelta(minutes=5)
            )
            
            system.submit_task(viz_task)
            while not system.get_task_result(viz_task.task_id):
                await asyncio.sleep(0.1)
            
            result = system.get_task_result(viz_task.task_id)
            if result.status == "success":
                enhanced_charts.append({
                    "slide_number": data["slide_number"],
                    "enhanced_chart": result.output
                })
    
    # Step 6: Generate presentation narration
    narration_task = Task(
        task_id="generate_narration",
        task_type="slide_narration",
        input_data=presentation_path,
        parameters={
            "narration_prompt": """
            Provide a detailed narration of this presentation, with special attention to:
            1. Chart explanations and insights
            2. Data trends and patterns
            3. Key messages and conclusions
            4. Recommendations based on the data
            """
        },
        deadline=datetime.now() + timedelta(minutes=10)
    )
    
    system.submit_task(narration_task)
    while not system.get_task_result("generate_narration"):
        await asyncio.sleep(0.1)
    
    narration_result = system.get_task_result("generate_narration")
    
    # Step 7: Store results in database
    store_task = Task(
        task_id="store_analysis",
        task_type="batch_insert",
        input_data={
            "presentation_analysis": {
                "file_path": presentation_path,
                "analysis_date": datetime.now().isoformat(),
                "deck_analysis": analysis_result.output,
                "chart_analyses": chart_analyses,
                "chart_data": chart_data,
                "enhanced_charts": enhanced_charts,
                "narration": narration_result.output
            }
        },
        parameters={
            "table": "presentation_analyses",
            "batch_size": 1
        },
        deadline=datetime.now() + timedelta(minutes=5)
    )
    
    system.submit_task(store_task)
    while not system.get_task_result("store_analysis"):
        await asyncio.sleep(0.1)
    
    store_result = system.get_task_result("store_analysis")
    
    # Generate final report
    report = {
        "presentation_path": presentation_path,
        "analysis_date": datetime.now().isoformat(),
        "total_slides": len(slides),
        "charts_analyzed": len(chart_analyses),
        "data_extracted": len(chart_data),
        "enhanced_visualizations": len(enhanced_charts),
        "key_insights": analysis_result.output.get("key_insights", []),
        "recommendations": analysis_result.output.get("recommendations", [])
    }
    
    return report

async def main():
    # Initialize the agent system
    system = AgentSystem()
    
    # Create work directories
    work_dir = Path("work_files")
    viz_dir = work_dir / "visualizations"
    slide_dir = work_dir / "slides"
    log_dir = work_dir / "logs"
    for dir_path in [work_dir, viz_dir, slide_dir, log_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize agents
    viz_agent = VisualizationAgent(
        agent_id="viz_agent_1",
        work_dir=str(viz_dir),
        api_keys={
            "anthropic": "your_anthropic_key"
        }
    )
    
    slide_agent = SlideAgent(
        agent_id="slide_agent_1",
        work_dir=str(slide_dir),
        api_keys={
            "anthropic": "your_anthropic_key"
        }
    )
    
    db_agent = DatabaseAgent(
        agent_id="db_agent_1",
        connection_params={
            "host": "localhost",
            "port": 5432,
            "user": "user",
            "password": "password",
            "database": "presentations_db"
        }
    )
    
    monitor_agent = MonitoringAgent(
        agent_id="monitor_1",
        log_dir=str(log_dir)
    )
    
    # Register all agents
    for agent in [viz_agent, slide_agent, db_agent, monitor_agent]:
        system.register_agent(agent)
    
    # Analyze a presentation
    presentation_path = "path/to/your/presentation.pdf"
    report = await presentation_analysis_workflow(
        system,
        viz_agent,
        slide_agent,
        db_agent,
        monitor_agent,
        presentation_path
    )
    
    # Save the report
    report_path = work_dir / "presentation_analysis_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info("Presentation analysis completed successfully!")
    logger.info(f"Report saved to: {report_path}")

if __name__ == "__main__":
    asyncio.run(main())
