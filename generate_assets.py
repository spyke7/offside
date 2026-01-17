
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import os

def generate_pitch_image():
    # Create asset directory
    if not os.path.exists("assets"):
        os.makedirs("assets")
        
    print("Generating high-quality pitch texture...")
    
    # Setup pitch (StatsBomb settings)
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#2c3e50', line_color='#c0c0c0',
                  goal_type='box', goal_alpha=0.8)
                  
    fig, ax = pitch.draw(figsize=(16, 12))
    
    # Save transparently or with color
    # We want a nice dark theme background
    fig.set_facecolor('#2c3e50')
    
    output_path = "assets/pitch_texture.png"
    plt.savefig(output_path, bbox_inches='tight', pad_inches=0, dpi=100)
    plt.close()
    
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    generate_pitch_image()
