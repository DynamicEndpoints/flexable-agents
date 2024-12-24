import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json
import markdown
import jinja2
from typing import List, Dict, Any

from src.core.base import Task, AgentSystem, Message
from src.agents.creative_agent import CreativeAgent
from src.agents.image_agent import ImageAgent
from src.agents.visualization_agent import VisualizationAgent
from src.agents.db_agent import DatabaseAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTML template for the story
STORY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        body {
            font-family: 'Georgia', serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .story-section {
            background-color: white;
            padding: 30px;
            margin: 20px 0;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .poetry {
            font-style: italic;
            margin: 20px 0;
            padding: 20px;
            border-left: 4px solid #4a90e2;
        }
        .image-analysis {
            background-color: #f9f9f9;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
        .character-profile {
            background-color: #fff8dc;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
        }
        img {
            max-width: 100%;
            height: auto;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 3px 6px rgba(0,0,0,0.2);
        }
        .metaphor {
            color: #2c5282;
            font-style: italic;
        }
        .scene-description {
            background-color: #f0f9ff;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    
    {% for section in sections %}
    <div class="story-section">
        <h2>{{ section.title }}</h2>
        {% if section.image_path %}
        <img src="{{ section.image_path }}" alt="{{ section.title }}">
        {% endif %}
        
        {% if section.analysis %}
        <div class="image-analysis">
            <h3>Artistic Analysis</h3>
            {{ section.analysis|safe }}
        </div>
        {% endif %}
        
        {% if section.poetry %}
        <div class="poetry">
            {{ section.poetry|safe }}
        </div>
        {% endif %}
        
        {% if section.story %}
        <div class="story">
            {{ section.story|safe }}
        </div>
        {% endif %}
        
        {% if section.characters %}
        <div class="character-profile">
            <h3>Characters</h3>
            {{ section.characters|safe }}
        </div>
        {% endif %}
        
        {% if section.metaphors %}
        <div class="metaphor">
            <h3>Metaphorical Interpretations</h3>
            {{ section.metaphors|safe }}
        </div>
        {% endif %}
        
        {% if section.scene %}
        <div class="scene-description">
            <h3>Scene Setting</h3>
            {{ section.scene|safe }}
        </div>
        {% endif %}
    </div>
    {% endfor %}
</body>
</html>
"""

async def creative_storytelling_workflow(
    system: AgentSystem,
    creative_agent: CreativeAgent,
    image_agent: ImageAgent,
    viz_agent: VisualizationAgent,
    db_agent: DatabaseAgent,
    image_sources: List[str],
    story_theme: str,
    output_dir: Path
) -> Dict[str, Any]:
    """Create a multimedia story from a collection of images"""
    
    story_sections = []
    
    # Process each image
    for idx, image_source in enumerate(image_sources, 1):
        section_title = f"Chapter {idx}"
        logger.info(f"Processing {section_title} with image: {image_source}")
        
        # 1. Analyze image
        analysis_task = Task(
            task_id=f"analyze_image_{idx}",
            task_type="image_analysis",
            input_data=image_source,
            parameters={
                "analysis_prompt": f"""
                Analyze this image in relation to the theme: {story_theme}
                Consider:
                1. Visual elements and composition
                2. Symbolic meanings
                3. Emotional resonance
                4. Connection to the overall theme
                """
            }
        )
        
        system.submit_task(analysis_task)
        while not system.get_task_result(analysis_task.task_id):
            await asyncio.sleep(0.1)
        
        analysis_result = system.get_task_result(analysis_task.task_id)
        
        # 2. Generate poetry
        poetry_task = Task(
            task_id=f"generate_poetry_{idx}",
            task_type="poetry_generation",
            input_data=image_source,
            parameters={
                "type": "sonnet" if idx % 2 == 0 else "free_verse",
                "style": "dramatic"
            }
        )
        
        system.submit_task(poetry_task)
        while not system.get_task_result(poetry_task.task_id):
            await asyncio.sleep(0.1)
        
        poetry_result = system.get_task_result(poetry_task.task_id)
        
        # 3. Create story segment
        story_task = Task(
            task_id=f"create_story_{idx}",
            task_type="story_creation",
            input_data=image_source,
            parameters={
                "genre": "literary",
                "length": "medium",
                "perspective": "third_person"
            }
        )
        
        system.submit_task(story_task)
        while not system.get_task_result(story_task.task_id):
            await asyncio.sleep(0.1)
        
        story_result = system.get_task_result(story_task.task_id)
        
        # 4. Develop characters
        character_task = Task(
            task_id=f"develop_characters_{idx}",
            task_type="character_development",
            input_data=image_source,
            parameters={
                "count": 2,
                "depth": "detailed"
            }
        )
        
        system.submit_task(character_task)
        while not system.get_task_result(character_task.task_id):
            await asyncio.sleep(0.1)
        
        character_result = system.get_task_result(character_task.task_id)
        
        # 5. Generate metaphors
        metaphor_task = Task(
            task_id=f"generate_metaphors_{idx}",
            task_type="metaphor_generation",
            input_data=image_source,
            parameters={
                "style": "poetic",
                "count": 3
            }
        )
        
        system.submit_task(metaphor_task)
        while not system.get_task_result(metaphor_task.task_id):
            await asyncio.sleep(0.1)
        
        metaphor_result = system.get_task_result(metaphor_task.task_id)
        
        # 6. Set scene
        scene_task = Task(
            task_id=f"set_scene_{idx}",
            task_type="scene_setting",
            input_data=image_source,
            parameters={
                "style": "atmospheric",
                "focus": ["atmosphere", "sensory_elements"]
            }
        )
        
        system.submit_task(scene_task)
        while not system.get_task_result(scene_task.task_id):
            await asyncio.sleep(0.1)
        
        scene_result = system.get_task_result(scene_task.task_id)
        
        # Add section to story
        story_sections.append({
            "title": section_title,
            "image_path": image_source,
            "analysis": markdown.markdown(analysis_result.output["analysis"]),
            "poetry": markdown.markdown(poetry_result.output["poetry"]),
            "story": markdown.markdown(story_result.output["story"]),
            "characters": markdown.markdown(character_result.output["characters"]),
            "metaphors": markdown.markdown(metaphor_result.output["metaphors"]),
            "scene": markdown.markdown(scene_result.output["scene"])
        })
        
        # Store results in database
        store_task = Task(
            task_id=f"store_chapter_{idx}",
            task_type="batch_insert",
            input_data={
                "chapter_data": {
                    "chapter_number": idx,
                    "image_source": image_source,
                    "analysis": analysis_result.output,
                    "poetry": poetry_result.output,
                    "story": story_result.output,
                    "characters": character_result.output,
                    "metaphors": metaphor_result.output,
                    "scene": scene_result.output,
                    "timestamp": datetime.now().isoformat()
                }
            },
            parameters={
                "table": "story_chapters",
                "batch_size": 1
            }
        )
        
        system.submit_task(store_task)
        while not system.get_task_result(store_task.task_id):
            await asyncio.sleep(0.1)
    
    # Generate HTML story
    template = jinja2.Template(STORY_TEMPLATE)
    html_content = template.render(
        title=f"A Story of {story_theme}",
        sections=story_sections
    )
    
    # Save HTML file
    output_file = output_dir / f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return {
        "title": f"A Story of {story_theme}",
        "chapter_count": len(story_sections),
        "output_file": str(output_file)
    }

async def main():
    # Initialize the agent system
    system = AgentSystem()
    
    # Create work directories
    work_dir = Path("work_files")
    creative_dir = work_dir / "creative"
    image_dir = work_dir / "images"
    viz_dir = work_dir / "visualizations"
    output_dir = work_dir / "stories"
    
    for dir_path in [work_dir, creative_dir, image_dir, viz_dir, output_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize agents
    creative_agent = CreativeAgent(
        agent_id="creative_agent_1",
        work_dir=str(creative_dir),
        api_keys={
            "anthropic": "your_anthropic_key"
        }
    )
    
    image_agent = ImageAgent(
        agent_id="image_agent_1",
        work_dir=str(image_dir),
        api_keys={
            "anthropic": "your_anthropic_key"
        }
    )
    
    viz_agent = VisualizationAgent(
        agent_id="viz_agent_1",
        work_dir=str(viz_dir),
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
            "database": "stories_db"
        }
    )
    
    # Register all agents
    for agent in [creative_agent, image_agent, viz_agent, db_agent]:
        system.register_agent(agent)
    
    # Example image sources
    image_sources = [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg",
        "https://example.com/image3.jpg"
    ]
    
    # Create story
    story_result = await creative_storytelling_workflow(
        system,
        creative_agent,
        image_agent,
        viz_agent,
        db_agent,
        image_sources,
        "Journey Through Time",
        output_dir
    )
    
    logger.info(f"Story created successfully!")
    logger.info(f"Title: {story_result['title']}")
    logger.info(f"Chapters: {story_result['chapter_count']}")
    logger.info(f"Output file: {story_result['output_file']}")

if __name__ == "__main__":
    asyncio.run(main())
