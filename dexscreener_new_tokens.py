"""
DexScreener a une API publique gratuite, sans clé, qui liste les
tokens "boostés" (les gens paient pour mettre en avant leur token,
souvent un signe d'activité marketing/hype autour d'un lancement).
C'est un bon signal complémentaire pour repérer les nouveaux tokens
qui commencent à faire parler d'eux, notamment sur Solana (pump.fun
et équivalents).
"""

import requests

DEXSCREENER_BOOSTS_URL = "https://api.dexscreener.com/token-boosts/latest/v1"


def get_boosted_tokens():
    """
    Retourne une liste de dicts avec les tokens récemment boostés :
    [{"symbol": "...", "chain": "solana", "url": "...", "description": "..."}, ...]
    """
    try:
        response = requests.get(DEXSCREENER_BOOSTS_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"[dexscreener_new_tokens] Erreur API DexScreener : {e}")
        return []

    tokens = []
    # L'API renvoie une liste directement (pas de clé "coins")
    items = data if isinstance(data, list) else data.get("tokens", [])

    for item in items:
        token_address = item.get("tokenAddress", "")
        chain = item.get("chainId", "?")
        url = item.get("url", "")
        description = item.get("description", "") or ""

        # On utilise les 8 premiers caractères de l'adresse comme identifiant
        # unique (pas de vrai "symbole" dans cette réponse API)
        short_id = f"{chain}:{token_address[:8]}" if token_address else url

        tokens.append({
            "id": short_id,
            "chain": chain,
            "url": url,
            "description": description[:80],
        })

    return tokens


if __name__ == "__main__":
    # Test : python dexscreener_new_tokens.py
    for t in get_boosted_tokens()[:15]:
        print(f"  {t['id']} ({t['chain']}) - {t['description']}")
