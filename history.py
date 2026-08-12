"""
Historique des scans pour éviter les alertes en double et
calculer les moyennes (Reddit) ou les variations de rang (CoinGecko).
"""

import json
import os
from datetime import datetime, timezone

from config import HISTORY_FILE, MAX_HISTORY_ENTRIES


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_scan_result(history, counts):
    timestamp = datetime.now(timezone.utc).isoformat()

    for key, count in counts.items():
        history.setdefault(key, [])
        history[key].append({"timestamp": timestamp, "count": count})
        history[key] = history[key][-MAX_HISTORY_ENTRIES:]

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    return history


def was_seen(history, key):
    return key in history and len(history[key]) > 0


def last_value(history, key):
    entries = history.get(key, [])
    if not entries:
        return None
    return entries[-1]["count"]


def average_mentions(history, coin, exclude_last_n=1):
    entries = history.get(coin, [])
    past_entries = entries[:-exclude_last_n] if exclude_last_n else entries

    if not past_entries:
        return 0.0

    counts = [e["count"] for e in past_entries]
    return sum(counts) / len(counts)
