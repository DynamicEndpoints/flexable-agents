import pytest
import asyncio
from unittest.mock import MagicMock, patch
import json
from pathlib import Path
from datetime import datetime, timedelta

from src.monitoring.sharepoint_monitor import SharePointMonitor

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
    return SharePointMonitor(
        graph_client=mock_graph_client,
        config_path=str(Path(__file__).parent.parent / "config/templates/sharepoint_dev_config_template.json"),
        output_dir=str(tmp_path)
    )

@pytest.mark.asyncio
async def test_collect_site_usage(monitor, mock_graph_client):
    # Arrange
    mock_graph_client._make_request.return_value = [
        {
            "siteUrl": "https://test.sharepoint.com/sites/test1",
            "visitCount": 100,
            "lastActivityDate": ["user1@test.com", "user2@test.com"],
            "fileViewedOrEdited": 50,
            "filesSharedExternally": 10,
            "filesSynced": 20
        },
        {
            "siteUrl": "https://test.sharepoint.com/sites/test2",
            "visitCount": 200,
            "lastActivityDate": ["user2@test.com", "user3@test.com"],
            "fileViewedOrEdited": 75,
            "filesSharedExternally": 15,
            "filesSynced": 30
        }
    ]
    
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    # Act
    usage = await monitor._collect_site_usage(start_date, end_date)
    
    # Assert
    assert usage["visits"]["total"] == 300
    assert len(usage["visits"]["by_site"]) == 2
    assert usage["active_users"]["total"] == 3
    assert usage["file_activity"]["viewed"] == 125
    assert usage["file_activity"]["shared"] == 25
    assert usage["file_activity"]["synced"] == 50

@pytest.mark.asyncio
async def test_collect_storage_metrics(monitor, mock_graph_client):
    # Arrange
    mock_graph_client._make_request.return_value = [
        {
            "siteUrl": "https://test.sharepoint.com/sites/test1",
            "storageUsedInBytes": 1024 * 1024 * 100,  # 100 MB
            "storageAllocatedInBytes": 1024 * 1024 * 1024  # 1 GB
        },
        {
            "siteUrl": "https://test.sharepoint.com/sites/test2",
            "storageUsedInBytes": 1024 * 1024 * 200,  # 200 MB
            "storageAllocatedInBytes": 1024 * 1024 * 1024  # 1 GB
        }
    ]
    
    # Act
    storage = await monitor._collect_storage_metrics()
    
    # Assert
    assert storage["total"] == 1024 * 1024 * 300  # 300 MB
    assert len(storage["by_site"]) == 2
    assert storage["by_site"]["https://test.sharepoint.com/sites/test1"]["used"] == 1024 * 1024 * 100

@pytest.mark.asyncio
async def test_collect_performance_metrics(monitor, mock_graph_client):
    # Arrange
    mock_graph_client._make_request.return_value = [
        {
            "pageUrl": "https://test.sharepoint.com/sites/test1/page1",
            "averageTimeToFirstByte": 100,
            "averageTimeToFullyLoaded": 500
        },
        {
            "pageUrl": "https://test.sharepoint.com/sites/test1/page2",
            "averageTimeToFirstByte": 150,
            "averageTimeToFullyLoaded": 600
        }
    ]
    
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    # Act
    performance = await monitor._collect_performance_metrics(start_date, end_date)
    
    # Assert
    assert performance["page_load_times"]["average"] == 125
    assert len(performance["page_load_times"]["by_page"]) == 2

@pytest.mark.asyncio
async def test_collect_security_metrics(monitor, mock_graph_client):
    # Arrange
    mock_graph_client._make_request.return_value = [
        {"severity": "high"},
        {"severity": "medium"},
        {"severity": "medium"},
        {"severity": "low"}
    ]
    
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    # Act
    security = await monitor._collect_security_metrics(start_date, end_date)
    
    # Assert
    assert security["alerts"]["total"] == 4
    assert security["alerts"]["by_severity"]["high"] == 1
    assert security["alerts"]["by_severity"]["medium"] == 2
    assert security["alerts"]["by_severity"]["low"] == 1

@pytest.mark.asyncio
async def test_collect_metrics(monitor, mock_graph_client):
    # Arrange
    mock_graph_client._make_request.side_effect = [
        # Site usage
        [
            {
                "siteUrl": "https://test.sharepoint.com/sites/test1",
                "visitCount": 100,
                "lastActivityDate": ["user1@test.com"],
                "fileViewedOrEdited": 50,
                "filesSharedExternally": 10,
                "filesSynced": 20
            }
        ],
        # Storage
        [
            {
                "siteUrl": "https://test.sharepoint.com/sites/test1",
                "storageUsedInBytes": 1024 * 1024 * 100,
                "storageAllocatedInBytes": 1024 * 1024 * 1024
            }
        ],
        # Performance
        [
            {
                "pageUrl": "https://test.sharepoint.com/sites/test1/page1",
                "averageTimeToFirstByte": 100,
                "averageTimeToFullyLoaded": 500
            }
        ],
        # Security
        [
            {"severity": "high"},
            {"severity": "medium"}
        ]
    ]
    
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    # Act
    metrics = await monitor.collect_metrics(start_date, end_date)
    
    # Assert
    assert "site_usage" in metrics
    assert "storage" in metrics
    assert "performance" in metrics
    assert "security" in metrics

def test_generate_report(monitor, tmp_path):
    # Arrange
    metrics = {
        "site_usage": {
            "visits": {"total": 300, "by_site": {"site1": 100, "site2": 200}},
            "active_users": {"total": 3},
            "file_activity": {"viewed": 125, "shared": 25, "synced": 50}
        },
        "storage": {
            "total": 1024 * 1024 * 300,
            "by_site": {
                "site1": {"used": 1024 * 1024 * 100, "allocated": 1024 * 1024 * 1024},
                "site2": {"used": 1024 * 1024 * 200, "allocated": 1024 * 1024 * 1024}
            }
        },
        "performance": {
            "page_load_times": {
                "average": 125,
                "by_page": {
                    "page1": {"ttfb": 100, "render": 500},
                    "page2": {"ttfb": 150, "render": 600}
                }
            }
        },
        "security": {
            "alerts": {
                "total": 4,
                "by_severity": {"high": 1, "medium": 2, "low": 1}
            }
        }
    }
    
    # Act
    report_path = monitor.generate_report(metrics, "html")
    
    # Assert
    assert Path(report_path).exists()
    with open(report_path) as f:
        content = f.read()
        assert "SharePoint Monitoring Report" in content
        assert "Site Usage" in content
        assert "Storage" in content
        assert "Performance" in content
        assert "Security" in content
