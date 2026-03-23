import os
import sys
import json
from typing import List, Dict, Optional

def read_config(config_path: str) -> Dict:
    """Read configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)

def process_data(data: List[str]) -> List[str]:
    """Process list of strings."""
    return [item.strip().upper() for item in data]

def validate_input(value: str) -> bool:
    """Validate input string."""
    if not value:
        return False
    return len(value) > 0 and len(value) < 100

class DataHelper:
    def __init__(self, config: Dict):
        self.config = config
        self.cache = {}

    def get_value(self, key: str) -> Optional[str]:
        """Get value from cache or config."""
        if key in self.cache:
            return self.cache[key]

        value = self.config.get(key)
        if value:
            self.cache[key] = value
        return value
