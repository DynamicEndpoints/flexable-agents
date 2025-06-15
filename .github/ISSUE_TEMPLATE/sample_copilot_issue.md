# Sample Issue: Add M365 Teams Channel Message Deletion Tool

**This is a sample issue demonstrating best practices for GitHub Copilot interactions**

## 🤖 Copilot Task

### Goal
Create a new MCP tool that allows users to delete messages from Microsoft Teams channels via the Microsoft Graph API.

### Detailed Requirements

1. **Create the tool function in `src/tools/m365_tools.py`**:
   - Function name: `M365_Teams_Delete_Message`
   - Input parameters:
     - `team_id: str` - The ID of the Teams team
     - `channel_id: str` - The ID of the channel within the team
     - `message_id: str` - The ID of the message to delete
   - Processing: Use Microsoft Graph API to delete the specified message
   - Output: Return a JSON object with deletion confirmation
   - Error Handling: Handle authentication errors, not found errors, permission errors

2. **Add the tool decorator and registration**:
   - Use the `@tool` decorator with appropriate metadata
   - Include the `@with_error_handling` decorator for consistent error responses
   - Add proper docstring with parameter descriptions

3. **Add unit tests in `tests/test_m365_tools.py`**:
   - Test successful message deletion
   - Test error cases (invalid IDs, permission denied, message not found)
   - Mock the Microsoft Graph API calls using `unittest.mock`

4. **Update tool registration**:
   - Ensure the new tool is registered in `src/tools/__init__.py`

### Files to Modify
- `src/tools/m365_tools.py` - Add the new tool function
- `tests/test_m365_tools.py` - Add unit tests (create if doesn't exist)
- `src/tools/__init__.py` - Ensure tool registration

### Context

**Relevant Code Snippet** (existing pattern to follow):
```python
@tool(
    name="M365_Teams_Send_Message",
    description="Send a message to a Microsoft Teams channel",
    # ... other metadata
)
@with_error_handling("M365_Teams_Send_Message")
async def teams_send_message(team_id: str, channel_id: str, content: str) -> dict:
    """
    Send a message to a Microsoft Teams channel.
    
    Args:
        team_id: The ID of the Teams team
        channel_id: The ID of the channel within the team  
        content: The message content to send
    
    Returns:
        dict: Message details including ID and timestamp
    """
    # Implementation here...
```

**Microsoft Graph API Reference**: 
- Endpoint: `DELETE /teams/{team-id}/channels/{channel-id}/messages/{message-id}`
- Documentation: https://docs.microsoft.com/en-us/graph/api/chatmessage-delete

**Related Issues**: None

### Acceptance Criteria

- [ ] New tool `M365_Teams_Delete_Message` is implemented in `src/tools/m365_tools.py`
- [ ] Tool accepts `team_id`, `channel_id`, and `message_id` parameters
- [ ] Tool uses Microsoft Graph API to delete the message
- [ ] Tool returns appropriate success/error responses
- [ ] Tool includes proper docstring with type hints
- [ ] Unit tests cover success and error scenarios
- [ ] All existing tests continue to pass
- [ ] Code follows project formatting standards (Black, isort)

### Definition of Done (for Reviewer)

- [ ] Code has been reviewed for security considerations
- [ ] Manual testing performed with actual Teams environment
- [ ] Tool appears in `python -m src.cli list-tools` output
- [ ] Documentation is clear and complete

### Notes for Copilot (AI Agent)

- Follow the existing pattern for M365 tools in the same file
- Use the existing Graph client setup (likely `self.graph_client`)
- Include comprehensive error handling for Graph API responses
- Make sure to include the `time` import and `log_request_metrics` call
- Follow the existing async/await patterns in the codebase
- Use descriptive variable names and include comments for complex logic

### Task Complexity: Medium
**Reasoning**: Requires understanding of Microsoft Graph API, following existing patterns, and comprehensive testing.

### Priority: Medium
**Reasoning**: Useful feature that complements existing Teams tools, but not blocking critical functionality.

---

## Why This Is a Good Copilot Issue

This sample issue demonstrates several best practices for AI coding agents:

1. **Clear, Specific Goal**: The goal is unambiguous - create a message deletion tool
2. **Detailed Requirements**: Step-by-step breakdown with inputs, outputs, and error handling
3. **Context Provided**: Shows existing code patterns to follow
4. **Files Listed**: Specific files to modify are identified
5. **External API Info**: Links to relevant documentation
6. **Testable Criteria**: Clear acceptance criteria that can be verified
7. **Code Standards**: References to existing formatting and quality standards
8. **Security Considerations**: Mentioned in definition of done
9. **Complexity Assessment**: Helps estimate effort required
10. **Specific Instructions**: Direct guidance for the AI agent

This format helps ensure AI agents have all the context they need to produce high-quality, consistent code that integrates well with the existing codebase.
