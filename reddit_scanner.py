"""
Scanne les subreddits configurés et compte combien de fois chaque
coin est mentionné dans les titres + textes des posts récents.

Nécessite un compte app Reddit gratuit (voir README.md, étape 2).
Les identifiants sont lus depuis des variables d'environnement,
JAMAIS écrits en dur dans le code (sécurité).
"""

import os
import praw

from config import COINS, SUBREDDITS, POSTS_PER_SUBREDDIT


def get_reddit_client():
    """Crée le client Reddit à partir des variables d'environnement."""
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError(
            "Variables REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET manquantes. "
            "Voir README.md étape 2."
        )

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent="crypto-alert-bot/1.0 (personal script)",
    )


def count_mentions():
    """
    Retourne un dict {coin: nombre_de_mentions} en scannant les
    posts récents ("new") de chaque subreddit configuré.
    """
    reddit = get_reddit_client()
    counts = {coin: 0 for coin in COINS}
    posts_scanned = 0

    for subreddit_name in SUBREDDITS:
        subreddit = reddit.subreddit(subreddit_name)
        for post in subreddit.new(limit=POSTS_PER_SUBREDDIT):
            posts_scanned += 1
            text = (post.title + " " + (post.selftext or "")).lower()

            for coin, keywords in COINS.items():
                if any(keyword.lower() in text for keyword in keywords):
                    counts[coin] += 1

    print(f"[reddit_scanner] {posts_scanned} posts scannés sur {len(SUBREDDITS)} subreddits.")
    return counts


if __name__ == "__main__":
    # Permet de tester ce fichier seul : python reddit_scanner.py
    result = count_mentions()
    for coin, n in result.items():
        print(f"  {coin}: {n} mentions")
