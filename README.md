# SAGETRIM ExpertForm

Générateur de rapport d'expertise immobilière pour Luc SILVESTRE / Cabinet SAGETRIM.

## Déploiement en 3 étapes

### 1. Pousser sur GitHub
```bash
git init
git add .
git commit -m "Initial — SAGETRIM ExpertForm"
git remote add origin https://github.com/TON_COMPTE/sagetrim-expert.git
git push -u origin main
```

### 2. Connecter à Vercel
1. Aller sur [vercel.com](https://vercel.com)
2. "Add New Project" → Importer le repo GitHub `sagetrim-expert`
3. Framework : **Next.js** (détecté automatiquement)
4. Cliquer "Deploy"

### 3. C'est en ligne
Vercel donne une URL type `https://sagetrim-expert.vercel.app`

---

## Développement local

```bash
npm install
vercel dev          # Lance Next.js + API Python ensemble
```

## Stack
- Next.js 14 (frontend)
- Python + ReportLab (génération PDF)
- Vercel (hébergement)
- Données DVF : API Cerema open-data
