from datetime import datetime, timezone

def get_utc_timestamp() -> str:
    """Generiert den von Amazon geforderten ISO-Zeitstempel."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
