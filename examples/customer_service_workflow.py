import asyncio
import logging
from datetime import datetime
from pathlib import Path
import json

from src.core.base import Task, AgentSystem, Message
from src.agents.customer_service_agent import CustomerServiceAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def customer_service_workflow(
    system: AgentSystem,
    cs_agent: CustomerServiceAgent,
    inquiries: list[str]
) -> dict[str, any]:
    """Process a series of customer service inquiries"""
    
    results = []
    
    for idx, inquiry in enumerate(inquiries, 1):
        logger.info(f"Processing inquiry {idx}: {inquiry}")
        
        # Create task for inquiry
        task = Task(
            task_id=f"inquiry_{idx}",
            task_type="customer_inquiry",
            input_data=inquiry,
            parameters={}
        )
        
        # Submit task
        system.submit_task(task)
        while not system.get_task_result(task.task_id):
            await asyncio.sleep(0.1)
        
        # Get result
        result = system.get_task_result(task.task_id)
        
        if result.status == "success":
            results.append({
                "inquiry": inquiry,
                "response": result.output["response"],
                "tools_used": result.output["tools_used"],
                "timestamp": result.output["timestamp"]
            })
            logger.info(f"Successfully processed inquiry {idx}")
        else:
            logger.error(f"Failed to process inquiry {idx}: {result.error}")
            results.append({
                "inquiry": inquiry,
                "error": result.error,
                "timestamp": datetime.now().isoformat()
            })
    
    # Generate summary
    summary = {
        "total_inquiries": len(inquiries),
        "successful_inquiries": len([r for r in results if "error" not in r]),
        "failed_inquiries": len([r for r in results if "error" in r]),
        "tools_used": list(set(
            tool 
            for result in results 
            if "tools_used" in result 
            for tool in result["tools_used"]
        )),
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "results": results,
        "summary": summary
    }

async def main():
    # Initialize agent system
    system = AgentSystem()
    
    # Create work directory
    work_dir = Path("work_files")
    cs_dir = work_dir / "customer_service"
    cs_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize customer service agent
    cs_agent = CustomerServiceAgent(
        agent_id="cs_agent_1",
        work_dir=str(cs_dir),
        api_keys={
            "anthropic": "your_anthropic_key"
        }
    )
    
    # Register agent
    system.register_agent(cs_agent)
    
    # Example customer inquiries
    inquiries = [
        "Can you tell me the status of order O2?",
        "I need to return my order O1. It's not what I expected.",
        "What's the current location of my shipment with tracking number TRK123456?",
        "Can you help me cancel order O2?",
        "I'm having issues with my Laptop Pro. Can you create a support ticket? My customer ID is C1."
    ]
    
    # Process inquiries
    results = await customer_service_workflow(system, cs_agent, inquiries)
    
    # Save results
    output_file = cs_dir / f"customer_service_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Log summary
    logger.info("Customer Service Workflow Summary:")
    logger.info(f"Total Inquiries: {results['summary']['total_inquiries']}")
    logger.info(f"Successful: {results['summary']['successful_inquiries']}")
    logger.info(f"Failed: {results['summary']['failed_inquiries']}")
    logger.info(f"Tools Used: {', '.join(results['summary']['tools_used'])}")
    logger.info(f"Results saved to: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
