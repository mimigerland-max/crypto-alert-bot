"""
Récupère les métadonnées d'un token pump.fun (image, description, réseaux
sociaux) depuis son URI (JSON hébergé sur IPFS/pump.fun). Ces signaux
servent à évaluer la "communauté" et le branding d'un token, en
complément des métriques de marché (liquidité, volume, etc.).
"""

import requests


def fetch_metadata(uri, timeout=6):
    """
    Retourne un dict : {"description", "image", "twitter", "telegram", "website"}
    Retourne un dict vide si l'URI est absent ou si la requête échoue
    (ne doit jamais faire planter le scoring).
    """
    if not uri:
        return {}

    try:
        response = requests.get(uri, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return {}

    return {
        "description": data.get("description") or "",
        "image": data.get("image") or "",
        "twitter": data.get("twitter") or "",
        "telegram": data.get("telegram") or "",
        "website": data.get("website") or "",
    }
