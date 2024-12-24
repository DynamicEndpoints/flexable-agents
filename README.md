# Intelligent Customer Service System

A comprehensive, AI-powered customer service platform built with Claude 3 and advanced NLP capabilities. This system provides multilingual support, sentiment analysis, automated follow-ups, and detailed analytics for modern customer service operations.

## 🌟 Features

### 🤖 AI-Powered Agents

#### EnhancedCustomerServiceAgent
- **Multilingual Support**: Handles inquiries in 10+ languages
- **Sentiment Analysis**: Real-time emotion detection and response
- **Knowledge Base Integration**: Smart article search and suggestions
- **Automated Follow-ups**: Priority-based scheduling
- **Satisfaction Surveys**: Automated feedback collection
- **Escalation Management**: Multi-tier support system

#### CreativeAgent
- **Content Generation**: Poetry, stories, and creative writing
- **Image Analysis**: Visual content interpretation
- **Emotional Intelligence**: Sentiment-aware responses
- **Style Adaptation**: Multiple writing styles and tones

### 📊 Analytics & Visualization

- **Sentiment Trends**: Track customer satisfaction over time
- **Language Distribution**: Monitor language preferences
- **Tool Usage Analytics**: Optimize resource allocation
- **Performance Metrics**: Track response times and resolution rates

### 🔄 Automated Workflows

- **Multi-step Processing**: Seamless inquiry handling
- **Priority Queue**: Smart task management
- **Error Recovery**: Robust exception handling
- **Audit Trails**: Comprehensive logging

## 🚀 Getting Started

### Prerequisites

```bash
# Python 3.8+ required
python -m pip install -r requirements.txt
```

### Environment Setup

1. Create a `.env` file:
```env
ANTHROPIC_API_KEY=your_api_key_here
```

2. Create required directories:
```bash
mkdir -p work_files/customer_service/analytics
```

### Basic Usage

```python
from src.agents.enhanced_customer_service_agent import EnhancedCustomerServiceAgent
from src.core.base import AgentSystem

# Initialize system
system = AgentSystem()

# Create agent
cs_agent = EnhancedCustomerServiceAgent(
    agent_id="cs_agent_1",
    work_dir="work_files/cs",
    api_keys={
        "anthropic": "your_api_key"
    }
)

# Register agent
system.register_agent(cs_agent)

# Process inquiry
result = await cs_agent.process_task(Task(
    task_id="inquiry_1",
    task_type="customer_inquiry",
    input_data="What's the status of my order?",
    parameters={"customer_id": "C1"}
))
```

### Running Workflows

```bash
# Run enhanced customer service workflow
python examples/enhanced_customer_service_workflow.py
```

## 📖 Example Workflows

### 1. Basic Customer Service

```python
# Process simple inquiry
inquiry = "What's the status of my order O2?"
result = await cs_agent.process_task(Task(
    task_id="basic_inquiry",
    task_type="customer_inquiry",
    input_data=inquiry
))
```

### 2. Multilingual Support

```python
# Process Spanish inquiry
spanish_inquiry = "¿Cómo puedo devolver mi pedido?"
result = await cs_agent.process_task(Task(
    task_id="spanish_inquiry",
    task_type="customer_inquiry",
    input_data=spanish_inquiry
))
```

### 3. Knowledge Base Search

```python
# Search articles
articles = await cs_agent.process_task(Task(
    task_id="kb_search",
    task_type="search_knowledge_base",
    input_data={
        "query": "return policy",
        "category": "returns"
    }
))
```

## 📊 Analytics Generation

The system automatically generates:

1. **Sentiment Analysis**:
   - Trend visualization
   - Emotional pattern detection
   - Priority alerts

2. **Language Statistics**:
   - Usage distribution
   - Translation metrics
   - Regional patterns

3. **Performance Metrics**:
   - Response times
   - Resolution rates
   - Tool efficiency

## 🛠 Advanced Configuration

### Custom Knowledge Base

```python
knowledge_base = {
    "returns": [
        {
            "id": "KB001",
            "title": "Return Policy",
            "content": "Our return policy..."
        }
    ]
}

cs_agent = EnhancedCustomerServiceAgent(
    # ... other params ...
    knowledge_base=knowledge_base
)
```

### Custom Language Support

```python
cs_agent = EnhancedCustomerServiceAgent(
    # ... other params ...
    supported_languages=["en", "es", "fr", "de", "it"]
)
```

## 📈 Visualization Examples

The system generates these visualizations:

1. `sentiment_trends.png`: Sentiment over time
2. `language_distribution.png`: Language usage
3. `tool_usage.png`: Tool utilization

## 🔍 Monitoring & Maintenance

### Real-time Monitoring

```python
# Get agent status
status = await cs_agent.handle_message(Message(
    sender="monitor",
    message_type="customer_service_status"
))
```

### Cleanup Operations

```python
# Process pending follow-ups
await cs_agent.process_followups()

# Archive old interactions
await cs_agent.cleanup()
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Claude 3 by Anthropic for AI capabilities
- NLTK for natural language processing
- Matplotlib and Seaborn for visualizations

## 📚 Documentation

Full documentation available in the `/docs` directory:

- `agents.md`: Detailed agent documentation
- `workflows.md`: Workflow examples
- `api.md`: API reference
- `analytics.md`: Analytics guide

## 🆘 Support

For support:
1. Check documentation
2. Search issues
3. Create new issue
4. Contact maintainers

## 🔮 Future Enhancements

1. **Real-time Chat Integration**:
   - WebSocket support
   - Chat interface
   - Mobile app integration

2. **Advanced Analytics**:
   - Predictive analytics
   - Customer behavior modeling
   - Trend forecasting

3. **Enhanced Automation**:
   - Workflow automation
   - Custom triggers
   - Integration webhooks

4. **Security Features**:
   - Role-based access
   - Audit logging
   - Data encryption

## 🎯 Agent Examples & Collaboration

### EnhancedCustomerServiceAgent Examples

1. **Order Management**
```python
# Handle order status inquiry
order_inquiry = await cs_agent.process_task(Task(
    task_id="order_status",
    task_type="customer_inquiry",
    input_data="Can you check the status of order O123?",
    parameters={"customer_id": "C1"}
))

# Process return request
return_request = await cs_agent.process_task(Task(
    task_id="return_request",
    task_type="customer_inquiry",
    input_data="I want to return my laptop, order number O456",
    parameters={
        "customer_id": "C2",
        "order_id": "O456"
    }
))

# Track shipment
tracking_inquiry = await cs_agent.process_task(Task(
    task_id="track_shipment",
    task_type="customer_inquiry",
    input_data="Where is my package? Tracking number: TRK789",
    parameters={"tracking_id": "TRK789"}
))

# Handle product complaint
complaint = await cs_agent.process_task(Task(
    task_id="product_complaint",
    task_type="customer_inquiry",
    input_data="My new phone isn't working properly",
    parameters={
        "customer_id": "C3",
        "priority": "high"
    }
))

# Process refund request
refund_request = await cs_agent.process_task(Task(
    task_id="refund_request",
    task_type="customer_inquiry",
    input_data="I'd like a refund for order O789",
    parameters={
        "customer_id": "C4",
        "order_id": "O789"
    }
))
```

### CreativeAgent Examples

1. **Story Generation**
```python
# Generate story from image
story = await creative_agent.process_task(Task(
    task_id="story_gen",
    task_type="generate_story",
    input_data={
        "image_url": "path/to/image.jpg",
        "style": "fantasy",
        "length": "medium"
    }
))

# Create character description
character = await creative_agent.process_task(Task(
    task_id="character_dev",
    task_type="create_character",
    input_data={
        "character_type": "protagonist",
        "genre": "sci-fi",
        "complexity": "high"
    }
))

# Generate poetry
poem = await creative_agent.process_task(Task(
    task_id="poetry_gen",
    task_type="generate_poetry",
    input_data={
        "theme": "nature",
        "style": "haiku",
        "mood": "peaceful"
    }
))

# Create scene description
scene = await creative_agent.process_task(Task(
    task_id="scene_desc",
    task_type="describe_scene",
    input_data={
        "image_url": "path/to/landscape.jpg",
        "perspective": "first_person",
        "tone": "mysterious"
    }
))

# Generate metaphors
metaphors = await creative_agent.process_task(Task(
    task_id="metaphor_gen",
    task_type="generate_metaphors",
    input_data={
        "concept": "time",
        "context": "philosophical",
        "count": 3
    }
))
```

### 🤝 Agent Collaboration

#### 1. Customer Service with Creative Response

```python
async def handle_creative_customer_service(
    system: AgentSystem,
    cs_agent: EnhancedCustomerServiceAgent,
    creative_agent: CreativeAgent,
    inquiry: str
) -> Dict[str, Any]:
    """Handle customer inquiry with creative response"""
    
    # First, process the customer inquiry
    cs_result = await cs_agent.process_task(Task(
        task_id="cs_inquiry",
        task_type="customer_inquiry",
        input_data=inquiry
    ))
    
    # If positive sentiment, generate creative response
    if cs_result.output["sentiment"]["compound"] > 0.5:
        creative_result = await creative_agent.process_task(Task(
            task_id="creative_response",
            task_type="generate_poetry",
            input_data={
                "theme": "customer_appreciation",
                "context": cs_result.output["response"]
            }
        ))
        
        return {
            "response": cs_result.output["response"],
            "creative_addition": creative_result.output["poem"]
        }
    
    return {"response": cs_result.output["response"]}
```

#### 2. Multi-Agent Support Ticket

```python
async def handle_complex_support_ticket(
    system: AgentSystem,
    cs_agent: EnhancedCustomerServiceAgent,
    creative_agent: CreativeAgent,
    ticket_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Process complex support ticket with multiple agents"""
    
    # Get customer history
    history = await cs_agent.process_task(Task(
        task_id="get_history",
        task_type="get_customer_history",
        input_data={"customer_id": ticket_data["customer_id"]}
    ))
    
    # Generate empathetic response
    creative_response = await creative_agent.process_task(Task(
        task_id="empathy_response",
        task_type="generate_content",
        input_data={
            "tone": "empathetic",
            "context": ticket_data["issue"]
        }
    ))
    
    # Process technical solution
    solution = await cs_agent.process_task(Task(
        task_id="tech_solution",
        task_type="search_knowledge_base",
        input_data={"query": ticket_data["issue"]}
    ))
    
    return {
        "history": history.output,
        "empathetic_response": creative_response.output,
        "technical_solution": solution.output
    }
```

#### 3. Visual Content Support

```python
async def handle_visual_support(
    system: AgentSystem,
    cs_agent: EnhancedCustomerServiceAgent,
    creative_agent: CreativeAgent,
    image_url: str,
    inquiry: str
) -> Dict[str, Any]:
    """Handle support inquiry with visual content"""
    
    # Analyze image
    image_analysis = await creative_agent.process_task(Task(
        task_id="analyze_image",
        task_type="analyze_image",
        input_data={"image_url": image_url}
    ))
    
    # Generate visual description
    description = await creative_agent.process_task(Task(
        task_id="describe_image",
        task_type="describe_scene",
        input_data={
            "image_url": image_url,
            "context": inquiry
        }
    ))
    
    # Process customer inquiry with visual context
    support_response = await cs_agent.process_task(Task(
        task_id="visual_support",
        task_type="customer_inquiry",
        input_data=inquiry,
        parameters={
            "visual_context": image_analysis.output
        }
    ))
    
    return {
        "analysis": image_analysis.output,
        "description": description.output,
        "response": support_response.output
    }
```

#### 4. Satisfaction Survey with Feedback

```python
async def process_satisfaction_survey(
    system: AgentSystem,
    cs_agent: EnhancedCustomerServiceAgent,
    creative_agent: CreativeAgent,
    survey_response: Dict[str, Any]
) -> Dict[str, Any]:
    """Process customer satisfaction survey with creative feedback"""
    
    # Analyze survey sentiment
    sentiment = await cs_agent.process_task(Task(
        task_id="analyze_survey",
        task_type="analyze_sentiment",
        input_data={"text": survey_response["feedback"]}
    ))
    
    # Generate personalized response
    if sentiment.output["compound"] > 0:
        response = await creative_agent.process_task(Task(
            task_id="positive_feedback",
            task_type="generate_content",
            input_data={
                "tone": "grateful",
                "context": survey_response["feedback"]
            }
        ))
    else:
        response = await creative_agent.process_task(Task(
            task_id="improvement_feedback",
            task_type="generate_content",
            input_data={
                "tone": "apologetic",
                "context": survey_response["feedback"]
            }
        ))
    
    # Update customer record
    await cs_agent.process_task(Task(
        task_id="update_record",
        task_type="update_customer_record",
        input_data={
            "customer_id": survey_response["customer_id"],
            "survey_data": survey_response
        }
    ))
    
    return {
        "sentiment": sentiment.output,
        "response": response.output
    }
```

#### 5. Knowledge Base Enhancement

```python
async def enhance_knowledge_base(
    system: AgentSystem,
    cs_agent: EnhancedCustomerServiceAgent,
    creative_agent: CreativeAgent,
    article_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Enhance knowledge base articles with creative content"""
    
    # Generate engaging title
    title = await creative_agent.process_task(Task(
        task_id="generate_title",
        task_type="generate_content",
        input_data={
            "type": "title",
            "context": article_data["content"]
        }
    ))
    
    # Create summary
    summary = await creative_agent.process_task(Task(
        task_id="create_summary",
        task_type="generate_content",
        input_data={
            "type": "summary",
            "content": article_data["content"]
        }
    ))
    
    # Add to knowledge base
    kb_entry = await cs_agent.process_task(Task(
        task_id="add_to_kb",
        task_type="update_knowledge_base",
        input_data={
            "title": title.output["title"],
            "content": article_data["content"],
            "summary": summary.output["summary"],
            "category": article_data["category"]
        }
    ))
    
    return {
        "title": title.output,
        "summary": summary.output,
        "kb_entry": kb_entry.output
    }
```

### 🔄 Running Multiple Agents

1. **Initialize Agent System**
```python
# Create agent system
system = AgentSystem()

# Initialize agents
cs_agent = EnhancedCustomerServiceAgent(
    agent_id="cs_1",
    work_dir="work_files/cs",
    api_keys={"anthropic": "your_key"}
)

creative_agent = CreativeAgent(
    agent_id="creative_1",
    work_dir="work_files/creative",
    api_keys={"anthropic": "your_key"}
)

# Register agents
system.register_agent(cs_agent)
system.register_agent(creative_agent)
```

2. **Create Workflow Manager**
```python
class WorkflowManager:
    def __init__(self, system: AgentSystem):
        self.system = system
        self.workflows = {
            "customer_service": handle_creative_customer_service,
            "support_ticket": handle_complex_support_ticket,
            "visual_support": handle_visual_support,
            "satisfaction_survey": process_satisfaction_survey,
            "kb_enhancement": enhance_knowledge_base
        }
    
    async def run_workflow(
        self,
        workflow_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        if workflow_name not in self.workflows:
            raise ValueError(f"Unknown workflow: {workflow_name}")
        
        workflow = self.workflows[workflow_name]
        return await workflow(self.system, **kwargs)
```

3. **Execute Workflows**
```python
# Initialize workflow manager
workflow_manager = WorkflowManager(system)

# Run customer service workflow
result = await workflow_manager.run_workflow(
    "customer_service",
    inquiry="I need help with my order",
    customer_id="C1"
)

# Run visual support workflow
visual_result = await workflow_manager.run_workflow(
    "visual_support",
    image_url="path/to/image.jpg",
    inquiry="What's wrong with my product?"
)
```

4. **Monitor Performance**
```python
# Get agent status
cs_status = await cs_agent.handle_message(Message(
    sender="monitor",
    message_type="customer_service_status"
))

creative_status = await creative_agent.handle_message(Message(
    sender="monitor",
    message_type="creative_status"
))

# Process results
print(f"Customer Service: {cs_status}")
print(f"Creative Agent: {creative_status}")
```

5. **Cleanup Resources**
```python
# Cleanup agents
await cs_agent.cleanup()
await creative_agent.cleanup()

# Close system
await system.shutdown()
```

These examples demonstrate how to:
1. Use each agent independently
2. Combine agents for complex tasks
3. Create reusable workflows
4. Monitor agent performance
5. Manage system resources

Each workflow shows a different aspect of agent collaboration:
- Customer service with creative responses
- Complex support ticket handling
- Visual content analysis and support
- Survey processing with feedback
- Knowledge base enhancement

The WorkflowManager provides a structured way to:
- Organize multiple workflows
- Handle dependencies between agents
- Monitor execution
- Manage resources
- Scale the system

# 🤖 Flexible Agents System

A comprehensive, AI-powered multi-agent system built with Claude 3, featuring intelligent agents for customer service, content creation, data processing, and more. This system demonstrates advanced agent collaboration and task processing capabilities.

## 🌟 System Overview

### Core Components

1. **Agent System**
   - Task distribution
   - Message routing
   - Resource management
   - Error handling
   - Performance monitoring

2. **Base Agent**
   - Async task processing
   - Message handling
   - Tool integration
   - State management
   - Error recovery

## 🎯 Available Agents

### 1. 🎭 EnhancedCustomerServiceAgent
Advanced customer service handling with multi-language support and sentiment analysis.

**Capabilities:**
- Multi-language support (10+ languages)
- Real-time sentiment analysis
- Automated follow-ups
- Knowledge base integration
- Satisfaction surveys
- Escalation management

**Example Usage:**
```python
cs_agent = EnhancedCustomerServiceAgent(
    agent_id="cs_1",
    work_dir="work_files/cs",
    api_keys={"anthropic": "your_key"}
)

# Handle customer inquiry
result = await cs_agent.process_task(Task(
    task_type="customer_inquiry",
    input_data="What's my order status?",
    parameters={"order_id": "O123"}
))
```

### 2. 📝 CreativeAgent
Content generation and creative writing with visual capabilities.

**Capabilities:**
- Story generation
- Poetry creation
- Character development
- Scene description
- Metaphor generation
- Image-based content

**Example Usage:**
```python
creative_agent = CreativeAgent(
    agent_id="creative_1",
    work_dir="work_files/creative",
    api_keys={"anthropic": "your_key"}
)

# Generate story from image
story = await creative_agent.process_task(Task(
    task_type="generate_story",
    input_data={
        "image_url": "path/to/image.jpg",
        "style": "fantasy"
    }
))
```

### 3. 🖼️ ImageAgent
Image processing and analysis capabilities.

**Capabilities:**
- Image analysis
- Visual content generation
- Object detection
- Scene understanding
- Style transfer
- Image comparison

**Example Usage:**
```python
image_agent = ImageAgent(
    agent_id="image_1",
    work_dir="work_files/image",
    api_keys={"anthropic": "your_key"}
)

# Analyze image
analysis = await image_agent.process_task(Task(
    task_type="analyze_image",
    input_data={"image_url": "path/to/image.jpg"}
))
```

### 4. 🔄 TranslationAgent
Advanced language translation and localization.

**Capabilities:**
- Multi-language translation
- Context preservation
- Style adaptation
- Idiom handling
- Cultural adaptation
- Quality assurance

**Example Usage:**
```python
trans_agent = TranslationAgent(
    agent_id="trans_1",
    work_dir="work_files/translation",
    api_keys={"anthropic": "your_key"}
)

# Translate text
translation = await trans_agent.process_task(Task(
    task_type="translate",
    input_data={
        "text": "Hello, world!",
        "target_language": "es"
    }
))
```

### 5. 📊 DataProcessor
Data analysis and transformation capabilities.

**Capabilities:**
- Data cleaning
- Format conversion
- Statistical analysis
- Pattern recognition
- Data visualization
- Anomaly detection

**Example Usage:**
```python
data_agent = DataProcessor(
    agent_id="data_1",
    work_dir="work_files/data",
    api_keys={"anthropic": "your_key"}
)

# Process dataset
result = await data_agent.process_task(Task(
    task_type="analyze_data",
    input_data={
        "file_path": "data.csv",
        "analysis_type": "statistical"
    }
))
```

## 🤝 Agent Collaboration

### 1. Customer Service Enhancement
```python
async def enhanced_customer_service(
    system: AgentSystem,
    inquiry: str,
    image_url: str = None
) -> Dict[str, Any]:
    """Handle customer inquiry with multiple agents"""
    
    # Initialize agents
    cs_agent = system.get_agent("customer_service")
    creative_agent = system.get_agent("creative")
    image_agent = system.get_agent("image")
    
    results = {}
    
    # Process image if provided
    if image_url:
        image_analysis = await image_agent.process_task(Task(
            task_type="analyze_image",
            input_data={"image_url": image_url}
        ))
        results["image_analysis"] = image_analysis.output
    
    # Handle customer inquiry
    cs_result = await cs_agent.process_task(Task(
        task_type="customer_inquiry",
        input_data=inquiry,
        parameters={"image_context": results.get("image_analysis")}
    ))
    results["cs_response"] = cs_result.output
    
    # Generate creative response if positive sentiment
    if cs_result.output["sentiment"]["compound"] > 0.5:
        creative_result = await creative_agent.process_task(Task(
            task_id="creative_response",
            task_type="generate_poetry",
            input_data={
                "theme": "customer_appreciation",
                "context": cs_result.output["response"]
            }
        ))
        results["creative_response"] = creative_result.output
    
    return results
```

### 2. Multi-language Content Creation
```python
async def create_multilingual_content(
    system: AgentSystem,
    content_request: Dict[str, Any]
) -> Dict[str, Any]:
    """Create content in multiple languages"""
    
    # Initialize agents
    creative_agent = system.get_agent("creative")
    trans_agent = system.get_agent("translation")
    
    # Generate base content
    content = await creative_agent.process_task(Task(
        task_type="generate_content",
        input_data=content_request
    ))
    
    # Translate to target languages
    translations = {}
    for lang in content_request["target_languages"]:
        trans_result = await trans_agent.process_task(Task(
            task_type="translate",
            input_data={
                "text": content.output["content"],
                "target_language": lang
            }
        ))
        translations[lang] = trans_result.output
    
    return {
        "original": content.output,
        "translations": translations
    }
```

## 🔄 Workflow Examples

### 1. Customer Support Workflow
```python
# Initialize system
system = AgentSystem()

# Register agents
system.register_agent(EnhancedCustomerServiceAgent(...))
system.register_agent(CreativeAgent(...))
system.register_agent(ImageAgent(...))

# Create workflow
workflow = CustomerSupportWorkflow(system)

# Process customer inquiry
result = await workflow.process_inquiry(
    text="My product is damaged",
    image="damage.jpg"
)
```

### 2. Content Creation Workflow
```python
# Initialize system
system = AgentSystem()

# Register agents
system.register_agent(CreativeAgent(...))
system.register_agent(ImageAgent(...))
system.register_agent(TranslationAgent(...))

# Create workflow
workflow = ContentCreationWorkflow(system)

# Generate multi-language content
content = await workflow.create_content(
    type="blog_post",
    topic="AI Trends",
    languages=["en", "es", "fr"]
)
```

## 📊 Performance Monitoring

```python
# Get agent statistics
stats = await system.get_statistics()

# Monitor specific agent
agent_stats = await cs_agent.get_performance_metrics()

# Generate system report
report = await system.generate_report()
```

## 🛠️ Advanced Configuration

### 1. Custom Knowledge Base
```python
knowledge_base = {
    "products": [...],
    "policies": [...],
    "faqs": [...]
}

cs_agent = EnhancedCustomerServiceAgent(
    knowledge_base=knowledge_base,
    ...
)
```

### 2. Custom Workflows
```python
class CustomWorkflow(BaseWorkflow):
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Custom workflow logic
        pass
```

## 🔍 Error Handling

```python
try:
    result = await agent.process_task(task)
except AgentError as e:
    # Handle agent-specific errors
    logger.error(f"Agent error: {e}")
except SystemError as e:
    # Handle system-level errors
    logger.error(f"System error: {e}")
```

## 📈 Scaling

### 1. Horizontal Scaling
```python
# Create agent pool
pool = AgentPool(
    agent_class=EnhancedCustomerServiceAgent,
    pool_size=5
)

# Process tasks
results = await pool.process_batch(tasks)
```

### 2. Load Balancing
```python
# Create load balancer
balancer = LoadBalancer(
    strategy="round_robin",
    agents=[agent1, agent2, agent3]
)

# Process task
result = await balancer.process_task(task)
```

## 🔒 Security

1. **API Key Management**
```python
from utils.security import KeyManager

key_manager = KeyManager()
api_keys = key_manager.get_keys()
```

2. **Access Control**
```python
@requires_permission("admin")
async def sensitive_operation():
    pass
```

## 📚 Resources

- [Full Documentation](docs/README.md)
- [API Reference](docs/api.md)
- [Example Collection](examples/README.md)
- [Contributing Guide](CONTRIBUTING.md)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Run tests
5. Submit pull request

## 📝 License

MIT License - see LICENSE file for details

## Specialized Workflows

### 1. Employee Offboarding
Located in `examples/employee_offboarding_workflow.py`, this workflow automates the complete employee offboarding process:
- Disables user account and sets out-of-office message
- Removes licenses
- Sets up email forwarding to manager
- Removes from groups and teams
- Wipes company devices
- Archives data
- Generates comprehensive offboarding report

### 2. Security Audit
Located in `examples/security_audit_workflow.py`, this workflow performs comprehensive security audits:
- User audit (inactive accounts, MFA status, admin accounts)
- Device audit (compliance, encryption, updates)
- Data audit (external sharing, DLP violations)
- Automated remediation based on findings
- Configurable notifications and reporting

### 3. Compliance Monitoring
Located in `examples/compliance_monitoring_workflow.py`, this workflow ensures continuous compliance:
- Data classification and sensitivity scanning
- Policy compliance monitoring
- Access reviews (privileged roles, guest access)
- Automated remediation actions
- Compliance reporting and alerts

## Configuration Templates

### 1. M365 Configuration
Located in `config/templates/m365_config_template.json`:
- Authentication settings
- Environment configuration
- Logging preferences
- Agent-specific settings
- Workflow configurations

### 2. Workflow Templates
Located in `config/templates/workflow_templates/`:

#### Security Audit Workflow
- Audit components and checks
- Thresholds and severity levels
- Notification settings
- Remediation actions
- Reporting preferences

#### Compliance Workflow
- Data classification settings
- Policy compliance rules
- Access review scope
- Alert configuration
- Automation settings

## Agents

### 1. M365 Admin Agent
Core agent for Microsoft 365 administration:
- User management
- License management
- Group management
- Security management
- Reporting capabilities

### 2. Intune Agent
Device management specialist:
- Device compliance
- Policy management
- App management
- Configuration profiles

### 3. Exchange Agent
Email and calendar management:
- Mailbox configuration
- Calendar management
- Distribution groups
- Mail flow rules

### 4. Teams Agent
Teams workspace management:
- Team/channel management
- Meeting policies
- App management
- Security settings

### 5. Bookings Agent
Appointment and service management:
- Business management
- Staff management
- Service configuration
- Appointment handling
- Customer management

## Getting Started

1. Copy the appropriate configuration template:
```bash
cp config/templates/m365_config_template.json config/m365_config.json
```

2. Update the configuration with your credentials:
- Tenant ID
- Client ID
- Client Secret
- Environment settings

3. Choose a workflow to run:
```python
# Employee offboarding
python examples/employee_offboarding_workflow.py

# Security audit
python examples/security_audit_workflow.py

# Compliance monitoring
python examples/compliance_monitoring_workflow.py
```

## Best Practices

1. Security:
- Store credentials securely
- Use least-privilege access
- Enable audit logging
- Regular security reviews

2. Compliance:
- Regular compliance scans
- Document all changes
- Maintain audit trails
- Review access regularly

3. Automation:
- Test workflows in staging
- Monitor automated actions
- Set up alerts for failures
- Regular backup checks

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details
