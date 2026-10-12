# -*- coding: utf-8 -*-
"""Strategy module for generating simple trading signals."""

# The __future__ import must be the very first statement (after the module docstring).
from __future__ import annotations

from typing import Iterable, List


def generate_signals(prices: Iterable[float]) -> List[str]:
    """
    Generate a list of trading signals based on a sequence of price data.

    The simple heuristic used here is:
      * If the current price is higher than the previous price → "buy"
      * If the current price is lower than the previous price → "sell"
      * If the price is unchanged → "hold"

    Parameters
    ----------
    prices: Iterable[float]
        An iterable of price points (e.g., closing prices).

    Returns
    -------
    List[str]
        A list of signals, one for each price after the first one.
        The length of the returned list is ``len(prices) - 1``.
    """
    # Convert to a list so we can index it multiple times.
    price_list = list(prices)

    if len(price_list) < 2:
        # Not enough data to generate a signal.
        return []

    signals: List[str] = []
    for previous, current in zip(price_list, price_list[1:]):
        if current > previous:
            signals.append("buy")
        elif current < previous:
            signals.append("sell")
        else:
            signals.append("hold")
    return signals
