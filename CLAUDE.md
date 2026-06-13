# SAGETRIM ExpertForm — CLAUDE.md

## Contexte du projet

Application web de génération de rapports d'expertise immobilière pour
**Luc SILVESTRE / Cabinet SAGETRIM** (Les Abymes, Guadeloupe).

L'application permet à Luc de saisir les données d'une expertise en 6 étapes
et de générer un PDF professionnel conforme à la Charte de l'Expertise en
Évaluation Immobilière (TEGoVA 5ᵉ éd.).

## Stack technique

- **Frontend** : Next.js 14 (React, pages router, CSS modules)
- **Backend** : Python serverless via Vercel (`/api/generer.py`)
- **PDF** : ReportLab (`lib/sagetrim_template.py`)
- **Déploiement** : Vercel + GitHub (auto-deploy sur push main)
- **Données marché** : API Cerema DVF+ open-data (apidf-preprod.cerema.fr)

## Structure des fichiers

```
sagetrim-expert/
├── pages/
│   ├── _app.jsx          ← Layout global
│   └── index.jsx         ← ExpertForm (wizard 6 étapes)
├── api/
│   └── generer.py        ← Endpoint Python → PDF
├── lib/
│   └── sagetrim_template.py  ← Moteur de génération PDF
├── styles/
│   └── globals.css       ← Design system SAGETRIM
├── requirements.txt      ← reportlab==4.2.5
├── package.json
├── vercel.json           ← Config Vercel (Python + Next.js)
└── CLAUDE.md             ← Ce fichier
```

## Types de biens supportés

- **maison** → 3 méthodes : comparaison DVF + sol & construction + actualisation ICC
- **appartement** → 1 méthode : comparaison directe uniquement (pas de vétusté sur comparaison)
- **terrain** → méthode terrain uniquement

## Règles métier critiques (NE PAS modifier)

1. **SHOB abrogée** — Toujours utiliser SDP (art. R.111-22 Code urbanisme, depuis mars 2012)
2. **Vétusté** — Ne JAMAIS appliquer un abattement de vétusté sur une valeur obtenue par comparaison
3. **Appartement** — Méthode par sol & construction interdite pour les appartements
4. **Réserves automatiques** — Tout diagnostic manquant génère une réserve dans le rapport
5. **TEGoVA** — Chaque rapport doit mentionner la Charte de l'Expertise en Évaluation Immobilière

## Design system SAGETRIM

- Navy `#1A2B45` — couleur principale
- Gold `#C8A96E` — accent
- Ivory `#F7F5F0` — fond
- Police : DM Serif Display (titres) + DM Sans (texte)

## Commandes utiles

```bash
npm run dev        # Dev local (frontend Next.js)
# L'API Python ne tourne pas en local sans Vercel CLI
vercel dev         # Dev complet avec API Python (recommandé)
vercel --prod      # Déploiement production
```

## Variables d'environnement Vercel

Aucune requise pour le fonctionnement de base.
Pour DVF en production : `DVF_API_URL=https://apidf-preprod.cerema.fr`

## Points d'attention

- Le générateur PDF est synchrone et peut prendre 2-5 secondes
- Timeout Vercel : 10s (hobby) / 60s (pro) — suffisant
- Taille du bundle Python : ~8MB (ReportLab + dépendances) — OK pour Vercel (limite 50MB)
- CORS configuré pour tous les origins (`*`) — affiner en production si nécessaire
