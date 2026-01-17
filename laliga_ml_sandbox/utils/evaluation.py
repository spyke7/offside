import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error


def direction_accuracy(y_true, y_pred):
    """
    Calculate the accuracy of predicting the match outcome direction.
    
    Args:
        y_true: Actual goal differences
        y_pred: Predicted goal differences
    
    Returns:
        Accuracy score (0-1) for predicting the correct sign
    """
    # Convert to numpy arrays
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # Get signs: positive (home win), zero (draw), negative (away win)
    true_signs = np.sign(y_true)
    pred_signs = np.sign(y_pred)
    
    # Calculate accuracy
    correct = np.sum(true_signs == pred_signs)
    total = len(y_true)
    
    return correct / total


def outcome_confusion_matrix(y_true, y_pred):
    """
    Create a confusion matrix for H/D/A outcomes.
    
    Returns:
        DataFrame with confusion matrix
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # Convert to outcome labels
    def to_outcome(values):
        outcomes = []
        for v in values:
            if v > 0:
                outcomes.append('H')  # Home win
            elif v < 0:
                outcomes.append('A')  # Away win
            else:
                outcomes.append('D')  # Draw
        return outcomes
    
    true_outcomes = to_outcome(y_true)
    pred_outcomes = to_outcome(y_pred)
    
    # Create confusion matrix
    outcomes = ['H', 'D', 'A']
    matrix = pd.DataFrame(0, index=outcomes, columns=outcomes)
    
    for true, pred in zip(true_outcomes, pred_outcomes):
        matrix.loc[true, pred] += 1
    
    return matrix


def evaluate_model(y_true, y_pred, model_name="Model"):
    """
    Comprehensive evaluation of a goal difference prediction model.
    
    Args:
        y_true: Actual goal differences
        y_pred: Predicted goal differences
        model_name: Name of the model for display
    
    Returns:
        Dictionary with all evaluation metrics
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # Calculate metrics
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    dir_acc = direction_accuracy(y_true, y_pred)
    
    # Outcome-specific accuracy
    true_signs = np.sign(y_true)
    pred_signs = np.sign(y_pred)
    
    # Home win accuracy
    home_wins = true_signs > 0
    if np.sum(home_wins) > 0:
        home_acc = np.sum((true_signs == pred_signs) & home_wins) / np.sum(home_wins)
    else:
        home_acc = 0.0
    
    # Away win accuracy
    away_wins = true_signs < 0
    if np.sum(away_wins) > 0:
        away_acc = np.sum((true_signs == pred_signs) & away_wins) / np.sum(away_wins)
    else:
        away_acc = 0.0
    
    # Draw accuracy
    draws = true_signs == 0
    if np.sum(draws) > 0:
        draw_acc = np.sum((true_signs == pred_signs) & draws) / np.sum(draws)
    else:
        draw_acc = 0.0
    
    results = {
        'model_name': model_name,
        'mae': mae,
        'rmse': rmse,
        'direction_accuracy': dir_acc,
        'home_win_accuracy': home_acc,
        'away_win_accuracy': away_acc,
        'draw_accuracy': draw_acc,
        'n_samples': len(y_true)
    }
    
    return results


def print_evaluation(results):
    """
    Print evaluation results in a nice format.
    """
    print(f"\n{'='*60}")
    print(f"  {results['model_name']} Evaluation")
    print(f"{'='*60}")
    print(f"  Samples: {results['n_samples']}")
    print(f"\n  Regression Metrics:")
    print(f"    MAE:  {results['mae']:.4f}")
    print(f"    RMSE: {results['rmse']:.4f}")
    print(f"\n  Direction Accuracy:")
    print(f"    Overall:   {results['direction_accuracy']:.2%}")
    print(f"    Home Wins: {results['home_win_accuracy']:.2%}")
    print(f"    Draws:     {results['draw_accuracy']:.2%}")
    print(f"    Away Wins: {results['away_win_accuracy']:.2%}")
    print(f"{'='*60}\n")


def compare_models(results_list):
    """
    Compare multiple models side by side.
    
    Args:
        results_list: List of result dictionaries from evaluate_model
    
    Returns:
        DataFrame with comparison
    """
    df = pd.DataFrame(results_list)
    df = df.set_index('model_name')
    
    # Reorder columns for better readability
    cols = ['mae', 'rmse', 'direction_accuracy', 'home_win_accuracy', 
            'draw_accuracy', 'away_win_accuracy', 'n_samples']
    df = df[cols]
    
    return df
