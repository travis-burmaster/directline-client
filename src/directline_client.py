from dataclasses import dataclass
from typing import Optional, Dict, Any
import requests
import time
import os
from dotenv import load_dotenv
from smolagents import HfApiModel, DuckDuckGoSearchTool, tool, ToolCallingAgent

@dataclass
class DirectLineConfig:
    """Configuration for Direct Line API"""
    endpoint: str = "https://directline.botframework.com/v3/directline"
    token_url: str = f"{endpoint}/tokens/generate"
    timeout: int = 120
    retry_attempts: int = 3
    retry_delay: int = 5

class DirectLineClient:
    """Handles Direct Line API communications"""
    def __init__(self, secret: str, bot_id: str):
        self.secret = secret
        self.bot_id = bot_id
        self.config = DirectLineConfig()
        self._validate_credentials()

    def _validate_credentials(self) -> None:
        """Validate that required credentials are present"""
        if not self.secret or not self.bot_id:
            raise ValueError("Direct Line secret and bot ID are required")

    def _make_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """Create headers for API requests"""
        auth_token = token or f"Bearer {self.secret}"
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

    def get_token(self) -> Optional[str]:
        """Generate a Direct Line token"""
        try:
            response = requests.post(
                self.config.token_url,
                headers=self._make_headers(self.secret),
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()["token"]
        except requests.exceptions.RequestException as e:
            print(f"Error generating Direct Line token: {e}")
            return None

    def start_conversation(self, token: str) -> Optional[str]:
        """Start a new conversation"""
        try:
            payload = {"bot": {"id": self.bot_id}}
            response = requests.post(
                f"{self.config.endpoint}/conversations",
                headers=self._make_headers(token),
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()["conversationId"]
        except requests.exceptions.RequestException as e:
            print(f"Failed to start conversation: {e}")
            return None

    def send_message(self, conversation_id: str, message: str, token: str) -> bool:
        """Send a message to the conversation"""
        payload = {
            "type": "message",
            "from": {"id": "user123"},  # Consider making this configurable
            "text": message,
            "locale": "en-US"
        }
        try:
            response = requests.post(
                f"{self.config.endpoint}/conversations/{conversation_id}/activities",
                headers=self._make_headers(token),
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error sending message: {e}")
            return False

    def send_user_token(self, conversation_id: str, user_token: str, token: str) -> bool:
        """Send user authentication token"""
        payload = {
            "type": "event",
            "name": "tokens/response",
            "value": {"token": user_token},
            "from": {"id": "user123"}
        }
        try:
            response = requests.post(
                f"{self.config.endpoint}/conversations/{conversation_id}/activities",
                headers=self._make_headers(token),
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error sending user token: {e}")
            return False

    def get_responses(self, conversation_id: str, token: str) -> Optional[str]:
        """Get responses from the conversation"""
        try:
            response = requests.get(
                f"{self.config.endpoint}/conversations/{conversation_id}/activities",
                headers=self._make_headers(token),
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return self._extract_markdown_content(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error getting responses: {e}")
            return None

    @staticmethod
    def _extract_markdown_content(data: Dict[str, Any]) -> Optional[str]:
        """Extract markdown content from response data"""
        for activity in data.get("activities", []):
            if (activity.get("type") == "event" and 
                activity.get("valueType") == "DynamicPlanStepFinished"):
                observation = activity.get("value", {}).get("observation", {})
                search_result = observation.get("search_result", {})
                text = search_result.get("Text", {})
                if markdown_content := text.get("MarkdownContent"):
                    return markdown_content
        return None

@tool
def query_directline(conversation_id: str, message: str, token: str) -> str:
    """Enhanced Direct Line query tool"""
    # Initialize the client with environment variables
    client = DirectLineClient(
        secret=os.getenv('DIRECT_LINE_SECRET'),
        bot_id=os.getenv('BotIdentifier')
    )
    
    # Send the message
    if not client.send_message(conversation_id, message, token):
        return "Error: Failed to send message"

    # Send user token if available
    user_token = os.getenv('USER_TOKEN')
    if user_token and not client.send_user_token(conversation_id, user_token, token):
        return "Error: Failed to send user token"

    # Wait for processing
    time.sleep(10)  # Consider making this configurable or implementing a better waiting mechanism

    # Get response
    response = client.get_responses(conversation_id, token)
    return response or "No response received"

def main():
    """Main execution function"""
    # Load environment variables
    load_dotenv()

    # Initialize the Direct Line client
    client = DirectLineClient(
        secret=os.getenv('DIRECT_LINE_SECRET'),
        bot_id=os.getenv('BotIdentifier')
    )

    # Get Direct Line token
    token = client.get_token()
    if not token:
        print("Failed to get Direct Line token")
        return

    # Start conversation
    conversation_id = client.start_conversation(token)
    if not conversation_id:
        print("Failed to start conversation")
        return

    # Initialize agent
    model = HfApiModel(
        token=os.getenv("HUGGINGFACE_API_TOKEN"),
        model_id="mistralai/Mistral-7B-Instruct-v0.3"
    )
    search_tool = DuckDuckGoSearchTool()
    agent = ToolCallingAgent(
        tools=[query_directline, search_tool],
        model=model,
        max_steps=2
    )

    # Run agent
    response = agent.run(
        "what new opportunities on sam.gov would be best for Northramp to pursue?",
        additional_args=dict(
            conversation_id=conversation_id,
            message="what are new opportunities for Northramp to pursue?",
            token=token
        )
    )
    print(response)

if __name__ == "__main__":
    main()