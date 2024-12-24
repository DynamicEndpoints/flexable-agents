import asyncio
import logging
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(
        self,
        graph_client: Any,
        config_path: str,
        output_dir: str = "monitoring/performance"
    ):
        self.graph_client = graph_client
        
        # Load configuration
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def collect_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collect performance metrics"""
        metrics = {}
        
        # Page performance
        metrics["page_performance"] = await self._collect_page_metrics(start_date, end_date)
        
        # API performance
        metrics["api_performance"] = await self._collect_api_metrics(start_date, end_date)
        
        # Resource usage
        metrics["resource_usage"] = await self._collect_resource_metrics(start_date, end_date)
        
        # Network performance
        metrics["network_performance"] = await self._collect_network_metrics(start_date, end_date)
        
        return metrics
    
    async def _collect_page_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collect page performance metrics"""
        metrics = {}
        
        # Get page load times
        response = await self.graph_client._make_request(
            "GET",
            "/reports/getSharePointSiteUsagePages(period='D7')"
        )
        
        # Process metrics
        page_metrics = []
        for page in response:
            page_metrics.append({
                "url": page["pageUrl"],
                "ttfb": page["averageTimeToFirstByte"],
                "render": page["averageTimeToFullyLoaded"],
                "visits": page["pageVisits"]
            })
        
        metrics["pages"] = page_metrics
        
        # Calculate aggregates
        metrics["aggregates"] = {
            "avg_ttfb": sum(p["ttfb"] for p in page_metrics) / len(page_metrics),
            "avg_render": sum(p["render"] for p in page_metrics) / len(page_metrics),
            "total_visits": sum(p["visits"] for p in page_metrics)
        }
        
        # Performance thresholds
        metrics["thresholds"] = {
            "ttfb": {
                "warning": 1000,  # 1 second
                "critical": 3000  # 3 seconds
            },
            "render": {
                "warning": 3000,  # 3 seconds
                "critical": 5000  # 5 seconds
            }
        }
        
        return metrics
    
    async def _collect_api_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collect API performance metrics"""
        metrics = {}
        
        # Get API metrics
        response = await self.graph_client._make_request(
            "GET",
            "/reports/getSharePointActivityUserDetail(period='D7')"
        )
        
        # Process metrics
        api_metrics = []
        for call in response:
            api_metrics.append({
                "endpoint": call["apiEndpoint"],
                "latency": call["averageLatency"],
                "success_rate": call["successRate"],
                "calls": call["totalCalls"]
            })
        
        metrics["endpoints"] = api_metrics
        
        # Calculate aggregates
        metrics["aggregates"] = {
            "avg_latency": sum(a["latency"] for a in api_metrics) / len(api_metrics),
            "avg_success_rate": sum(a["success_rate"] for a in api_metrics) / len(api_metrics),
            "total_calls": sum(a["calls"] for a in api_metrics)
        }
        
        return metrics
    
    async def _collect_resource_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collect resource usage metrics"""
        metrics = {}
        
        # Get resource usage
        response = await self.graph_client._make_request(
            "GET",
            "/reports/getSharePointSiteUsageStorage(period='D7')"
        )
        
        # Process metrics
        resource_metrics = []
        for site in response:
            resource_metrics.append({
                "site": site["siteUrl"],
                "storage_used": site["storageUsedInBytes"],
                "storage_allocated": site["storageAllocatedInBytes"],
                "files": site["fileCount"]
            })
        
        metrics["sites"] = resource_metrics
        
        # Calculate aggregates
        metrics["aggregates"] = {
            "total_storage_used": sum(r["storage_used"] for r in resource_metrics),
            "total_storage_allocated": sum(r["storage_allocated"] for r in resource_metrics),
            "total_files": sum(r["files"] for r in resource_metrics)
        }
        
        return metrics
    
    async def _collect_network_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collect network performance metrics"""
        metrics = {}
        
        # Get network metrics
        response = await self.graph_client._make_request(
            "GET",
            "/reports/getSharePointActivityUserDetail(period='D7')"
        )
        
        # Process metrics
        network_metrics = []
        for user in response:
            network_metrics.append({
                "location": user["userLocation"],
                "bandwidth": user["averageBandwidth"],
                "latency": user["averageLatency"],
                "packet_loss": user["packetLoss"]
            })
        
        metrics["locations"] = network_metrics
        
        # Calculate aggregates
        metrics["aggregates"] = {
            "avg_bandwidth": sum(n["bandwidth"] for n in network_metrics) / len(network_metrics),
            "avg_latency": sum(n["latency"] for n in network_metrics) / len(network_metrics),
            "avg_packet_loss": sum(n["packet_loss"] for n in network_metrics) / len(network_metrics)
        }
        
        return metrics
    
    def generate_report(self, metrics: Dict[str, Any], report_type: str = "html") -> str:
        """Generate performance report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"performance_report_{timestamp}.{report_type}"
        
        if report_type == "html":
            report = self._generate_html_report(metrics)
        elif report_type == "json":
            report = json.dumps(metrics, indent=2)
        else:
            raise ValueError(f"Unsupported report type: {report_type}")
        
        with open(report_path, "w") as f:
            f.write(report)
        
        return str(report_path)
    
    def _generate_html_report(self, metrics: Dict[str, Any]) -> str:
        """Generate HTML report with visualizations"""
        plots = []
        
        # Page performance plot
        page_df = pd.DataFrame(metrics["page_performance"]["pages"])
        plots.append(px.scatter(
            page_df,
            x="ttfb",
            y="render",
            size="visits",
            hover_data=["url"],
            title="Page Performance"
        ).to_html())
        
        # API performance plot
        api_df = pd.DataFrame(metrics["api_performance"]["endpoints"])
        plots.append(px.bar(
            api_df,
            x="endpoint",
            y="latency",
            color="success_rate",
            title="API Performance"
        ).to_html())
        
        # Resource usage plot
        resource_df = pd.DataFrame(metrics["resource_usage"]["sites"])
        plots.append(px.bar(
            resource_df,
            x="site",
            y=["storage_used", "storage_allocated"],
            title="Resource Usage"
        ).to_html())
        
        # Network performance plot
        network_df = pd.DataFrame(metrics["network_performance"]["locations"])
        plots.append(px.scatter_mapbox(
            network_df,
            lat="latitude",
            lon="longitude",
            color="latency",
            size="bandwidth",
            hover_data=["packet_loss"],
            title="Network Performance"
        ).to_html())
        
        # Generate HTML
        html = f"""
        <html>
        <head>
            <title>SharePoint Performance Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric {{ margin-bottom: 20px; }}
                .plot {{ margin-bottom: 40px; }}
                .warning {{ color: orange; }}
                .critical {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>SharePoint Performance Report</h1>
            <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            
            <h2>Summary</h2>
            <div class="metric">
                <h3>Page Performance</h3>
                <p>Average TTFB: {metrics["page_performance"]["aggregates"]["avg_ttfb"]:.2f} ms</p>
                <p>Average Render Time: {metrics["page_performance"]["aggregates"]["avg_render"]:.2f} ms</p>
            </div>
            
            <div class="metric">
                <h3>API Performance</h3>
                <p>Average Latency: {metrics["api_performance"]["aggregates"]["avg_latency"]:.2f} ms</p>
                <p>Success Rate: {metrics["api_performance"]["aggregates"]["avg_success_rate"]:.2f}%</p>
            </div>
            
            <div class="metric">
                <h3>Resource Usage</h3>
                <p>Total Storage: {metrics["resource_usage"]["aggregates"]["total_storage_used"] / (1024**3):.2f} GB</p>
                <p>Total Files: {metrics["resource_usage"]["aggregates"]["total_files"]}</p>
            </div>
            
            <div class="metric">
                <h3>Network Performance</h3>
                <p>Average Bandwidth: {metrics["network_performance"]["aggregates"]["avg_bandwidth"] / (1024**2):.2f} Mbps</p>
                <p>Average Latency: {metrics["network_performance"]["aggregates"]["avg_latency"]:.2f} ms</p>
            </div>
            
            <h2>Visualizations</h2>
            {"".join(f'<div class="plot">{plot}</div>' for plot in plots)}
        </body>
        </html>
        """
        
        return html

async def main():
    # Example usage
    monitor = PerformanceMonitor(
        graph_client=None,  # Replace with actual graph client
        config_path="config/templates/sharepoint_dev_config_template.json"
    )
    
    # Collect metrics for last 7 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    metrics = await monitor.collect_metrics(start_date, end_date)
    report_path = monitor.generate_report(metrics)
    
    logger.info(f"Report generated: {report_path}")

if __name__ == "__main__":
    asyncio.run(main())
