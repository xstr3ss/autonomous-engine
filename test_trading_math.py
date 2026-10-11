from trading_math import calculate_sma

def test_calculate_sma():
    # Test standard Moving Averages
    assert calculate_sma([10, 20, 30], 3) == 20.0
    assert calculate_sma([10, 20, 30, 40, 50], 3) == 40.0
    
    # Edge Cases: Empty lists or period larger than the dataset
    assert calculate_sma([], 3) is None
    assert calculate_sma([10, 20], 5) is None
# Trigger
