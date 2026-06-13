"""
/api/generer.py
Endpoint Vercel Python — reçoit les paramètres du formulaire,
génère le rapport PDF, retourne le fichier en téléchargement.
"""

import sys
import os
import json
import base64
import tempfile
import traceback

# Ajouter lib/ au path pour importer sagetrim_template
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from http.server import BaseHTTPRequestHandler
from sagetrim_template import RapportExpertise


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        """Répondre aux preflight CORS."""
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        """
        Reçoit un JSON POST avec les paramètres du rapport,
        génère le PDF, retourne en base64 ou binaire.
        """
        try:
            # Lire le body JSON
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            params = json.loads(body.decode('utf-8'))

            # Valider les paramètres obligatoires
            if not params.get('demandeur_nom'):
                self._json_error(400, "demandeur_nom est obligatoire")
                return
            if not params.get('type_bien'):
                self._json_error(400, "type_bien est obligatoire (maison/appartement/terrain)")
                return

            # Générer le PDF dans un fichier temporaire
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp_path = tmp.name

            rapport = RapportExpertise(params)
            rapport.generer(tmp_path)

            # Lire le PDF généré
            with open(tmp_path, 'rb') as f:
                pdf_bytes = f.read()

            # Nettoyer
            os.unlink(tmp_path)

            # Construire le nom de fichier
            ref    = params.get('ref', 'rapport').replace('/', '-')
            nom    = params.get('demandeur_nom', '').split()[0] if params.get('demandeur_nom') else 'client'
            fname  = f"rapport_expertise_{ref}_{nom}.pdf"

            # Retourner le PDF
            self.send_response(200)
            self._cors_headers()
            self.send_header('Content-Type', 'application/pdf')
            self.send_header('Content-Disposition', f'attachment; filename="{fname}"')
            self.send_header('Content-Length', str(len(pdf_bytes)))
            self.end_headers()
            self.wfile.write(pdf_bytes)

        except json.JSONDecodeError as e:
            self._json_error(400, f"JSON invalide : {e}")
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[ERROR] Génération PDF : {e}\n{tb}")
            self._json_error(500, f"Erreur génération : {str(e)}")

    def do_GET(self):
        """Health check."""
        self._json_response(200, {
            "status": "ok",
            "service": "SAGETRIM — Générateur de rapport d'expertise",
            "version": "1.0.0",
        })

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _json_response(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self._cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json_error(self, code, message):
        self._json_response(code, {"error": message, "code": code})
