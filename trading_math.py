def calculate_sma(prices, period):
    if not prices or period <= 0 or len(prices) < period:
        return None
    
    # Calculate the Simple Moving Average of the last 'period' prices
    window = prices[-period:]
    return sum(window) / period
