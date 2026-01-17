
import os
from src.data_loader import StatsBombDataLoader

def main():
    loader = StatsBombDataLoader()
    dataset = loader.load_match(3869685)
    
    if not dataset:
        print("Failed to load dataset")
        return
    
    freeze_frames = 0
    total_positions = 0
    
    for event in dataset.events:
        if hasattr(event, 'freeze_frame') and event.freeze_frame and hasattr(event.freeze_frame, 'players_coordinates'):
            freeze_frames += 1
            total_positions += len(event.freeze_frame.players_coordinates)

    print(f"Events with freeze_frame: {freeze_frames}")
    print(f"Total player positions found in frames: {total_positions}")

if __name__ == "__main__":
    main()
