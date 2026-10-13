def count_lines(file_path: str) -> int:
    if not file_path:
        return 0
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            return len(lines)
    except (FileNotFoundError, IsADirectoryError):
        return 0