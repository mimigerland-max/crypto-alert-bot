"""
Flux des tokens TOUT JUSTE créés sur DexScreener (avant même d'être
"boostés"). C'est le signal le plus rapide et le plus brut possible
avec des APIs gratuites — mais aussi le plus risqué : à ce stade,
un token peut avoir quelques minutes d'existence.
"""

import requests

LATEST_PROFILES_URL = "https://api.dexscreener.com/token-profiles/latest/v1"


def get_latest_new_tokens():
    """
    Retourne les tokens les plus récemment listés (profils créés),
    tous chains confondues. Format similaire à get_boosted_tokens().
    """
    try:
        response = requests.get(LATEST_PROFILES_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"[dexscreener_latest_profiles] Erreur API : {e}")
        return []

    tokens = []
    items = data if isinstance(data, list) else data.get("tokens", [])

    for item in items:
        token_address = item.get("tokenAddress", "")
        chain = item.get("chainId", "?")
        url = item.get("url", "")
        description = (item.get("description", "") or "")[:80]

        short_id = f"{chain}:{token_address[:8]}" if token_address else url

        tokens.append({
            "id": short_id,
            "chain": chain,
            "url": url,
            "description": description,
        })

    return tokens


if __name__ == "__main__":
    for t in get_latest_new_tokens()[:15]:
        print(f"  {t['id']} ({t['chain']}) - {t['description']}")
