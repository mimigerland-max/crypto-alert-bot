"""
Configuration du bot. Modifie ce fichier pour personnaliser
les coins, subreddits, filtres et seuils d'alerte.
"""

# --- Reddit (optionnel, nécessite REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET) ---

COINS = {
    "PEPE": ["pepe", "$pepe", "pepecoin"],
    "BONK": ["bonk", "$bonk"],
    "WIF": ["wif", "dogwifhat", "$wif"],
    "SHIB": ["shib", "shiba inu", "$shib"],
    "DOGE": ["doge", "dogecoin", "$doge"],
}

SUBREDDITS = [
    "CryptoCurrency",
    "CryptoMoonShots",
    "SatoshiStreetBets",
    "CryptoCurrencies",
]

POSTS_PER_SUBREDDIT = 50
SPIKE_THRESHOLD_MULTIPLIER = 3.0
MIN_MENTIONS_TO_ALERT = 5

# --- CoinGecko ---

TOP_N_TO_WATCH = 10
# Alerte aussi si un coin déjà connu monte de X places dans le top (ex: #8 -> #3)
COINGECKO_RANK_JUMP_THRESHOLD = 3

# --- DexScreener (boostés + sniper profils) ---

MAX_BOOSTED_TO_CHECK = 15
MAX_NEW_TOKENS_TO_CHECK = 15

# Chaînes autorisées (liste vide = toutes). Ex: ["solana", "ethereum"]
ALLOWED_CHAINS = ["solana"]

# Liquidité minimale en USD pour alerter (filtre les tokens morts / honeypots évidents)
MIN_LIQUIDITY_USD = 3_000

# --- Score "breakout" (filtre les memecoins à fort potentiel) ---

# Score minimum /100 pour envoyer une alerte DexScreener ou pump.fun
MIN_BREAKOUT_SCORE = 58

# Zone de liquidité idéale : assez pour survivre, pas trop pour être déjà tard
IDEAL_LIQUIDITY_MIN = 5_000
IDEAL_LIQUIDITY_MAX = 120_000
MAX_LIQUIDITY_USD = 400_000

# Au moins 52% d'achats sur les 5 dernières minutes
MIN_BUY_RATIO = 0.52

# Minimum de transactions sur 5 min pour considérer le token actif
MIN_TXNS_M5 = 8

# Tokens de plus de X minutes = trop tard pour le mode sniper early
MAX_TOKEN_AGE_MINUTES = 180

# --- Pump.fun sniper (WebSocket) ---

MIN_SOL_TO_ALERT = 2.0
# Attendre X secondes après création pour laisser le marché se former avant scoring
PUMP_SCORE_DELAY_SECONDS = 25

# Seuil renforcé : le sniper n'alerte QUE si le score dépasse ce seuil
# (plus strict que MIN_BREAKOUT_SCORE, utilisé par dexscreener/boostés).
# ATTENTION : un score élevé = un setup statistiquement plus favorable,
# PAS une garantie de x2/x3. Aucun signal ne peut garantir un pump.
MIN_HIGH_CONVICTION_SCORE = 78

# --- Général ---

HISTORY_FILE = "history.json"
MAX_HISTORY_ENTRIES = 100
