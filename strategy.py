import pandas as pd
import numpy as np
import talib

def generate_signals(df: pd.DataFrame) -> pd.Series:
    """
    Takes a DataFrame with OHLCV data.
    Returns a pandas Series of positions: 1 (Long) or 0 (Flat).
    """
    # Calculate EMA for 12 and 26 periods
    df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
    
    # Implement the crossover logic
    # Long signal when EMA_12 crosses above EMA_26
    crossover_up = (df['EMA_12'] > df['EMA_26']) & (df['EMA_12'].shift(1) <= df['EMA_26'].shift(1))
    
    # Calculate RSI
    df['RSI'] = talib.RSI(df['Close'], timeperiod=14)
    
    # RSI threshold check: RSI must be below 65
    rsi_condition = df['RSI'] < 65
    
    # Combine conditions: Crossover up AND RSI < 65
    signals = np.where(crossover_up & rsi_condition, 1, 0)
    
    return pd.Series(signals, index=df.index)
