"""
/api/icc.py
Récupère l'Indice du Coût de la Construction (ICC — INSEE, idbank 000008630)
directement depuis l'API BDM ouverte de l'INSEE (sans authentification).

GET /api/icc?annee=2015&trimestre=1
  → { "acquisition": {"periode":"1er trimestre 2015","indice":1632},
      "actuel":      {"periode":"4e trimestre 2025","indice":2058} }

GET /api/icc                → renvoie seulement l'indice le plus récent.
"""

import json
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler

ICC_URL = "https://api.insee.fr/series/BDM/V1/data/SERIES_BDM/000008630"
_TRIM = ["1er trimestre", "2e trimestre", "3e trimestre", "4e trimestre"]


def _fr(period):
    """'2015-Q1' → '1er trimestre 2015'."""
    try:
        y, q = period.split("-Q")
        return f"{_TRIM[int(q) - 1]} {y}"
    except Exception:
        return period


def _fetch_series():
    req = urllib.request.Request(ICC_URL, headers={
        "Accept": "application/xml",
        "User-Agent": "SAGETRIM-ExpertForm/1.0",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        root = ET.fromstring(r.read())
    obs = {}
    for el in root.iter():
        if el.tag.split("}")[-1] == "Obs":
            p = el.attrib.get("TIME_PERIOD")
            v = el.attrib.get("OBS_VALUE")
            if p and v:
                try:
                    obs[p] = float(v)
                except ValueError:
                    pass
    return obs


def _pick(obs, annee, trimestre):
    """Trouve l'indice du trimestre demandé, ou le plus proche disponible."""
    periods = sorted(obs)
    if trimestre:
        key = f"{annee}-Q{trimestre}"
        if key in obs:
            return key
    same_year = [p for p in periods if p.startswith(f"{annee}-")]
    if same_year:
        # sans trimestre précis → milieu d'année ; sinon dernier dispo de l'année
        return same_year[len(same_year) // 2] if not trimestre else same_year[-1]
    # année hors série → trimestre le plus proche dans le temps
    return min(periods, key=lambda p: abs(int(p[:4]) - int(annee)))


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200); self._cors(); self.end_headers()

    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        annee = (q.get("annee", [None])[0] or "").strip()
        trimestre = (q.get("trimestre", [None])[0] or "").strip()
        try:
            obs = _fetch_series()
            if not obs:
                return self._json(502, {"error": "Série ICC vide côté INSEE"})
            latest = sorted(obs)[-1]
            out = {"actuel": {"periode": _fr(latest), "indice": int(round(obs[latest])), "code": latest}}
            if annee.isdigit():
                key = _pick(obs, annee, trimestre if trimestre.isdigit() else None)
                out["acquisition"] = {"periode": _fr(key), "indice": int(round(obs[key])), "code": key}
            out["source"] = "INSEE — ICC idbank 000008630"
            self._json(200, out)
        except Exception as e:
            self._json(502, {"error": f"INSEE indisponible : {e}"})

    # ── helpers ──
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code); self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
