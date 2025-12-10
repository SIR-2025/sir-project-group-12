"""
Direct HTTPS requests to execute Dialogflow CX flows.

This script allows you to execute any flow in your Dialogflow CX agent using direct HTTPS requests.
Simply configure the variables at the top of main() and run the script.

Requirements:
    pip install google-auth requests

Setup:
    1. Place your Google Cloud keyfile in the same directory (google-key.json)
    2. Update the configuration variables in main()
    3. Run: python dialogflow_cx_direct_request.py
"""

import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import uuid


class DialogflowCXDirectClient:
    """Client for making direct HTTPS requests to Dialogflow CX."""
    
    def __init__(self, keyfile_path, agent_id, location):
        """
        Initialize the Dialogflow CX client.
        
        Args:
            keyfile_path: Path to the Google Cloud service account keyfile
            agent_id: The Dialogflow CX agent ID
            location: The agent location (e.g., 'europe-west4')
        """
        self.agent_id = agent_id
        self.location = location
        
        # Load the service account credentials
        with open(keyfile_path) as f:
            keyfile_json = json.load(f)
        
        self.project_id = keyfile_json.get("project_id")
        
        # Create credentials for Google Cloud API
        self.credentials = service_account.Credentials.from_service_account_info(
            keyfile_json,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        
        # Base URL for Dialogflow CX API
        self.base_url = f"https://{location}-dialogflow.googleapis.com/v3"
        
        print(f"Initialized client for project: {self.project_id}")
        print(f"Agent ID: {agent_id}")
        print(f"Location: {location}")
    
    def _get_access_token(self):
        """Get a fresh access token from the credentials."""
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        return self.credentials.token
    
    def detect_intent_text(self, text, session_id, language_code="en", current_page=None, parameters=None):
        """
        Send a text query to Dialogflow CX and get the intent detection result.
        
        Args:
            text: The text input from the user
            session_id: Session ID to maintain conversation context
            language_code: Language code (default: "en")
            current_page: Optional page resource path to direct the flow
            parameters: Optional dict of parameters to pass to the flow
        
        Returns:
            dict: The response from Dialogflow CX
        """
        # Construct the endpoint URL
        session_path = f"{self.base_url}/projects/{self.project_id}/locations/{self.location}/agents/{self.agent_id}/sessions/{session_id}:detectIntent"
        
        # Construct the request body
        request_body = {
            "queryInput": {
                "text": {
                    "text": text
                },
                "languageCode": language_code
            }
        }
        
        # Add optional query parameters if provided
        if current_page or parameters:
            request_body["queryParams"] = {}
            if current_page:
                request_body["queryParams"]["currentPage"] = current_page
            if parameters:
                request_body["queryParams"]["parameters"] = parameters
        
        # Get access token for authentication
        access_token = self._get_access_token()
        
        # Set up headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Make the POST request
        response = requests.post(
            session_path,
            headers=headers,
            json=request_body
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        return response.json()
    
    def parse_response(self, response):
        """
        Parse and extract useful information from the Dialogflow CX response.
        
        Args:
            response: The JSON response from Dialogflow CX
        
        Returns:
            dict: Parsed information including intent, transcript, fulfillment, etc.
        """
        query_result = response.get("queryResult", {})
        
        parsed = {
            "transcript": query_result.get("transcript", ""),
            "language_code": query_result.get("languageCode", ""),
            "parameters": query_result.get("parameters", {}),
            "intent": None,
            "intent_confidence": None,
            "fulfillment_messages": [],
            "payload_messages": [],
            "current_page_name": query_result.get("currentPage", {}).get("displayName", ""),
            "current_page_path": query_result.get("currentPage", {}).get("name", ""),
            "current_flow_name": query_result.get("currentFlow", {}).get("displayName", ""),
            "current_flow_path": query_result.get("currentFlow", {}).get("name", ""),
            "response_id": response.get("responseId", ""),
            "end_interaction": False
        }
        
        # Extract intent information
        if "intent" in query_result and query_result["intent"]:
            intent_name = query_result["intent"].get("displayName", "")
            parsed["intent"] = intent_name
        
        # Extract intent detection confidence
        if "intentDetectionConfidence" in query_result:
            parsed["intent_confidence"] = query_result["intentDetectionConfidence"]
        
        # Extract fulfillment messages and payloads
        response_messages = query_result.get("responseMessages", [])
        for msg in response_messages:
            if "text" in msg:
                texts = msg["text"].get("text", [])
                parsed["fulfillment_messages"].extend(texts)
            elif "payload" in msg:
                parsed["payload_messages"].append(msg["payload"])
            elif "endInteraction" in msg:
                parsed["end_interaction"] = True
        
        return parsed
    
    def execute_flow(self, flow_id, session_id=None, initial_text="hi", parameters=None):
        """
        Execute a flow from its START_PAGE.
        
        Args:
            flow_id: The flow ID (UUID)
            session_id: Session ID (generates random if None)
            initial_text: Initial text to trigger the flow (default: "hi")
            parameters: Optional dict of initial parameters
        
        Returns:
            dict: The response from Dialogflow CX
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        if parameters is None:
            parameters = {}
        
        # Construct the flow's START_PAGE path
        flow_start_page = f"projects/{self.project_id}/locations/{self.location}/agents/{self.agent_id}/flows/{flow_id}/pages/START_PAGE"
        
        print(f"\nExecuting flow: {flow_id}")
        print(f"Session ID: {session_id}")
        
        return self.detect_intent_text(
            text=initial_text,
            session_id=session_id,
            current_page=flow_start_page,
            parameters=parameters
        )


def run_interactive_conversation(client, flow_id, initial_parameters=None):
    """
    Run an interactive conversation with the specified flow.
    
    Args:
        client: DialogflowCXDirectClient instance
        flow_id: The flow ID to execute
        initial_parameters: Optional dict of initial parameters
    """
    if initial_parameters is None:
        initial_parameters = {}
    
    session_id = str(uuid.uuid4())
    
    print("\n" + "=" * 70)
    print("DIALOGFLOW CX INTERACTIVE MODE")
    print("=" * 70)
    print(f"Flow ID: {flow_id}")
    print(f"Session ID: {session_id}")
    print("\nCommands:")
    print("  - Type 'quit' or 'exit' to end")
    print("  - Type 'restart' to start a new session")
    print("=" * 70)
    
    # Execute the flow
    response = client.execute_flow(
        flow_id=flow_id,
        session_id=session_id,
        parameters=initial_parameters
    )
    parsed = client.parse_response(response)
    
    # Display initial response
    display_response(parsed)
    
    # Interactive loop
    turn_number = 1
    while True:
        try:
            # Get user input
            user_input = input(f"\nYOU (turn {turn_number}): ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit']:
                print("\nEnding conversation. Goodbye!")
                break
            
            # Check for restart command
            if user_input.lower() == 'restart':
                print("\nRestarting conversation...")
                session_id = str(uuid.uuid4())
                response = client.execute_flow(
                    flow_id=flow_id,
                    session_id=session_id,
                    parameters=initial_parameters
                )
                parsed = client.parse_response(response)
                display_response(parsed)
                turn_number = 1
                continue
            
            if not user_input:
                print("Please enter a message.")
                continue
            
            # Send user input to Dialogflow
            response = client.detect_intent_text(
                text=user_input,
                session_id=session_id
            )
            turn_number += 1
            
            # Parse and display response
            parsed = client.parse_response(response)
            display_response(parsed)
            
            # If conversation ended, offer to restart
            if parsed['end_interaction'] or parsed['current_page_name'] == 'End Session':
                print("\nConversation has ended.")
                restart_choice = input("Start a new conversation? (yes/no): ").strip().lower()
                if restart_choice in ['yes', 'y']:
                    session_id = str(uuid.uuid4())
                    response = client.execute_flow(
                        flow_id=flow_id,
                        session_id=session_id,
                        parameters=initial_parameters
                    )
                    parsed = client.parse_response(response)
                    display_response(parsed)
                    turn_number = 1
                else:
                    print("Goodbye!")
                    break
            
        except KeyboardInterrupt:
            print("\n\nConversation interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
            break


def display_response(parsed):
    """Display the parsed response in a formatted way."""
    print("\n" + "-" * 70)
    print("AGENT RESPONSE:")
    
    # Display text messages
    if parsed['fulfillment_messages']:
        for msg in parsed['fulfillment_messages']:
            print(f"  {msg}")
    else:
        print("  [No text response]")
    
    # Display payload messages
    if parsed['payload_messages']:
        print("\nPAYLOAD/ROBOT COMMANDS:")
        for payload in parsed['payload_messages']:
            print(f"  {json.dumps(payload, indent=2)}")
    
    # Show conversation state
    print(f"\nCONVERSATION STATE:")
    print(f"  Flow: {parsed['current_flow_name']}")
    print(f"  Page: {parsed['current_page_name']}")
    
    if parsed['intent']:
        print(f"  Intent: {parsed['intent']} (confidence: {parsed['intent_confidence']})")
    
    # Show collected parameters
    if parsed['parameters']:
        print(f"\n  COLLECTED PARAMETERS:")
        for key, value in parsed['parameters'].items():
            print(f"    {key}: {value}")
    
    if parsed['end_interaction']:
        print("\n  [END OF INTERACTION]")
    
    print("-" * 70)


def main():
    """
    Main function - Configure your agent and flow here.
    """
    
    # ==================== CONFIGURATION ====================
    # Update these values for your agent
    
    # Google Cloud credentials file (in same directory)
    KEYFILE_PATH = "google-key.json"
    
    # Agent configuration (find these in Dialogflow CX console URL)
    AGENT_ID = "5079e43a-fec2-441d-bf10-f23f292fbf15"
    LOCATION = "europe-west4"
    
    # Flow IDs (find these in Dialogflow CX console)
    # Navigate to your flow and copy the ID from the URL
    FLOWS = {
        "demo_cycle_1": "c5eacb8c-2410-47b0-a51a-02c96c998c08",
        "demo_cycle_2": "35b11713-c8ba-4c88-968a-1acbd74a43a8",
        # Add more flows here as needed
        # "your_flow_name": "your-flow-id-here",
    }
    
    # Select which flow to execute
    SELECTED_FLOW = "demo_cycle_1"
    
    # Optional: Pre-fill parameters (usually leave empty)
    INITIAL_PARAMETERS = {
        # "parameter_name": "value",
    }
    
    # ==================== EXECUTION ====================
    
    # Initialize the client
    client = DialogflowCXDirectClient(
        keyfile_path=KEYFILE_PATH,
        agent_id=AGENT_ID,
        location=LOCATION
    )
    
    # Get the flow ID
    flow_id = FLOWS[SELECTED_FLOW]
    
    # Run the interactive conversation
    run_interactive_conversation(
        client=client,
        flow_id=flow_id,
        initial_parameters=INITIAL_PARAMETERS
    )


if __name__ == "__main__":
    main()
