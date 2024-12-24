# Microsoft 365 Admin Agent Documentation

## Overview
The Microsoft 365 Admin Agent automates administrative tasks in Microsoft 365 environments. It manages users, licenses, groups, and security settings through Microsoft Graph API and PowerShell cmdlets.

## Features

### User Management
- User creation
- License assignment
- Group management
- Access control

### License Management
- License allocation
- Usage tracking
- Subscription management
- Cost optimization

### Security Configuration
- Conditional access
- MFA setup
- Security policies
- Compliance settings

### Group Management
- Group creation
- Membership control
- Policy assignment
- Team provisioning

## Usage

### Basic Setup
```python
from src.agents.m365_admin_agent import M365AdminAgent

agent = M365AdminAgent(
    credentials=m365_credentials,
    tenant_id="your-tenant-id",
    config_path="config/m365_config.json"
)
```

### User Management
```python
# Create new user
user = await agent.create_user(
    display_name="John Doe",
    email="john.doe@company.com",
    department="IT"
)

# Assign license
await agent.assign_license(
    user_id=user["id"],
    license_sku="E3"
)
```

## Configuration

### Sample Configuration
```json
{
    "m365": {
        "default_domain": "company.com",
        "license_defaults": {
            "IT": "E5",
            "Sales": "E3",
            "Marketing": "E3"
        },
        "security": {
            "mfa_required": true,
            "conditional_access": true
        },
        "groups": {
            "auto_create": true,
            "naming_convention": "dept-{department}-{type}"
        }
    }
}
```

## Features Details

### User Management
- Account creation
- Profile updates
- Password resets
- Account deactivation

### License Management
- SKU assignment
- Usage monitoring
- Cost tracking
- Optimization

### Security
- MFA enforcement
- Access policies
- Security alerts
- Compliance checks

### Groups
- Dynamic groups
- Team creation
- Policy assignment
- Resource access

## Best Practices

### User Setup
1. Use naming conventions
2. Assign proper licenses
3. Configure MFA
4. Set access policies

### License Management
1. Track usage
2. Optimize costs
3. Review assignments
4. Plan capacity

### Security Configuration
1. Enable MFA
2. Set access policies
3. Monitor alerts
4. Review compliance

## Integration

### Azure AD Integration
```python
# Sync with Azure AD
await agent.sync_azure_ad(
    sync_type="Delta",
    include_groups=True
)
```

### Teams Integration
```python
# Create team
await agent.create_team(
    name="IT Projects",
    members=["user1@company.com", "user2@company.com"],
    template="project"
)
```

## PowerShell Integration

### Exchange Online
```python
# Configure mailbox
await agent.configure_mailbox(
    user_id="user@company.com",
    settings={
        "quota": "100GB",
        "archive": True
    }
)
```

### SharePoint Online
```python
# Configure OneDrive
await agent.configure_onedrive(
    user_id="user@company.com",
    quota="1TB"
)
```

## API Reference

### M365AdminAgent Class
```python
class M365AdminAgent:
    def __init__(
        self,
        credentials: Any,
        tenant_id: str,
        config_path: str
    ):
        """Initialize M365 Admin Agent"""
        pass

    async def create_user(
        self,
        display_name: str,
        email: str,
        department: str
    ) -> Dict[str, Any]:
        """Create new user"""
        pass

    async def assign_license(
        self,
        user_id: str,
        license_sku: str
    ) -> Dict[str, Any]:
        """Assign license to user"""
        pass

    async def create_group(
        self,
        name: str,
        type: str,
        members: List[str]
    ) -> Dict[str, Any]:
        """Create new group"""
        pass

    async def configure_security(
        self,
        policy_name: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Configure security policy"""
        pass
```

## Troubleshooting

### Common Issues
1. User creation failures
   - Check permissions
   - Verify licenses
   - Review quotas

2. License assignment issues
   - Check availability
   - Verify compatibility
   - Review dependencies

3. Security configuration problems
   - Check policy settings
   - Verify conditions
   - Review conflicts

### Error Handling
```python
try:
    await agent.create_user(...)
except LicenseError as e:
    # Handle license issues
    pass
except SecurityError as e:
    # Handle security issues
    pass
except ConfigurationError as e:
    # Handle configuration issues
    pass
```

## Monitoring and Reporting

### Usage Reports
```python
# Generate usage report
report = await agent.generate_report(
    report_type="UserActivity",
    start_date=start_date,
    end_date=end_date
)
```

### License Reports
```python
# Generate license report
report = await agent.generate_license_report(
    include_costs=True,
    group_by="Department"
)
```

## Contributing
1. Follow coding standards
2. Add unit tests
3. Update documentation
4. Submit pull requests

## License
MIT License - See LICENSE file for details
