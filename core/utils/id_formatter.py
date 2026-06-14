def format_ui_id(prefix: str, start_from: int, postgres_ui_id: int) -> str:
    """
    Combines the user-configured prefix and start_from with the postgres auto-increment.
    e.g. format_ui_id("CUS", 1, 5) -> "CUS-0005"
    """
    p = f"{prefix}-" if prefix else ""
    sequence_num = (postgres_ui_id - 1) + start_from
    s = str(sequence_num).zfill(4)
    return f"{p}{s}"
