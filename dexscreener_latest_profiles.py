"""
Flux DexScreener des tokens tout juste créés (profils récents).
Signal le plus rapide, mais aussi le plus risqué.
"""

import requests

from config import ALLOWED_CHAINS

LATEST_PROFILES_URL = "https://api.dexscreener.com/token-profiles/latest/v1"


def get_latest_new_tokens():
    try:
        response = requests.get(LATEST_PROFILES_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"[dexscreener_latest_profiles] Erreur API : {e}")
        return []

    items = data if isinstance(data, list) else data.get("tokens", [])
    tokens = []

    for item in items:
        token_address = item.get("tokenAddress", "")
        chain = item.get("chainId", "?")

        if ALLOWED_CHAINS and chain not in ALLOWED_CHAINS:
            continue

        url = item.get("url", "")
        description = (item.get("description", "") or "")[:120]

        tokens.append({
            "id": f"{chain}:{token_address}",
            "token_address": token_address,
            "chain": chain,
            "url": url or f"https://dexscreener.com/{chain}/{token_address}",
            "description": description,
        })

    return tokens
