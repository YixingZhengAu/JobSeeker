import json
from datetime import date, datetime
import os
from pathlib import Path


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

        
def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, cls=DateEncoder)



def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt template from the prompts directory
    
    Args:
        prompt_name (str): Name of the prompt file (without .txt extension)
    
    Returns:
        str: The prompt template content
    
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    # Get the directory where this script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_file = os.path.join(current_dir, "prompts", f"{prompt_name}.txt")
    
    if not os.path.exists(prompt_file):
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read().strip()
