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

    def load_data(self, match_id: int = DEFAULT_MATCH_ID, dataset_type: str = "events"):
        """
        Loads match data from local files.
        Uses the pre-downloaded match.json and lineup.json files.
        
        For World Cup 2022 Final: Argentina vs France
        """
        # Try World Cup 2022 final first
        match_path = os.path.join(str(self.data_dir), "matches", "worldcup_2022_final.json")
        lineup_path = os.path.join(str(self.data_dir), "matches", "worldcup_2022_final_lineup.json")
        
        # Fallback to old match.json if WC final not found
        if not os.path.exists(match_path):
            print("[!] World Cup 2022 final not found, using fallback match data...")
            match_path = os.path.join(str(self.data_dir), "matches", "match.json")
            lineup_path = os.path.join(str(self.data_dir), "matches", "lineup.json")
        
        if not os.path.exists(match_path):
            raise FileNotFoundError(f"Match file not found at: {match_path}")

        print(f"Loading match data from {match_path}...")
        try:
            dataset = statsbomb.load(
                event_data=match_path,
                lineup_data=lineup_path if os.path.exists(lineup_path) else None,
                coordinates="statsbomb",
            )
            print("Data loaded successfully.")
            return dataset
        except Exception as e:
            print(f"Error loading data: {e}")
            raise