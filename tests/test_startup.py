import os
import pygame
import sys

# Use dummy video driver for headless testing
os.environ["SDL_VIDEODRIVER"] = "dummy"

# Add src to path just in case
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.game_engine import GameEngine
    print("Import successful.")
    
    # Initialize engine
    game = GameEngine()
    print("GameEngine initialized.")
    
    # Load content
    game.load_content()
    print("Content loaded.")
    
    # Run one loop iteration manually
    game.handle_input()
    game.update()
    game.draw()
    print("One loop iteration successful.")
    
    pygame.quit()
    print("Test Passed.")
except Exception as e:
    print(f"Test Failed: {e}")
    sys.exit(1)
