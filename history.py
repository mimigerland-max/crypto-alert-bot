"""
Sans historique, impossible de savoir si "20 mentions de PEPE"
est normal ou énorme. Ce module sauvegarde chaque scan dans un
fichier JSON pour pouvoir calculer une moyenne mobile.
"""

import json
import os
from datetime import datetime, timezone

from config import HISTORY_FILE


def load_history():
    """Charge l'historique existant, ou un historique vide si premier lancement."""
    if not os.path.exists(HISTORY_FILE):
        return {}

    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_scan_result(history, counts):
    """Ajoute le scan actuel à l'historique et sauvegarde sur disque."""
    timestamp = datetime.now(timezone.utc).isoformat()

    for coin, count in counts.items():
        history.setdefault(coin, [])
        history[coin].append({"timestamp": timestamp, "count": count})
        # On garde seulement les 100 derniers scans par coin (évite un fichier énorme)
        history[coin] = history[coin][-100:]

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

    return history


def average_mentions(history, coin, exclude_last_n=1):
    """
    Calcule la moyenne des mentions passées pour un coin,
    en excluant les derniers scans (pour ne pas comparer le
    pic actuel à lui-même).
    """
    entries = history.get(coin, [])
    past_entries = entries[:-exclude_last_n] if exclude_last_n else entries

    if not past_entries:
        return 0.0

    counts = [e["count"] for e in past_entries]
    return sum(counts) / len(counts)
