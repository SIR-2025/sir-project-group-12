# Dialogflow CX - How to Execute a Flow Using Direct HTTPS Requests

This guide explains how to execute a specific flow in your Dialogflow CX agent using direct HTTPS requests with the `DialogflowCXDirectClient` class.

## Overview

The `DialogflowCXDirectClient` class provides a simple interface to execute Dialogflow CX flows via direct HTTPS requests, without needing the SIC framework's Dialogflow CX service.

## Requirements

```bash
pip install google-auth requests
```

## API Endpoint

The client sends POST requests to:
```
https://{LOCATION}-dialogflow.googleapis.com/v3/projects/{PROJECT_ID}/locations/{LOCATION}/agents/{AGENT_ID}/sessions/{SESSION_ID}:detectIntent
```

## Finding Your IDs

### 1. PROJECT_ID, LOCATION, AGENT_ID

**From Dialogflow CX Console URL:**
When you open your agent, the URL shows all three:
```
https://dialogflow.cloud.google.com/cx/projects/{PROJECT_ID}/locations/{LOCATION}/agents/{AGENT_ID}/...
```

**Example:**
```
https://dialogflow.cloud.google.com/cx/projects/newagent-tcmq/locations/europe-west4/agents/5079e43a-fec2-441d-bf10-f23f292fbf15/...
```
- PROJECT_ID: `newagent-tcmq`
- LOCATION: `europe-west4`
- AGENT_ID: `5079e43a-fec2-441d-bf10-f23f292fbf15`

**From google-key.json:**
The `project_id` is also available in your service account keyfile:
```json
{
  "project_id": "newagent-tcmq",
  ...
}
```

### 2. FLOW_ID

**From Dialogflow CX Console:**
1. Click on "Flows" in the left sidebar
2. Click on your flow (e.g., "demo_cycle_1")
3. The URL shows the FLOW_ID:
```
.../flows/{FLOW_ID}/...
```

**Example:**
- URL: `.../flows/c5eacb8c-2410-47b0-a51a-02c96c998c08/...`
- FLOW_ID: `c5eacb8c-2410-47b0-a51a-02c96c998c08`
- Flow Name: `demo_cycle_1`

**From API Response:**
After any request, the response shows the current flow:
```json
{
  "queryResult": {
    "currentFlow": {
      "displayName": "demo_cycle_1",
      "name": "projects/.../flows/c5eacb8c-2410-47b0-a51a-02c96c998c08"
    }
  }
}
```

## Using the DialogflowCXDirectClient

### 1. Initialize the Client

```python
from dialogflow_cx_direct_request import DialogflowCXDirectClient

client = DialogflowCXDirectClient(
    keyfile_path="google-key.json",
    agent_id="5079e43a-fec2-441d-bf10-f23f292fbf15",
    location="europe-west4"
)
```

### 2. Execute a Flow

The simplest way to start a flow is using `execute_flow()`:

```python
import uuid

# Generate a session ID
session_id = str(uuid.uuid4())

# Execute the flow from START_PAGE
flow_id = "c5eacb8c-2410-47b0-a51a-02c96c998c08"  # demo_cycle_1

response = client.execute_flow(
    flow_id=flow_id,
    session_id=session_id,
    initial_text="hi",
    parameters={}  # Optional: pre-fill parameters
)
```

### 3. Parse the Response

```python
parsed = client.parse_response(response)

# Access parsed information
print(f"Flow: {parsed['current_flow_name']}")
print(f"Page: {parsed['current_page_name']}")
print(f"Intent: {parsed['intent']}")
print(f"Fulfillment messages: {parsed['fulfillment_messages']}")
print(f"Parameters: {parsed['parameters']}")
```

### 4. Continue the Conversation

```python
# Send user input in the same session
response = client.detect_intent_text(
    text="user's response here",
    session_id=session_id  # Same session maintains context
)

parsed = client.parse_response(response)
```

## Complete Example

```python
from dialogflow_cx_direct_request import DialogflowCXDirectClient
import uuid

# Configuration
KEYFILE_PATH = "google-key.json"
AGENT_ID = "5079e43a-fec2-441d-bf10-f23f292fbf15"
LOCATION = "europe-west4"

# Flow IDs
FLOWS = {
    "demo_cycle_1": "c5eacb8c-2410-47b0-a51a-02c96c998c08",
    "demo_cycle_2": "35b11713-c8ba-4c88-968a-1acbd74a43a8",
}

# Initialize client
client = DialogflowCXDirectClient(
    keyfile_path=KEYFILE_PATH,
    agent_id=AGENT_ID,
    location=LOCATION
)

# Select flow
flow_id = FLOWS["demo_cycle_1"]
session_id = str(uuid.uuid4())

# Execute flow
response = client.execute_flow(
    flow_id=flow_id,
    session_id=session_id
)

# Parse and display
parsed = client.parse_response(response)
print(f"Agent: {parsed['fulfillment_messages'][0]}")

# Continue conversation
user_input = input("You: ")
response = client.detect_intent_text(
    text=user_input,
    session_id=session_id
)
parsed = client.parse_response(response)
print(f"Agent: {parsed['fulfillment_messages'][0]}")
```

## Available Methods

### `execute_flow(flow_id, session_id=None, initial_text="hi", parameters=None)`

Executes a flow from its START_PAGE.

**Parameters:**
- `flow_id` (str): The flow ID (UUID)
- `session_id` (str, optional): Session ID (generates random UUID if None)
- `initial_text` (str): Initial text to trigger the flow (default: "hi")
- `parameters` (dict, optional): Initial parameters to pass to the flow

**Returns:** dict - Raw Dialogflow CX response

### `detect_intent_text(text, session_id, language_code="en", current_page=None, parameters=None)`

Sends a text query to Dialogflow CX.

**Parameters:**
- `text` (str): User input text
- `session_id` (str): Session ID for conversation context
- `language_code` (str): Language code (default: "en")
- `current_page` (str, optional): Full page path to navigate to
- `parameters` (dict, optional): Parameters to pass

**Returns:** dict - Raw Dialogflow CX response

### `parse_response(response)`

Parses the Dialogflow CX response into a structured format.

**Parameters:**
- `response` (dict): Raw response from Dialogflow CX

**Returns:** dict with keys:
- `transcript`: User's transcript
- `parameters`: Collected parameters
- `intent`: Detected intent name
- `intent_confidence`: Confidence score
- `fulfillment_messages`: List of text responses
- `payload_messages`: List of payload objects
- `current_page_name`: Current page display name
- `current_flow_name`: Current flow display name
- `end_interaction`: Boolean indicating if conversation ended

## Naming Flows

When creating different flows (cycles), use descriptive names:
- `demo_cycle_1` → First conversation cycle
- `demo_cycle_2` → Second conversation cycle
- `demo_cycle_3` → Third conversation cycle

Each flow will have its own unique FLOW_ID (UUID) generated by Dialogflow CX.

## Request Body Structure

Under the hood, the client constructs requests like this:

```json
{
  "queryInput": {
    "text": {
      "text": "hi"
    },
    "languageCode": "en"
  },
  "queryParams": {
    "currentPage": "projects/{PROJECT_ID}/locations/{LOCATION}/agents/{AGENT_ID}/flows/{FLOW_ID}/pages/START_PAGE"
  }
}
```

## Quick Reference

| What You Need | Where to Find It | Example |
|---------------|------------------|---------|
| PROJECT_ID | Dialogflow CX Console URL or google-key.json | `newagent-tcmq` |
| LOCATION | Dialogflow CX Console URL | `europe-west4` |
| AGENT_ID | Dialogflow CX Console URL | `5079e43a-fec2-441d-bf10-f23f292fbf15` |
| FLOW_ID | Flow page URL in console | `c5eacb8c-2410-47b0-a51a-02c96c998c08` |
| Starting Page | Always use this | `START_PAGE` |

## Important Notes

1. **Session Management**: Use the same `session_id` throughout a conversation to maintain context.

2. **Flow Execution**: To execute a flow from the beginning, use `execute_flow()` which automatically navigates to `START_PAGE`.

3. **Parameters**: When manually setting `currentPage`, previous session state is ignored. Pass any needed parameters explicitly.

4. **Authentication**: The client automatically handles Google Cloud authentication using your service account keyfile.

5. **Error Handling**: The client raises exceptions for HTTP errors. Wrap calls in try-except blocks for production use.