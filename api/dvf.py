"""
/api/dvf.py
Endpoint Vercel Python — recherche automatique des ventes comparables
dans la base DVF géolocalisée (DGFiP / Etalab — data.gouv.fr).

Flux :
  1. Géocode l'adresse / la commune via la Base Adresse Nationale (BAN)
     → code INSEE + coordonnées.
  2. Télécharge les fichiers DVF géolocalisés de la commune (dernières années).
  3. Nettoie (ventes simples mono-bien, prix/surface valides, hors aberrations).
  4. Filtre par type de bien, calcule le €/m² et la médiane.
  5. Renvoie les comparables prêts à pré-remplir le tableau du formulaire.

Aucune dépendance externe : urllib + csv + json (stdlib).
"""

import io
import csv
import json
import urllib.parse
import urllib.request
from datetime import date
from http.server import BaseHTTPRequestHandler

BAN_URL = "https://api-adresse.data.gouv.fr/search/"
DVF_BASE = "https://files.data.gouv.fr/geo-dvf/latest/csv/{year}/communes/{dept}/{insee}.csv"

# Correspondance type de bien (formulaire) → type_local DVF
TYPE_MAP = {
    "maison": "Maison",
    "appartement": "Appartement",
}

# Garde-fous €/m² pour écarter les valeurs aberrantes (bâti vs terrain)
BORNES_BATI = (300, 9000)
BORNES_TERRAIN = (5, 2000)

UA = {"User-Agent": "SAGETRIM-ExpertForm/1.0 (expertise immobilière)"}


def _http_json(url, timeout=6):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _http_text(url, timeout=8):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def geocode(adresse, commune, code_postal):
    """Retourne (insee, dept, label_commune, lat, lon) ou lève une erreur."""
    query = (adresse or "").strip() or (commune or "").strip()
    if not query:
        raise ValueError("Adresse ou commune requise pour la recherche DVF.")
    params = {"q": query, "limit": 1}
    if code_postal:
        params["postcode"] = str(code_postal).strip()
    data = _http_json(BAN_URL + "?" + urllib.parse.urlencode(params))
    feats = data.get("features") or []
    if not feats:
        # 2e tentative sur la seule commune
        if commune and query != commune:
            return geocode(None, commune, code_postal)
        raise ValueError(f"Commune introuvable pour « {query} ».")
    p = feats[0]["properties"]
    insee = p.get("citycode")
    lon, lat = feats[0]["geometry"]["coordinates"]
    dept = insee[:3] if insee and insee.startswith("97") else (insee[:2] if insee else None)
    return insee, dept, p.get("city"), lat, lon


def _to_float(v):
    try:
        return float(str(v).replace(",", ".")) if v not in (None, "") else 0.0
    except (ValueError, TypeError):
        return 0.0


def fetch_mutations(insee, dept, years):
    """Télécharge et concatène les mutations DVF des années demandées."""
    rows = []
    for y in years:
        url = DVF_BASE.format(year=y, dept=dept, insee=insee)
        try:
            text = _http_text(url)
        except Exception:
            continue  # année non disponible (404/302) → on ignore
        rows.extend(csv.DictReader(io.StringIO(text)))
    return rows


def build_comparables(rows, type_bien, cutoff_iso, surface_sujet=0):
    """Nettoie les mutations et renvoie (comparables triés, médiane €/m²)."""
    type_local = TYPE_MAP.get(type_bien)
    is_terrain = type_bien == "terrain"

    # Compter les lignes par mutation : on ne garde que les ventes mono-ligne
    # (un seul bien) pour un €/m² fiable — on écarte les ventes groupées.
    counts = {}
    for r in rows:
        counts[r.get("id_mutation")] = counts.get(r.get("id_mutation"), 0) + 1

    comps = []
    for r in rows:
        if r.get("nature_mutation") != "Vente":
            continue
        if counts.get(r.get("id_mutation")) != 1:
            continue
        if r.get("date_mutation", "") < cutoff_iso:
            continue
        valeur = _to_float(r.get("valeur_fonciere"))
        if valeur <= 0:
            continue

        if is_terrain:
            if (r.get("type_local") or "").strip():
                continue  # un bâti est présent → pas un terrain nu
            surface = _to_float(r.get("surface_terrain"))
            bornes = BORNES_TERRAIN
            type_lbl = "Terrain"
        else:
            if r.get("type_local") != type_local:
                continue
            surface = _to_float(r.get("surface_reelle_bati"))
            bornes = BORNES_BATI
            type_lbl = type_local

        if surface <= 0:
            continue
        pm2 = round(valeur / surface)
        if not (bornes[0] <= pm2 <= bornes[1]):
            continue

        num = (r.get("adresse_numero") or "").strip()
        voie = (r.get("adresse_nom_voie") or "").strip().title()
        localisation = (f"{num} {voie}".strip()) or r.get("nom_commune", "")

        comps.append({
            "date": r.get("date_mutation", ""),
            "localisation": localisation,
            "type": type_lbl,
            "surface": round(surface),
            "valeur": round(valeur),
            "pm2": pm2,
            "pieces": r.get("nombre_pieces_principales", ""),
            "retenu": True,
            "statut": "Retenue",
        })

    # Tri par pertinence : proximité de surface (si connue) puis date récente
    if surface_sujet > 0:
        comps.sort(key=lambda c: (abs(c["surface"] - surface_sujet), c["date"]))
    else:
        comps.sort(key=lambda c: c["date"], reverse=True)

    comps = comps[:20]
    pm2s = sorted(c["pm2"] for c in comps)
    median = pm2s[len(pm2s) // 2] if pm2s else 0
    # Re-trier l'affichage final par date décroissante
    comps.sort(key=lambda c: c["date"], reverse=True)
    return comps, median


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}

            commune = body.get("commune", "")
            code_postal = body.get("code_postal", "")
            adresse = body.get("adresse_bien", "")
            type_bien = (body.get("type_bien") or "maison").lower()
            periode_mois = int(body.get("periode_mois") or 24)
            surface_sujet = _to_float(body.get("sdp") or body.get("surface"))

            insee, dept, label, lat, lon = geocode(adresse, commune, code_postal)

            # Alsace-Moselle (57/67/68) et Mayotte (976) absents de DVF
            if dept in ("57", "67", "68") or (insee or "").startswith("976"):
                return self._json(200, {
                    "insee": insee, "commune": label, "count": 0, "refs": [],
                    "pm2_median": 0,
                    "warning": "Territoire non couvert par la base DVF "
                               "(Alsace-Moselle ou Mayotte). Saisie manuelle requise.",
                })

            # Fenêtre temporelle + années de fichiers à télécharger.
            today = date.today()
            cutoff = today.replace(year=today.year - (periode_mois // 12),
                                   day=1).isoformat()
            years = [today.year - i for i in range(0, 4)]  # ex. 2026→2023

            rows = fetch_mutations(insee, dept, years)
            comps, median = build_comparables(rows, type_bien, cutoff, surface_sujet)

            self._json(200, {
                "insee": insee,
                "commune": label,
                "dept": dept,
                "periode_mois": periode_mois,
                "count": len(comps),
                "pm2_median": median,
                "refs": comps,
                "source": "Base DVF géolocalisée (DGFiP / Etalab — data.gouv.fr)",
            })

        except ValueError as e:
            self._json(400, {"error": str(e)})
        except Exception as e:
            self._json(500, {"error": f"Erreur recherche DVF : {e}"})

    # ── helpers ────────────────────────────────────────────────────────────
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
