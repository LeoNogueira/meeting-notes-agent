import os
import json
import logging
from typing import List, Dict
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("slack_notifier.log"),
        logging.StreamHandler()
    ]
)

class SlackNotifier:
    def __init__(self):
        load_dotenv()
        self.client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
        self.channel = os.getenv('SLACK_CHANNEL', '#actions')
        self.input_file = os.getenv('ACTIONS_FILE', 'meeting-notes/actions.json')

    def read_actions(self) -> List[Dict]:
        """Read actions from JSON file"""
        try:
            with open(self.input_file, 'r') as f:
                data = json.load(f)
                return data.get('actions', [])
        except Exception as e:
            logging.error(f"Error reading actions file: {e}")
            return []

    def format_action_message(self, action: Dict) -> str:
        """Format a single action into a Slack message"""
        description = action.get('description', 'No description')
        owner = action.get('owner', 'Unassigned')
        due_date = action.get('due_date', 'No due date')
        status = action.get('status', 'No status')

        return f"*Action Item*\n" \
               f">*Description:* {description}\n" \
               f">*Owner:* {owner}\n" \
               f">*Due Date:* {due_date}\n" \
               f">*Status:* {status}\n"

    def post_to_slack(self, message: str) -> bool:
        """Post a message to Slack channel"""
        try:
            response = self.client.chat_postMessage(
                channel=self.channel,
                text=message,
                mrkdwn=True
            )
            return response['ok']
        except SlackApiError as e:
            logging.error(f"Error posting to Slack: {e.response['error']}")
            return False

    def run(self):
        """Main execution method"""
        actions = self.read_actions()
        if not actions:
            logging.warning("No actions found to process")
            return

        logging.info(f"Found {len(actions)} actions to process")
        
        # Post header message
        self.post_to_slack("📋 *New Actions from Meeting Notes*\n")

        # Post each action
        for action in actions:
            message = self.format_action_message(action)
            success = self.post_to_slack(message)
            if success:
                logging.info(f"Successfully posted action: {action.get('description', 'Unknown')}")
            else:
                logging.error(f"Failed to post action: {action.get('description', 'Unknown')}")

def main():
    notifier = SlackNotifier()
    notifier.run()

if __name__ == "__main__":
    main()