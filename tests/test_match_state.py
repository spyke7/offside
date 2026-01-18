"""
Test suite for MatchState wrapper.
"""

import os
import sys
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_match_state_initialization():
    """Test basic MatchState initialization."""
    from src.match_state import MatchState
    
    state = MatchState()
    
    assert state.time == 0.0
    assert state.period == 1
    assert state.score == (0, 0)
    assert state.positions.shape == (23, 2)
    assert state.velocities.shape == (23, 2)
    assert state.stamina.shape == (22,)
    
    print("[PASS] MatchState initialization test passed")


def test_match_state_to_vector():
    """Test to_vector() returns correct shape."""
    from src.match_state import MatchState
    
    state = MatchState()
    
    # Without velocities
    vector = state.to_vector()
    # 5 base features + 23*2 positions = 5 + 46 = 51
    assert vector.shape == (51,), f"Expected (51,), got {vector.shape}"
    assert vector.dtype == np.float32
    
    # With velocities
    vector_with_vel = state.to_vector(include_velocities=True)
    # 51 + 23*2 velocities = 51 + 46 = 97
    assert vector_with_vel.shape == (97,), f"Expected (97,), got {vector_with_vel.shape}"
    
    print("[PASS] MatchState to_vector test passed")


def test_match_state_copy():
    """Test that copy() creates independent copy."""
    from src.match_state import MatchState
    
    state = MatchState()
    state.time = 45.0
    state.score = (1, 0)
    state.positions[0] = [30.0, 40.0]
    
    # Make copy
    copy = state.copy()
    
    # Modify original
    state.time = 90.0
    state.score = (2, 1)
    state.positions[0] = [60.0, 60.0]
    
    # Copy should be unchanged
    assert copy.time == 45.0
    assert copy.score == (1, 0)
    assert list(copy.positions[0]) == [30.0, 40.0]
    
    print("[PASS] MatchState copy test passed")


def test_match_state_to_dict():
    """Test to_dict() serialization."""
    from src.match_state import MatchState
    
    state = MatchState()
    state.time = 60.0
    state.score = (2, 1)
    
    data = state.to_dict()
    
    assert data['time'] == 60.0
    assert data['score'] == [2, 1]
    assert 'positions' in data
    assert 'velocities' in data
    
    print("[PASS] MatchState to_dict test passed")


def test_match_history():
    """Test MatchHistory tracking."""
    from src.match_state import MatchState, MatchHistory
    
    history = MatchHistory(max_snapshots=10, interval_seconds=1.0)
    
    state = MatchState()
    
    # Record states at different times
    state.time = 0.0
    history.record(state, force=True)
    
    state.time = 1.5
    state.score = (1, 0)
    history.record(state, force=True)
    
    state.time = 3.0
    state.score = (1, 1)
    history.record(state, force=True)
    
    assert len(history) == 3
    
    # Get state at specific time
    retrieved = history.get_state_at_time(1.5)
    assert retrieved.score == (1, 0)
    
    print("[PASS] MatchHistory test passed")


def test_match_state_properties():
    """Test property accessors."""
    from src.match_state import MatchState
    
    state = MatchState()
    state.positions[-1] = [50.0, 30.0]  # Ball position
    
    # Test ball_position property
    ball_pos = state.ball_position
    assert list(ball_pos) == [50.0, 30.0]
    
    # Test player_positions property
    player_pos = state.player_positions
    assert player_pos.shape == (22, 2)  # 22 players, not including ball
    
    # Test score properties
    state.score = (3, 2)
    assert state.home_score == 3
    assert state.away_score == 2
    
    print("[PASS] MatchState properties test passed")


if __name__ == "__main__":
    print("\n" + "="*50)
    print("Running MatchState Tests")
    print("="*50 + "\n")
    
    try:
        test_match_state_initialization()
        test_match_state_to_vector()
        test_match_state_copy()
        test_match_state_to_dict()
        test_match_history()
        test_match_state_properties()
        
        print("\n" + "="*50)
        print("All MatchState tests PASSED!")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"\nTest FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
