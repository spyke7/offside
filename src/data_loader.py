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

    def get_matches(self, competition_id: int, season_id: int) -> List[Dict]:
        url = f"{STATSBOMB_REPO}matches/{competition_id}/{season_id}.json"
        filepath = self.data_dir / f"matches_{competition_id}_{season_id}.json"
        
        if not filepath.exists():
            self.download_file(url, filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def download_match_files(self, match_id: int) -> Tuple[Path, Path]:
        events_url = f"{STATSBOMB_REPO}events/{match_id}.json"
        lineups_url = f"{STATSBOMB_REPO}lineups/{match_id}.json"
        
        events_path = self.data_dir / f"events_{match_id}.json"
        lineups_path = self.data_dir / f"lineups_{match_id}.json"
        
        # Download both files
        if not events_path.exists():
            self.download_file(events_url, events_path)
        
        if not lineups_path.exists():
            self.download_file(lineups_url, lineups_path)
        
        return events_path, lineups_path

    def load_match_data(self, match_id: Optional[int] = None) -> Dataset:
        if match_id is None:
            match_id = DEFAULT_MATCH_ID
        
        print(f"\n{'='*60}")
        print(f"Loading match {match_id}...")
        print(f"{'='*60}\n")
        
        # Download files if needed
        events_path, lineups_path = self.download_match_files(match_id)
        
        # Use Kloppy to parse StatsBomb data
        # Kloppy standardizes the data format across different providers
        dataset = statsbomb.load(
            event_data=str(events_path),
            lineup_data=str(lineups_path),
            coordinates="statsbomb"  # Use StatsBomb's 120x80 coordinate system
        )
        
        print(f"Loaded {len(dataset.events)} events")
        print(f"Teams: {dataset.teams[0].name} vs {dataset.teams[1].name}")
        print(f"Match duration: {dataset.events[-1].timestamp:.0f} seconds\n")
        
        return dataset

    def list_available_matches(self, competition_id: int, season_id: int) -> None:
        matches = self.get_matches(competition_id, season_id)
        
        print(f"\n{'='*80}")
        print(f"Available Matches (Competition: {competition_id}, Season: {season_id})")
        print(f"{'='*80}\n")
        
        for match in matches[:10]:  # Show first 10
            home = match['home_team']['home_team_name']
            away = match['away_team']['away_team_name']
            score = f"{match['home_score']}-{match['away_score']}"
            match_id = match['match_id']
            date = match['match_date']
            
            print(f"[{match_id}] {date} | {home} {score} {away}")
        
        if len(matches) > 10:
            print(f"\n... and {len(matches) - 10} more matches")


def get_player_info(dataset: Dataset) -> Dict[str, Dict]:
    """
    Extract player information from dataset.
    
    Args:
        dataset: Kloppy Dataset
        
    Returns:
        Dict mapping player_id to player info (name, team, jersey_number)
    """
    player_info = {}
    
    for team in dataset.teams:
        for player in team.players:
            player_info[player.player_id] = {
                'name': player.name,
                'team': team.name,
                'team_id': team.team_id,
                'jersey_number': player.jersey_no,
                'position': player.position.name if player.position else 'Unknown'
            }
    
    return player_info


def get_team_info(dataset: Dataset) -> Tuple[Dict, Dict]:
    """
    Extract team information.
    
    Args:
        dataset: Kloppy Dataset
        
    Returns:
        Tuple of (team_a_info, team_b_info) dictionaries
    """
    team_a = dataset.teams[0]
    team_b = dataset.teams[1]
    
    team_a_info = {
        'id': team_a.team_id,
        'name': team_a.name,
        'players': [p.player_id for p in team_a.players]
    }
    
    team_b_info = {
        'id': team_b.team_id,
        'name': team_b.name,
        'players': [p.player_id for p in team_b.players]
    }
    
    return team_a_info, team_b_info


# ============================================================================
# TESTING CODE
# ============================================================================

if __name__ == "__main__":
    """
    Test the data loader by loading a match and printing info.
    Run this file directly to test: python -m src.data_loader
    """
    
    loader = StatsBombDataLoader()
    
    # List available competitions
    print("\nFetching competitions...")
    competitions = loader.get_competitions()
    print(f"Found {len(competitions)} competitions")
    
    # List some matches
    loader.list_available_matches(DEFAULT_COMPETITION_ID, DEFAULT_SEASON_ID)
    
    # Load a match
    dataset = loader.load_match_data()
    
    # Print some event info
    print("\nFirst 5 events:")
    print("-" * 80)
    for event in dataset.events[:5]:
        print(f"{event.timestamp:.1f}s | {event.event_type.name} | "
              f"{event.player.name if event.player else 'N/A'}")
    
    # Print player info
    players = get_player_info(dataset)
    print(f"\nTotal players: {len(players)}")
    
    # Print team info
    team_a, team_b = get_team_info(dataset)
    print(f"\n{team_a['name']}: {len(team_a['players'])} players")
    print(f"{team_b['name']}: {len(team_b['players'])} players")
    return json.load(f)
