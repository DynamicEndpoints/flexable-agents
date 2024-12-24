import pytest
import asyncio
from unittest.mock import MagicMock, patch
import json
from pathlib import Path
from datetime import datetime, timedelta

from src.monitoring.performance_monitor import PerformanceMonitor

@pytest.fixture
def mock_graph_client():
    client = MagicMock()
    client._make_request = MagicMock()
    return client

@pytest.fixture
def config():
    config_path = Path(__file__).parent.parent / "config/templates/sharepoint_dev_config_template.json"
    with open(config_path) as f:
        return json.load(f)

@pytest.fixture
def monitor(mock_graph_client, config, tmp_path):
    return PerformanceMonitor(
        graph_client=mock_graph_client,
        config_path=str(Path(__file__).parent.parent / "config/templates/sharepoint_dev_config_template.json"),
        output_dir=str(tmp_path)
    )

@pytest.mark.asyncio
async def test_collect_page_metrics(monitor, mock_graph_client):
    # Arrange
    mock_graph_client._make_request.return_value = [
        {
            "pageUrl": "https://test.sharepoint.com/sites/test1/page1",
            "averageTimeToFirstByte": 100,
            "averageTimeToFullyLoaded": 500,
            "pageVisits": 1000
        },
        {
            "pageUrl": "https://test.sharepoint.com/sites/test1/page2",
            "averageTimeToFirstByte": 150,
            "averageTimeToFullyLoaded": 600,
            "pageVisits": 500
        }
    ]
    
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    # Act
    metrics = await monitor._collect_page_metrics(start_date, end_date)
    
    # Assert
    assert len(metrics["pages"]) == 2
    assert metrics["aggregates"]["avg_ttfb"] == 125
    assert metrics["aggregates"]["avg_render"] == 550
    assert metrics["aggregates"]["total_visits"] == 1500

@pytest.mark.asyncio
async def test_collect_api_metrics(monitor, mock_graph_client):
    # Arrange
    mock_graph_client._make_request.return_value = [
        {
            "apiEndpoint": "/api/test1",
            "averageLatency": 50,
            "successRate": 99.9,
            "totalCalls": 1000
        },
        {
            "apiEndpoint": "/api/test2",
            "averageLatency": 75,
            "successRate": 99.5,
            "totalCalls": 500
        }
    ]
    
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    # Act
    metrics = await monitor._collect_api_metrics(start_date, end_date)
    
    # Assert
    assert len(metrics["endpoints"]) == 2
    assert metrics["aggregates"]["avg_latency"] == 62.5
    assert metrics["aggregates"]["avg_success_rate"] == 99.7
    assert metrics["aggregates"]["total_calls"] == 1500

@pytest.mark.asyncio
async def test_collect_resource_metrics(monitor, mock_graph_client):
    # Arrange
    mock_graph_client._make_request.return_value = [
        {
            "siteUrl": "https://test.sharepoint.com/sites/test1",
            "storageUsedInBytes": 1024 * 1024 * 100,  # 100 MB
            "storageAllocatedInBytes": 1024 * 1024 * 1024,  # 1 GB
            "fileCount": 1000
        },
        {
            "siteUrl": "https://test.sharepoint.com/sites/test2",
            "storageUsedInBytes": 1024 * 1024 * 200,  # 200 MB
            "storageAllocatedInBytes": 1024 * 1024 * 1024,  # 1 GB
            "fileCount": 2000
        }
    ]
    
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    # Act
    metrics = await monitor._collect_resource_metrics(start_date, end_date)
    
    # Assert
    assert len(metrics["sites"]) == 2
    assert metrics["aggregates"]["total_storage_used"] == 1024 * 1024 * 300
    assert metrics["aggregates"]["total_storage_allocated"] == 1024 * 1024 * 1024 * 2
    assert metrics["aggregates"]["total_files"] == 3000

@pytest.mark.asyncio
async def test_collect_network_metrics(monitor, mock_graph_client):
    # Arrange
    mock_graph_client._make_request.return_value = [
        {
            "userLocation": "US West",
            "averageBandwidth": 100 * 1024 * 1024,  # 100 Mbps
            "averageLatency": 50,
            "packetLoss": 0.1
        },
        {
            "userLocation": "US East",
            "averageBandwidth": 75 * 1024 * 1024,  # 75 Mbps
            "averageLatency": 75,
            "packetLoss": 0.2
        }
    ]
    
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    # Act
    metrics = await monitor._collect_network_metrics(start_date, end_date)
    
    # Assert
    assert len(metrics["locations"]) == 2
    assert metrics["aggregates"]["avg_bandwidth"] == 87.5 * 1024 * 1024
    assert metrics["aggregates"]["avg_latency"] == 62.5
    assert metrics["aggregates"]["avg_packet_loss"] == 0.15

@pytest.mark.asyncio
async def test_collect_metrics(monitor, mock_graph_client):
    # Arrange
    mock_graph_client._make_request.side_effect = [
        # Page metrics
        [
            {
                "pageUrl": "https://test.sharepoint.com/sites/test1/page1",
                "averageTimeToFirstByte": 100,
                "averageTimeToFullyLoaded": 500,
                "pageVisits": 1000
            }
        ],
        # API metrics
        [
            {
                "apiEndpoint": "/api/test1",
                "averageLatency": 50,
                "successRate": 99.9,
                "totalCalls": 1000
            }
        ],
        # Resource metrics
        [
            {
                "siteUrl": "https://test.sharepoint.com/sites/test1",
                "storageUsedInBytes": 1024 * 1024 * 100,
                "storageAllocatedInBytes": 1024 * 1024 * 1024,
                "fileCount": 1000
            }
        ],
        # Network metrics
        [
            {
                "userLocation": "US West",
                "averageBandwidth": 100 * 1024 * 1024,
                "averageLatency": 50,
                "packetLoss": 0.1
            }
        ]
    ]
    
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    # Act
    metrics = await monitor.collect_metrics(start_date, end_date)
    
    # Assert
    assert "page_performance" in metrics
    assert "api_performance" in metrics
    assert "resource_usage" in metrics
    assert "network_performance" in metrics

def test_generate_report(monitor, tmp_path):
    # Arrange
    metrics = {
        "page_performance": {
            "pages": [
                {
                    "url": "https://test.sharepoint.com/sites/test1/page1",
                    "ttfb": 100,
                    "render": 500,
                    "visits": 1000
                }
            ],
            "aggregates": {
                "avg_ttfb": 100,
                "avg_render": 500,
                "total_visits": 1000
            }
        },
        "api_performance": {
            "endpoints": [
                {
                    "endpoint": "/api/test1",
                    "latency": 50,
                    "success_rate": 99.9,
                    "calls": 1000
                }
            ],
            "aggregates": {
                "avg_latency": 50,
                "avg_success_rate": 99.9,
                "total_calls": 1000
            }
        },
        "resource_usage": {
            "sites": [
                {
                    "site": "https://test.sharepoint.com/sites/test1",
                    "storage_used": 1024 * 1024 * 100,
                    "storage_allocated": 1024 * 1024 * 1024,
                    "files": 1000
                }
            ],
            "aggregates": {
                "total_storage_used": 1024 * 1024 * 100,
                "total_storage_allocated": 1024 * 1024 * 1024,
                "total_files": 1000
            }
        },
        "network_performance": {
            "locations": [
                {
                    "location": "US West",
                    "bandwidth": 100 * 1024 * 1024,
                    "latency": 50,
                    "packet_loss": 0.1
                }
            ],
            "aggregates": {
                "avg_bandwidth": 100 * 1024 * 1024,
                "avg_latency": 50,
                "avg_packet_loss": 0.1
            }
        }
    }
    
    # Act
    report_path = monitor.generate_report(metrics, "html")
    
    # Assert
    assert Path(report_path).exists()
    with open(report_path) as f:
        content = f.read()
        assert "SharePoint Performance Report" in content
        assert "Page Performance" in content
        assert "API Performance" in content
        assert "Resource Usage" in content
        assert "Network Performance" in content
