# SharePoint Monitor Documentation

## Overview
The SharePoint Monitor is a comprehensive monitoring solution for SharePoint Online environments. It collects metrics, generates reports, and provides insights into site usage, performance, and security.

## Features

### Site Usage Monitoring
- Active users tracking
- Page views analytics
- Document activity monitoring
- Storage utilization tracking

### Performance Metrics
- Page load times
- API response times
- Resource utilization
- Network latency

### Security Monitoring
- Access attempts
- Permission changes
- File sharing activity
- Security policy compliance

### Report Generation
- HTML reports with visualizations
- JSON data export
- Customizable metrics
- Trend analysis

## Usage

### Basic Setup
```python
from src.monitoring.sharepoint_monitor import SharePointMonitor

monitor = SharePointMonitor(
    graph_client=graph_client,
    config_path="config/sharepoint_dev_config.json"
)
```

### Collecting Metrics
```python
# Collect metrics for a specific timeframe
metrics = await monitor.collect_metrics(
    start_date=start_date,
    end_date=end_date
)
```

### Generating Reports
```python
# Generate HTML report
report_path = monitor.generate_report(
    metrics,
    report_type="html"
)
```

## Configuration

### Sample Configuration
```json
{
    "monitoring": {
        "metrics": {
            "collection_interval": 300,
            "retention_days": 30
        },
        "alerts": {
            "storage": {
                "threshold": 80,
                "recipients": ["admin@company.com"]
            },
            "performance": {
                "threshold": 5000,
                "recipients": ["ops@company.com"]
            }
        }
    }
}
```

## Metrics Collected

### Site Usage
- Daily active users
- Monthly active users
- Page views
- File operations

### Performance
- Average page load time
- API response latency
- Storage IOPS
- Network throughput

### Security
- Failed login attempts
- Permission changes
- External sharing events
- Policy violations

## Report Types

### HTML Reports
- Interactive visualizations
- Trend graphs
- Usage statistics
- Performance metrics

### JSON Reports
- Raw metrics data
- Custom analysis
- Integration with other tools
- Historical data

## Best Practices

### Monitoring Setup
1. Configure appropriate collection intervals
2. Set meaningful alert thresholds
3. Define clear escalation paths
4. Implement retention policies

### Performance Optimization
1. Monitor resource-intensive operations
2. Track long-running queries
3. Identify bottlenecks
4. Implement caching strategies

### Security Monitoring
1. Track suspicious activities
2. Monitor permission changes
3. Audit file access
4. Review sharing patterns

## Integration

### Power BI Integration
```python
# Export metrics to Power BI
await monitor.export_to_power_bi(
    metrics,
    workspace_id="your-workspace-id",
    dataset_name="SharePoint Metrics"
)
```

### Azure Monitor Integration
```python
# Send metrics to Azure Monitor
await monitor.send_to_azure_monitor(
    metrics,
    workspace_id="your-workspace-id"
)
```

## Troubleshooting

### Common Issues
1. Metric collection failures
   - Check permissions
   - Verify API access
   - Review rate limits

2. Report generation errors
   - Validate data format
   - Check storage space
   - Verify dependencies

3. Alert notification issues
   - Check email configuration
   - Verify recipient lists
   - Test notification paths

## API Reference

### SharePointMonitor Class
```python
class SharePointMonitor:
    def __init__(
        self,
        graph_client: Any,
        config_path: str,
        output_dir: str = "monitoring/sharepoint"
    ):
        """Initialize SharePoint Monitor"""
        pass

    async def collect_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Collect SharePoint metrics"""
        pass

    def generate_report(
        self,
        metrics: Dict[str, Any],
        report_type: str = "html"
    ) -> str:
        """Generate monitoring report"""
        pass
```

## Contributing
1. Follow coding standards
2. Add unit tests
3. Update documentation
4. Submit pull requests

## License
MIT License - See LICENSE file for details
