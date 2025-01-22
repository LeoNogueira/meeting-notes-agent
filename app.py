import os
import glob
import json
import logging
from typing import List, Dict
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import OpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import PromptValue
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent

# Load environment variables and setup logging
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# Update schema definition at top of file
response_schemas = [
    ResponseSchema(name="items", description="List of action items with their details", type="array")
]

# Define the expected structure for each action item
action_item_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "action": {"type": "string"},
            "owner": {"type": "string"},
            "due_date": {"type": "string"},
            "status": {"type": "string"}
        }
    }
}

output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

# Update prompt template
agent_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an AI assistant that extracts ALL action items and todos from meeting notes.
    For each action or todo, include:
    - The action/todo description
    - Owner/assigned person
    - Due date if specified if not return 'None'
    - Current status
    
    Return ALL items found, not just one.
    
    Available tools: {tool_names}"""),
    ("user", """Extract ALL actions and todos from these meeting notes:
    {content}
    
    {format_instructions}
    
    Return as a list of items."""),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

class MeetingNotesProcessor:
    def __init__(self):
        self.llm = OpenAI(temperature=0)
        self.setup_agent()

    def setup_agent(self):
        self.extract_tool = Tool(
            name="ExtractActions",
            func=self.process_content,
            description="Extract actions from meeting notes"
        )
        
        # Simple direct processing without React agent
        self.tools = [self.extract_tool]

    # Update process_content method
    def process_content(self, content: str) -> List[Dict]:
        try:
            prompt_value = agent_prompt.format_prompt(
                content=content,
                tool_names=", ".join([tool.name for tool in self.tools]),
                format_instructions=output_parser.get_format_instructions(),
                agent_scratchpad=[]
            )

            result = self.llm.invoke(prompt_value.to_string())
            
            # Convert list of dictionaries directly
            if isinstance(result, list):
                return result
                
            # If result is a string, parse it
            parsed_result = output_parser.parse(result)
            actions = parsed_result.get('items', [])
            
            # Rename 'actions' key to 'action' in each item
            for item in actions:
                if 'actions' in item:
                    item['action'] = item.pop('actions')
            
            logging.info(f"Extracted {len(actions)} actions")
            return actions
        
        except Exception as e:
            logging.error(f"Error processing content: {e}")
            return []

    def process_file(self, filepath: str) -> List[Dict]:
        logging.info(f"Processing {filepath}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                return self.process_content(content)
        except Exception as e:
            logging.error(f"Error processing {filepath}: {e}")
            return [{"error": str(e)}]

def main():
    processor = MeetingNotesProcessor()
    markdown_dir = os.getenv("DIRECTORY", "meeting-notes")
    output_file = os.getenv("OUTPUT_FILE", f"actions_{datetime.now().strftime('%Y%m%d')}.json")
    
    markdown_files = glob.glob(os.path.join(markdown_dir, "**/*.md"), recursive=True) + \
                    glob.glob(os.path.join(markdown_dir, "**/.*.md"), recursive=True)
    logging.info(f"Found {len(markdown_files)} markdown files")
    
    all_actions = []
    for file in markdown_files:
        actions = processor.process_file(file)
        if actions:  # Validate actions exist
            logging.info(f"Extracted {len(actions)} actions from {file}")
            all_actions.extend(actions)  # Fixed: extend with actions, not all_actions
        else:
            logging.warning(f"No actions found in {file}")
    logging.info(f"Total actions extracted: {len(all_actions)}")
    
    os.makedirs("output", exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump({"actions": all_actions}, f, indent=2, sort_keys=True)
    logging.info(f"Results saved to {output_file}")

#Start the main function
if __name__ == "__main__":
    main()