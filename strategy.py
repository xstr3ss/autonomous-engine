import pandas as pd
import numpy as np

def generate_signals(df: pd.DataFrame) -> pd.Series:
    """
    Takes a DataFrame with OHLCV data.
    Returns a pandas Series of positions: 1 (Long) or 0 (Flat).
    """
    # Implement 50-day and 200-day moving average crossover
    df['SMA_Fast'] = df['Close'].rolling(window=50).mean()
    df['SMA_Slow'] = df['Close'].rolling(window=200).mean()
    
    # 1 if Fast > Slow, else 0
    signals = np.where(df['SMA_Fast'] > df['SMA_Slow'], 1, 0)
    
    return pd.Series(signals, index=df.index)
