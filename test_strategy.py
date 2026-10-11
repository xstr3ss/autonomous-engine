import os
import sys
import pandas as pd
import yfinance as yf
from strategy import generate_signals

TARGET_ROI = 0.30       # 30% Return requirement
MAX_DRAWDOWN = 0.20     # 20% Maximum Drawdown limit
DATA_FILE = "btc_historical_data.csv"

def get_data() -> pd.DataFrame:
    """Fetch and cache market data to avoid yfinance rate limits during AI loops."""
    if not os.path.exists(DATA_FILE):
        print("📊 Fetching historical data from yfinance...")
        df = yf.download("BTC-USD", period="2y", interval="1d", progress=False)
        
        # FIX: Flatten MultiIndex BEFORE saving to prevent CSV string corruption
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.to_csv(DATA_FILE)
    
    # Read the data and force all columns to float numeric types
    df = pd.read_csv(DATA_FILE, index_col=0, parse_dates=True)
    df = df.apply(pd.to_numeric, errors='coerce').dropna()
    return df

def calculate_metrics(df: pd.DataFrame, signals: pd.Series) -> tuple[float, float]:
    """Vectorized backtest returning (Cumulative ROI, Max Drawdown)."""
    df = df.copy()
    df['Position'] = signals.shift(1).fillna(0)  # Shift by 1 to prevent look-ahead bias
    df['Market_Return'] = df['Close'].pct_change()
    df['Strategy_Return'] = df['Position'] * df['Market_Return']
    
    # Calculate ROI
    cumulative_return = (1 + df['Strategy_Return'].fillna(0)).prod() - 1
    
    # Calculate Drawdown
    rolling_max = (1 + df['Strategy_Return'].fillna(0)).cumprod().cummax()
    drawdown = (1 + df['Strategy_Return'].fillna(0)).cumprod() / rolling_max - 1
    max_drawdown = abs(drawdown.min()) if not pd.isna(drawdown.min()) else 0.0
    
    return float(cumulative_return), float(max_drawdown)

def main():
    df = get_data()
    
    # Strict 70/30 Train-Test Split to prevent curve-fitting
    split_idx = int(len(df) * 0.7)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    
    try:
        train_signals = generate_signals(train_df)
        test_signals = generate_signals(test_df)
    except Exception as e:
        print(f"❌ [Execution Error] The strategy.py code crashed: {e}")
        sys.exit(1)
        
    train_roi, train_dd = calculate_metrics(train_df, train_signals)
    test_roi, test_dd = calculate_metrics(test_df, test_signals)
    
    failed = False
    feedback = []
    
    # Evaluate In-Sample (Training)
    if train_roi < TARGET_ROI or train_dd > MAX_DRAWDOWN:
        failed = True
        feedback.append(f"IN-SAMPLE FAILURE (Train Data):\n - ROI: {train_roi*100:.2f}% (Target: {TARGET_ROI*100}%)\n - Max Drawdown: {train_dd*100:.2f}% (Limit: {MAX_DRAWDOWN*100}%)")
        if train_dd > MAX_DRAWDOWN:
            feedback.append("SUGGESTION: Your drawdown is too high. Implement an ATR (Average True Range) trailing stop, or add an RSI filter to avoid buying at the top.")
        elif train_roi < TARGET_ROI:
            feedback.append("SUGGESTION: Your returns are too low. The current indicators are likely triggering too late or getting chopped in sideways markets. Try combining trend (MACD/SMA) with momentum (RSI) or volume filters.")
            
    # Evaluate Out-Of-Sample (Validation)
    elif test_roi < TARGET_ROI or test_dd > MAX_DRAWDOWN:
        failed = True
        feedback.append(f"OUT-OF-SAMPLE FAILURE (Validation Data - Curve Fitting Detected):\n - ROI: {test_roi*100:.2f}% (Target: {TARGET_ROI*100}%)\n - Max Drawdown: {test_dd*100:.2f}% (Limit: {MAX_DRAWDOWN*100}%)")
        feedback.append("SUGGESTION: The strategy passed training but failed on unseen data. You have overfit to the historical curve. Reduce the number of hardcoded parameters, increase the moving average windows, or add a broader volatility filter to make the logic robust.")

    if failed:
        print("\n".join(feedback))
        sys.exit(1)
        
    print(f"✅ [HOLY GRAIL FOUND] Strategy passed both Train and Test splits!\nTrain ROI: {train_roi*100:.2f}%\nTest ROI: {test_roi*100:.2f}%")
    sys.exit(0)

if __name__ == "__main__":
    main()
