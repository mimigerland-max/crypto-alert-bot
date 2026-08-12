"""
DexScreener : tokens récemment boostés (payés pour être mis en avant).
"""

import requests

from config import ALLOWED_CHAINS

DEXSCREENER_BOOSTS_URL = "https://api.dexscreener.com/token-boosts/latest/v1"


def get_boosted_tokens():
    try:
        response = requests.get(DEXSCREENER_BOOSTS_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"[dexscreener_new_tokens] Erreur API DexScreener : {e}")
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
