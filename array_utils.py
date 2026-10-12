def max_difference(arr: list) -> float:
    if len(arr) < 2:
        return 0.0
    return max(arr) - min(arr)