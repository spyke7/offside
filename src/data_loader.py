import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from kloppy import statsbomb
from kloppy.domain import Dataset, Event, Team, Player

from src.config import (
    DATA_DIR, 
    STATSBOMB_REPO,
    DEFAULT_COMPETITION_ID,
    DEFAULT_SEASON_ID,
    DEFAULT_MATCH_ID
)


class StatsBombDataLoader:
    
    def __init__(self):
        self.data_dir = Path(DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def download_file(self, url: str, filepath: Path) -> bool:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded: {filepath.name}")
            return True
            
        except requests.RequestException as e:
            print(f"Failed to download {url}: {e}")
            return False

    def get_competitions(self) -> List[Dict]:
        url = f"{STATSBOMB_REPO}competitions.json"
        filepath = self.data_dir / "competitions.json"
        
        if not filepath.exists():
            self.download_file(url, filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)