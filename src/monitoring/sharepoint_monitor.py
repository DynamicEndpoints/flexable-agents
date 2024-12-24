import asyncio
import logging
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
import pandas as pd
import plotly.express as px

logger = logging.getLogger(__name__)

class SharePointMonitor:
    def __init__(
        self,
        graph_client: Any,
        config_path: str,
        output_dir: str = "monitoring/reports"
    ):
        self.graph_client = graph_client
        
        # Load configuration
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def collect_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collect SharePoint metrics"""
        metrics = {}
        
        # Site usage metrics
        metrics["site_usage"] = await self._collect_site_usage(start_date, end_date)
        
        # Storage metrics
        metrics["storage"] = await self._collect_storage_metrics()
        
        # Performance metrics
        metrics["performance"] = await self._collect_performance_metrics(start_date, end_date)
        
        # Security metrics
        metrics["security"] = await self._collect_security_metrics(start_date, end_date)
        
        return metrics
    
    async def _collect_site_usage(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collect site usage metrics"""
        usage = {}
        
        # Get site activity
        activity = await self.graph_client._make_request(
            "GET",
            f"/reports/getSharePointSiteUsageDetail(period='D7')"
        )
        
        # Process metrics
        usage["visits"] = {
            "total": sum(site["visitCount"] for site in activity),
            "by_site": {site["siteUrl"]: site["visitCount"] for site in activity}
        }
        
        usage["active_users"] = {
            "total": len({user["userPrincipalName"] for site in activity for user in site["lastActivityDate"]}),
            "by_site": {site["siteUrl"]: len(site["lastActivityDate"]) for site in activity}
        }
        
        usage["file_activity"] = {
            "viewed": sum(site["fileViewedOrEdited"] for site in activity),
            "shared": sum(site["filesSharedExternally"] for site in activity),
            "synced": sum(site["filesSynced"] for site in activity)
        }
        
        return usage
    
    async def _collect_storage_metrics(self) -> Dict[str, Any]:
        """Collect storage metrics"""
        storage = {}
        
        # Get storage usage
        usage = await self.graph_client._make_request(
            "GET",
            "/reports/getSharePointSiteUsageStorage(period='D7')"
        )
        
        # Process metrics
        storage["total"] = sum(site["storageUsedInBytes"] for site in usage)
        storage["by_site"] = {
            site["siteUrl"]: {
                "used": site["storageUsedInBytes"],
                "allocated": site["storageAllocatedInBytes"]
            }
            for site in usage
        }
        
        return storage
    
    async def _collect_performance_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collect performance metrics"""
        performance = {}
        
        # Get page load times
        load_times = await self.graph_client._make_request(
            "GET",
            "/reports/getSharePointSiteUsagePages(period='D7')"
        )
        
        # Process metrics
        performance["page_load_times"] = {
            "average": sum(page["averageTimeToFirstByte"] for page in load_times) / len(load_times),
            "by_page": {
                page["pageUrl"]: {
                    "ttfb": page["averageTimeToFirstByte"],
                    "render": page["averageTimeToFullyLoaded"]
                }
                for page in load_times
            }
        }
        
        return performance
    
    async def _collect_security_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collect security metrics"""
        security = {}
        
        # Get security events
        events = await self.graph_client._make_request(
            "GET",
            "/security/alerts"
        )
        
        # Process metrics
        security["alerts"] = {
            "total": len(events),
            "by_severity": {
                severity: len([e for e in events if e["severity"] == severity])
                for severity in ["high", "medium", "low"]
            }
        }
        
        return security
    
    def generate_report(self, metrics: Dict[str, Any], report_type: str = "html") -> str:
        """Generate monitoring report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"sharepoint_report_{timestamp}.{report_type}"
        
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
        # Create visualizations
        plots = []
        
        # Site usage plot
        site_usage_df = pd.DataFrame([
            {"site": site, "visits": visits}
            for site, visits in metrics["site_usage"]["visits"]["by_site"].items()
        ])
        plots.append(px.bar(
            site_usage_df,
            x="site",
            y="visits",
            title="Site Visits"
        ).to_html())
        
        # Storage usage plot
        storage_df = pd.DataFrame([
            {
                "site": site,
                "used_gb": data["used"] / (1024 ** 3),
                "allocated_gb": data["allocated"] / (1024 ** 3)
            }
            for site, data in metrics["storage"]["by_site"].items()
        ])
        plots.append(px.bar(
            storage_df,
            x="site",
            y=["used_gb", "allocated_gb"],
            title="Storage Usage (GB)"
        ).to_html())
        
        # Security alerts plot
        security_df = pd.DataFrame([
            {"severity": severity, "count": count}
            for severity, count in metrics["security"]["alerts"]["by_severity"].items()
        ])
        plots.append(px.pie(
            security_df,
            values="count",
            names="severity",
            title="Security Alerts by Severity"
        ).to_html())
        
        # Generate HTML
        html = f"""
        <html>
        <head>
            <title>SharePoint Monitoring Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric {{ margin-bottom: 20px; }}
                .plot {{ margin-bottom: 40px; }}
            </style>
        </head>
        <body>
            <h1>SharePoint Monitoring Report</h1>
            <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            
            <h2>Summary</h2>
            <div class="metric">
                <h3>Site Usage</h3>
                <p>Total Visits: {metrics["site_usage"]["visits"]["total"]}</p>
                <p>Active Users: {metrics["site_usage"]["active_users"]["total"]}</p>
            </div>
            
            <div class="metric">
                <h3>Storage</h3>
                <p>Total Storage Used: {metrics["storage"]["total"] / (1024 ** 3):.2f} GB</p>
            </div>
            
            <div class="metric">
                <h3>Performance</h3>
                <p>Average Page Load Time: {metrics["performance"]["page_load_times"]["average"]:.2f} ms</p>
            </div>
            
            <div class="metric">
                <h3>Security</h3>
                <p>Total Alerts: {metrics["security"]["alerts"]["total"]}</p>
            </div>
            
            <h2>Visualizations</h2>
            {"".join(f'<div class="plot">{plot}</div>' for plot in plots)}
        </body>
        </html>
        """
        
        return html

async def main():
    # Example usage
    monitor = SharePointMonitor(
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
