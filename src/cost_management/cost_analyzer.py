import asyncio
import logging
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import plotly.express as px
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import QueryDefinition, TimeframeType

logger = logging.getLogger(__name__)

class CostAnalyzer:
    def __init__(
        self,
        credentials: Any,
        subscription_id: str,
        output_dir: str = "reports/cost"
    ):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.cost_client = CostManagementClient(credentials, subscription_id)
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def analyze_costs(
        self,
        scope: str,
        timeframe: str = "MonthToDate",
        granularity: str = "Daily"
    ) -> Dict[str, Any]:
        """Analyze costs for the specified scope"""
        
        # Define cost query
        query = QueryDefinition(
            type="ActualCost",
            timeframe=TimeframeType(timeframe),
            dataset={
                "granularity": granularity,
                "aggregation": {
                    "totalCost": {
                        "name": "Cost",
                        "function": "Sum"
                    }
                },
                "grouping": [
                    {
                        "type": "Dimension",
                        "name": "ResourceGroup"
                    },
                    {
                        "type": "Dimension",
                        "name": "ResourceType"
                    }
                ]
            }
        )
        
        # Get cost data
        cost_data = self.cost_client.query.usage(scope, query)
        
        # Process results
        costs = {
            "total_cost": 0,
            "by_resource_group": {},
            "by_resource_type": {},
            "daily_costs": [],
            "recommendations": []
        }
        
        for row in cost_data.rows:
            date = row[0]
            resource_group = row[1]
            resource_type = row[2]
            cost = row[3]
            
            costs["total_cost"] += cost
            
            # Aggregate by resource group
            if resource_group not in costs["by_resource_group"]:
                costs["by_resource_group"][resource_group] = 0
            costs["by_resource_group"][resource_group] += cost
            
            # Aggregate by resource type
            if resource_type not in costs["by_resource_type"]:
                costs["by_resource_type"][resource_type] = 0
            costs["by_resource_type"][resource_type] += cost
            
            # Track daily costs
            costs["daily_costs"].append({
                "date": date,
                "cost": cost,
                "resource_group": resource_group,
                "resource_type": resource_type
            })
        
        # Generate cost recommendations
        costs["recommendations"] = await self._generate_recommendations(costs)
        
        return costs
    
    async def generate_report(
        self,
        costs: Dict[str, Any],
        report_type: str = "html"
    ) -> str:
        """Generate cost analysis report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"cost_report_{timestamp}.{report_type}"
        
        if report_type == "html":
            report = self._generate_html_report(costs)
        elif report_type == "json":
            report = json.dumps(costs, indent=2)
        else:
            raise ValueError(f"Unsupported report type: {report_type}")
        
        with open(report_path, "w") as f:
            f.write(report)
        
        return str(report_path)
    
    def _generate_html_report(self, costs: Dict[str, Any]) -> str:
        """Generate HTML report with visualizations"""
        plots = []
        
        # Daily cost trend
        daily_df = pd.DataFrame(costs["daily_costs"])
        plots.append(px.line(
            daily_df,
            x="date",
            y="cost",
            title="Daily Cost Trend"
        ).to_html())
        
        # Cost by resource group
        rg_df = pd.DataFrame([
            {"resource_group": rg, "cost": cost}
            for rg, cost in costs["by_resource_group"].items()
        ])
        plots.append(px.pie(
            rg_df,
            values="cost",
            names="resource_group",
            title="Cost by Resource Group"
        ).to_html())
        
        # Cost by resource type
        rt_df = pd.DataFrame([
            {"resource_type": rt, "cost": cost}
            for rt, cost in costs["by_resource_type"].items()
        ])
        plots.append(px.bar(
            rt_df,
            x="resource_type",
            y="cost",
            title="Cost by Resource Type"
        ).to_html())
        
        # Generate HTML
        html = f"""
        <html>
        <head>
            <title>Azure Cost Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric {{ margin-bottom: 20px; }}
                .plot {{ margin-bottom: 40px; }}
                .recommendation {{ 
                    background-color: #f8f9fa;
                    padding: 10px;
                    margin-bottom: 10px;
                    border-left: 4px solid #007bff;
                }}
                .high-cost {{
                    color: #dc3545;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <h1>Azure Cost Analysis Report</h1>
            <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            
            <h2>Summary</h2>
            <div class="metric">
                <h3>Total Cost</h3>
                <p class="{'high-cost' if costs['total_cost'] > 1000 else ''}">
                    ${costs['total_cost']:.2f}
                </p>
            </div>
            
            <h2>Cost Distribution</h2>
            {"".join(f'<div class="plot">{plot}</div>' for plot in plots)}
            
            <h2>Recommendations</h2>
            {"".join(
                f'<div class="recommendation">'
                f'<h4>{rec["title"]}</h4>'
                f'<p>{rec["description"]}</p>'
                f'<p>Potential Savings: ${rec["potential_savings"]:.2f}</p>'
                f'</div>'
                for rec in costs['recommendations']
            )}
        </body>
        </html>
        """
        
        return html
    
    async def _generate_recommendations(self, costs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        # Check for high-cost resource groups
        for rg, cost in costs["by_resource_group"].items():
            if cost > costs["total_cost"] * 0.3:  # More than 30% of total cost
                recommendations.append({
                    "title": f"High-cost resource group: {rg}",
                    "description": "Consider reviewing and optimizing resources in this group",
                    "potential_savings": cost * 0.2  # Estimate 20% potential savings
                })
        
        # Check for expensive resource types
        for rt, cost in costs["by_resource_type"].items():
            if "virtualMachines" in rt.lower():
                recommendations.append({
                    "title": "Virtual Machine Optimization",
                    "description": "Consider using reserved instances or scaling down during off-hours",
                    "potential_savings": cost * 0.3  # Estimate 30% potential savings
                })
            elif "storage" in rt.lower():
                recommendations.append({
                    "title": "Storage Optimization",
                    "description": "Review storage tiers and implement lifecycle management",
                    "potential_savings": cost * 0.25  # Estimate 25% potential savings
                })
        
        # Check for cost trends
        daily_costs = pd.DataFrame(costs["daily_costs"])
        if not daily_costs.empty:
            recent_trend = daily_costs.groupby("date")["cost"].sum().pct_change().mean()
            if recent_trend > 0.1:  # 10% average daily increase
                recommendations.append({
                    "title": "Rising Cost Trend",
                    "description": "Costs are increasing significantly. Review recent changes and implement cost controls",
                    "potential_savings": costs["total_cost"] * 0.15  # Estimate 15% potential savings
                })
        
        return recommendations

async def main():
    # Example usage
    analyzer = CostAnalyzer(
        credentials=None,  # Add Azure credentials
        subscription_id="your-subscription-id"
    )
    
    # Analyze costs
    scope = f"/subscriptions/your-subscription-id"
    costs = await analyzer.analyze_costs(scope)
    
    # Generate report
    report_path = await analyzer.generate_report(costs)
    
    logger.info(f"Cost analysis report generated: {report_path}")

if __name__ == "__main__":
    asyncio.run(main())
