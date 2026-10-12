def max_difference(arr: list[int]) -> int:
    if len(arr) < 2:
        return 0
    return max(arr) - min(arr)
