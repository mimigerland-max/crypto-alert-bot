# Crypto Alert Bot (gratuit)

Bot qui surveille Reddit (r/CryptoCurrency, r/CryptoMoonShots, etc.) et
alerte sur Discord quand un coin est mentionné anormalement souvent.
100% gratuit : Reddit API (gratuite), GitHub Actions (gratuit), Discord
webhook (gratuit).

**Important : ce bot n'inclut PAS X/Twitter** (l'API coûte cher, voir la
conversation). Il se base sur Reddit + CoinGecko trending.

---

## Étape 1 — Tester en local (optionnel mais recommandé)

```bash
pip install -r requirements.txt
python main.py
```

Sans identifiants Reddit configurés, ça plantera à l'étape Reddit — normal,
passe à l'étape 2.

## Étape 2 — Créer un compte app Reddit (gratuit, 2 minutes)

1. Va sur https://www.reddit.com/prefs/apps
2. Clique sur "create app" / "create another app" en bas
3. Choisis le type **"script"**
4. Nom : ce que tu veux (ex: "mon-crypto-bot")
5. Redirect URI : mets `http://localhost:8080` (obligatoire mais inutilisé ici)
6. Clique "create app"
7. Tu obtiens :
   - **client_id** : la chaîne sous le nom de l'app (ex: `a1B2c3D4e5F6`)
   - **client_secret** : à côté de "secret"

Garde ces deux valeurs, tu en as besoin à l'étape 4.

## Étape 3 — Créer un webhook Discord (gratuit, 2 minutes)

1. Dans ton serveur Discord, va dans les paramètres du salon où tu veux
   recevoir les alertes
2. Intégrations → Webhooks → "Nouveau webhook"
3. Donne-lui un nom (ex: "Crypto Alerts")
4. Clique "Copier l'URL du webhook"

Garde cette URL, tu en as besoin à l'étape 4.

## Étape 4 — Mettre en ligne sur GitHub (pour que ça tourne 24/7 gratuitement)

1. Crée un nouveau repo GitHub (peut être privé)
2. Mets-y tous les fichiers de ce projet
3. Va dans **Settings → Secrets and variables → Actions → New repository secret**
   et ajoute ces 3 secrets :
   - `REDDIT_CLIENT_ID` → ta valeur de l'étape 2
   - `REDDIT_CLIENT_SECRET` → ta valeur de l'étape 2
   - `DISCORD_WEBHOOK_URL` → ton URL de l'étape 3
4. Va dans l'onglet **Actions** du repo, active les workflows si demandé
5. Le bot tournera automatiquement toutes les 30 minutes (configurable dans
   `.github/workflows/scan.yml`, ligne `cron`)
6. Tu peux aussi le lancer manuellement : onglet Actions → "Crypto Alert Scan"
   → "Run workflow"

## Personnaliser

- **Ajouter/retirer des coins** : édite `COINS` dans `config.py`
- **Ajouter des subreddits** : édite `SUBREDDITS` dans `config.py`
- **Rendre le seuil plus/moins sensible** : `SPIKE_THRESHOLD_MULTIPLIER`
  dans `config.py` (plus haut = moins d'alertes, mais plus fiables)
- **Changer la fréquence de scan** : modifie le `cron` dans
  `.github/workflows/scan.yml`

## Limites à connaître

- Pas de données X/Twitter (payant) — Reddit réagit souvent un peu après X
  sur les memecoins qui explosent d'abord sur Twitter
- Un pic de mentions Reddit n'est pas une garantie de hausse de prix —
  c'est un signal parmi d'autres, pas un conseil financier
- Les mentions comptent aussi les posts négatifs ("PEPE va s'effondrer")
  — v1 ne fait pas d'analyse de sentiment, juste du volume
