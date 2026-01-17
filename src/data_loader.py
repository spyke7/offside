"""
Data Loader Module - Fixed version
Handles StatsBomb data with proper competition/match selection
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from kloppy import statsbomb
from kloppy.domain import Dataset

from src.config import DATA_DIR, STATSBOMB_REPO, COMPETITIONS


class StatsBombDataLoader:
    """Handles all StatsBomb data operations with menu support."""
    
    def __init__(self):
        """Initialize data loader."""
        self.data_dir = Path(DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cached_competitions = None
        self.cached_matches = {}
        
    def download_file(self, url: str, filepath: Path) -> bool:
        """Download a file from URL."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(response.content)
    
            print(f"Downloaded: {filepath.name}")
            return True
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            return False
    
    def get_competitions(self) -> List[Dict]:
        """Get list of available competitions."""
        if self.cached_competitions:
            return self.cached_competitions
        
        url = f"{STATSBOMB_REPO}competitions.json"
        filepath = self.data_dir / "competitions.json"
        
        if not filepath.exists():
            self.download_file(url, filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            self.cached_competitions = json.load(f)
        
        return self.cached_competitions
    
    def get_matches_for_competition(self, competition_id: int, season_id: int) -> List[Dict]:
        """Get all matches for a competition/season."""
        cache_key = f"{competition_id}_{season_id}"
        
        if cache_key in self.cached_matches:
            return self.cached_matches[cache_key]
        
        url = f"{STATSBOMB_REPO}matches/{competition_id}/{season_id}.json"
        filepath = self.data_dir / f"matches_{competition_id}_{season_id}.json"
        
        if not filepath.exists():
            if not self.download_file(url, filepath):
                return []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                matches = json.load(f)
                self.cached_matches[cache_key] = matches
                return matches
        except Exception as e:
            print(f"✗ Error reading matches: {e}")
            return []
    
    def load_match(self, match_id: int) -> Optional[Dataset]:
        """Load a specific match by ID."""
        events_url = f"{STATSBOMB_REPO}events/{match_id}.json"
        lineups_url = f"{STATSBOMB_REPO}lineups/{match_id}.json"
        
        events_path = self.data_dir / f"events_{match_id}.json"
        lineups_path = self.data_dir / f"lineups_{match_id}.json"
        
        # Download if needed
        if not events_path.exists():
            print(f"Downloading match {match_id} events...")
            if not self.download_file(events_url, events_path):
                return None
        
        if not lineups_path.exists():
            print(f"Downloading match {match_id} lineups...")
            self.download_file(lineups_url, lineups_path)
        
        # Load with Kloppy
        try:
            print(f"Loading match {match_id}...")
            dataset = statsbomb.load(
                event_data=str(events_path),
                lineup_data=str(lineups_path) if lineups_path.exists() else None,
                coordinates="statsbomb"
            )
            
            print(f"Loaded {len(dataset.events)} events")
            return dataset
        except Exception as e:
            print(f"Error loading match: {e}")
            return None


def get_player_info(dataset: Dataset) -> Dict[str, Dict]:
    """Extract player information from dataset."""
    player_info = {}
    
    for team in dataset.metadata.teams:
        for player in team.players:
            player_info[player.player_id] = {
                'name': player.name,
                'team': team.name,
                'team_id': team.team_id,
                'jersey_number': player.jersey_no if hasattr(player, 'jersey_no') else '?',
                'position': player.starting_position.name if player.starting_position else 'Unknown'
            }
    
    return player_info