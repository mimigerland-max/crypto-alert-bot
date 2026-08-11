"""
Configuration du bot. C'est ICI que tu modifies quels coins et
quels subreddits surveiller, sans toucher au reste du code.
"""

# Dictionnaire : nom du coin -> liste de mots-clés à chercher
# (ajoute autant de variantes que tu veux : ticker, nom complet, avec/sans $)
COINS = {
    "PEPE": ["pepe", "$pepe", "pepecoin"],
    "BONK": ["bonk", "$bonk"],
    "WIF": ["wif", "dogwifhat", "$wif"],
    "SHIB": ["shib", "shiba inu", "$shib"],
    "DOGE": ["doge", "dogecoin", "$doge"],
}

# Subreddits crypto à scanner (sans le "r/")
SUBREDDITS = [
    "CryptoCurrency",
    "CryptoMoonShots",
    "SatoshiStreetBets",
    "CryptoCurrencies",
]

# Nombre de posts récents à récupérer par subreddit à chaque scan
POSTS_PER_SUBREDDIT = 50

# Un coin déclenche une alerte si son nombre de mentions actuel
# dépasse (moyenne historique x ce multiplicateur)
SPIKE_THRESHOLD_MULTIPLIER = 3.0

# Nombre minimum de mentions pour même considérer une alerte
# (évite d'alerter sur du bruit genre "2 mentions au lieu de 1")
MIN_MENTIONS_TO_ALERT = 5

# Fichier où on garde l'historique des mentions (pour calculer la moyenne)
HISTORY_FILE = "history.json"
