"""
CoinGecko a une API gratuite, sans clé, avec un endpoint qui liste
les coins les plus recherchés sur leur site en ce moment.
C'est un signal complémentaire à Reddit (pas lié à X, mais gratuit
et fiable).
"""

import requests

COINGECKO_TRENDING_URL = "https://api.coingecko.com/api/v3/search/trending"


def get_trending_coins():
    """
    Retourne une liste de dicts : [{"name": "Pepe", "symbol": "PEPE", "rank": 1}, ...]
    Rank 1 = le plus recherché en ce moment sur CoinGecko.
    """
    try:
        response = requests.get(COINGECKO_TRENDING_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"[coingecko_trending] Erreur API CoinGecko : {e}")
        return []

    trending = []
    for i, item in enumerate(data.get("coins", []), start=1):
        coin_data = item.get("item", {})
        trending.append({
            "name": coin_data.get("name"),
            "symbol": coin_data.get("symbol", "").upper(),
            "rank": i,
        })

    return trending


if __name__ == "__main__":
    # Permet de tester ce fichier seul : python coingecko_trending.py
    for coin in get_trending_coins():
        print(f"  #{coin['rank']} {coin['name']} ({coin['symbol']})")
