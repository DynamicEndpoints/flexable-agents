# Intranet Workflow Documentation

## Overview
The Intranet Workflow automates the creation and configuration of a modern SharePoint intranet solution. It includes hub sites, department sites, news sites, Power Apps integration, and analytics.

## Features

### Site Architecture
- Hub site creation
- Department subsites
- News site configuration
- Document centers
- Team sites

### Power Platform Integration
- Employee directory Power App
- Automated workflows
- Business process automation
- Analytics dashboard

### Content Management
- Navigation structure
- Content types
- Document templates
- Metadata schemas

### Security
- Permission management
- Access control
- Compliance settings
- Audit logging

## Usage

### Basic Setup
```python
from src.workflows.intranet_workflow import IntranetWorkflow

workflow = IntranetWorkflow(
    m365_agent=m365_agent,
    sharepoint_dev_agent=sharepoint_dev_agent,
    config_path="config/intranet_config.json"
)
```

### Creating Intranet
```python
# Create complete intranet solution
result = await workflow.create_intranet(
    organization_name="Contoso",
    departments=["HR", "IT", "Finance"]
)
```

## Configuration

### Sample Configuration
```json
{
    "intranet": {
        "hub_site": {
            "template": "CommunicationSite",
            "features": {
                "news": true,
                "search": true,
                "social": true
            }
        },
        "department_sites": {
            "template": "TeamSite",
            "features": {
                "library": true,
                "calendar": true,
                "tasks": true
            }
        }
    }
}
```

## Components Created

### Hub Site
- Global navigation
- Company news
- Search center
- Common resources

### Department Sites
- Team collaboration
- Document management
- Project tracking
- Team calendar

### Power Apps
- Employee directory
- Room booking
- Help desk
- Asset tracking

### Power BI
- Site usage analytics
- Content engagement
- User adoption
- Performance metrics

## Best Practices

### Site Structure
1. Plan hierarchy carefully
2. Use consistent naming
3. Configure navigation
4. Implement metadata

### Content Organization
1. Define content types
2. Create templates
3. Set up workflows
4. Configure retention

### Security Setup
1. Plan permissions
2. Use groups
3. Audit access
4. Monitor sharing

## Integration

### Microsoft Teams Integration
```python
# Connect sites to Teams
await workflow.connect_to_teams(
    site_url="https://contoso.sharepoint.com/sites/hub",
    team_name="Contoso Intranet"
)
```

### Power Platform Integration
```python
# Deploy Power Apps solution
await workflow.deploy_power_apps(
    solution_name="IntranetApps",
    environment_name="Production"
)
```

## Customization

### Theme Customization
```python
# Apply custom theme
await workflow.apply_theme(
    theme_name="Contoso Theme",
    colors={
        "primaryColor": "#0078d4",
        "backgroundColor": "#ffffff"
    }
)
```

### Navigation Customization
```python
# Configure navigation
await workflow.configure_navigation(
    hub_site_url="https://contoso.sharepoint.com/sites/hub",
    navigation_nodes=[
        {
            "title": "Home",
            "url": "/sites/hub"
        },
        {
            "title": "Departments",
            "url": "/sites/departments"
        }
    ]
)
```

## Troubleshooting

### Common Issues
1. Site creation failures
   - Check permissions
   - Verify quotas
   - Review templates

2. Power Apps deployment issues
   - Check connections
   - Verify licenses
   - Test data sources

3. Integration problems
   - Validate endpoints
   - Check authentication
   - Review configurations

## API Reference

### IntranetWorkflow Class
```python
class IntranetWorkflow:
    def __init__(
        self,
        m365_agent: M365AdminAgent,
        sharepoint_dev_agent: SharePointDevAgent,
        config_path: str
    ):
        """Initialize Intranet Workflow"""
        pass

    async def create_intranet(
        self,
        organization_name: str,
        departments: List[str]
    ) -> Dict[str, Any]:
        """Create intranet solution"""
        pass

    async def deploy_power_apps(
        self,
        solution_name: str,
        environment_name: str
    ) -> Dict[str, Any]:
        """Deploy Power Apps solutions"""
        pass
```

## Contributing
1. Follow coding standards
2. Add unit tests
3. Update documentation
4. Submit pull requests

## License
MIT License - See LICENSE file for details
