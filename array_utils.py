def calculate_median(arr: list) -> float:
    if not arr:
        raise ValueError("Cannot calculate median of an empty list")
    sorted_arr = sorted(arr)
    n = len(sorted_arr)
    mid = n // 2
    if n % 2 == 1:
        return float(sorted_arr[mid])
    else:
        return (sorted_arr[mid - 1] + sorted_arr[mid]) / 2.0

def test_calculate_median():
    assert calculate_median([1, 3, 5, 7, 9]) == 5.0
    assert calculate_median([10, 20, 30, 40, 50]) == 30.0
    assert calculate_median([1, 2, 3, 4, 5, 6]) == 3.5
    assert calculate_median([100]) == 100.0
    assert calculate_median([1, 2, 3, 4, 5]) == 3.0
    assert calculate_median([5, 3, 1, 4, 2]) == 3.0