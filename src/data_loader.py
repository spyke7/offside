from kloppy import statsbomb
import pandas as pd
import os
from src.config import SAMPLE_MATCH_PATH

class DataLoader:
    def __init__(self, match_path=SAMPLE_MATCH_PATH):
        self.match_path = match_path
        self.dataset = None

    def load_data(self):
        """Loads StatsBomb data using kloppy."""
        if not os.path.exists(self.match_path):
            raise FileNotFoundError(f"Match file not found at: {self.match_path}")

        print(f"Loading match data from {self.match_path}...")
        self.dataset = statsbomb.load(
            event_data=self.match_path,
            coordinates="statsbomb",  # Keep native coordinates for now
            data_version="1.1" # Explicitly set data version if needed, or let kloppy decide
        )
        print("Data loaded successfully.")
        return self.dataset

    def get_events(self):
        """Returns events as a pandas DataFrame (if needed) or list."""
        if not self.dataset:
            self.load_data()
        
        # Kloppy datasets facilitate easy conversion to pandas
        # Accessing all events
        return self.dataset.events

if __name__ == "__main__":
    loader = DataLoader()
    try:
        data = loader.load_data()
        print(f"Loaded {len(data.events)} events.")
        print(f"Home Team: {data.metadata.teams[0].name}")
        print(f"Away Team: {data.metadata.teams[1].name}")
    except Exception as e:
        print(f"Error loading data: {e}")
