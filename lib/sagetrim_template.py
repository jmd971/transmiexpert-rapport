"""
═══════════════════════════════════════════════════════════════════════════════
SAGETRIM — TEMPLATE MAÎTRE PARAMÉTRABLE
Générateur de rapport d'expertise immobilière — Luc SILVESTRE
═══════════════════════════════════════════════════════════════════════════════

USAGE :
    from sagetrim_template import RapportExpertise, EXEMPLE_MAISON, EXEMPLE_APPART
    rapport = RapportExpertise(EXEMPLE_MAISON)
    rapport.generer("/mnt/user-data/outputs/rapport.pdf")

TYPES DE BIENS SUPPORTÉS :
    "maison"      → 3 méthodes : comparaison + sol & construction + actualisation
    "appartement" → 1 méthode : comparaison directe uniquement
    "terrain"     → méthode terrain uniquement

VARIABLES OBLIGATOIRES : voir SCHEMA_VARIABLES en bas de fichier
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Image as RLImage
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY
import datetime
import io
import base64

# ─── PALETTE SAGETRIM ────────────────────────────────────────────────────────
NAVY   = colors.HexColor("#1A2B45")
GOLD   = colors.HexColor("#C8A96E")
LIGHT  = colors.HexColor("#F7F5F0")
BORDER = colors.HexColor("#D0C8B8")
TEXT   = colors.HexColor("#1A1712")
MUTED  = colors.HexColor("#6B6355")
ALERT  = colors.HexColor("#8B2020")
ORANGE = colors.HexColor("#C8682A")
GREEN  = colors.HexColor("#1A4A2E")
W      = colors.white

# ─── CONSTANTES CABINET ──────────────────────────────────────────────────────
CABINET = {
    "nom"      : "SAGETRIM",
    "sous_nom" : "Cabinet Martial — Syndic de copropriétés — Administrateur de Biens",
    "expert"   : "Luc SILVESTRE",
    "titre"    : "Expert en évaluation immobilière",
    "adresse"  : "37 Espace Rocade — Grand-Camp — 97139 Les Abymes (Guadeloupe)",
    "tel"      : "0590 82 78 76",
    "rc"       : "RC N° 77B22",
    "siret"    : "31004861600026",
    "ape"      : "6831Z",
    "capital"  : "13 720,41 €",
    "rcp"      : "Sévères Assurance — Garantie financière : 500 000 €",
    "norme"    : ("Charte de l'Expertise en Évaluation Immobilière (5ᵉ éd. 2019) "
                  "et normes TEGoVA (EVS 2022)"),
    "refs_legales": (
        "Code civil art. 1075 (donation-partage) — "
        "Code de l'urbanisme art. R. 111-22 (Surface de Plancher — SDP, "
        "en vigueur depuis le 1ᵉʳ mars 2012 — décret 2011-2054 abrogeant SHOB/SHON) — "
        "CCH art. L. 271-4 (diagnostics obligatoires) — "
        "Base DVF+ open-data (DGFiP / Cerema — data.gouv.fr) — "
        "Géorisques (georisques.gouv.fr)"
    ),
}

PAGE_W, PAGE_H = A4
ML, MR = 2.2*cm, 2.0*cm
MT_TOP = 2.5*cm + 1.8*cm   # réserve header
MB_BOT = 2.5*cm + 1.0*cm   # réserve footer
CW = PAGE_W - ML - MR


# ═══════════════════════════════════════════════════════════════════════════════
# STYLES
# ═══════════════════════════════════════════════════════════════════════════════
def _styles():
    b = dict(fontName="Helvetica", fontSize=10, leading=14, textColor=TEXT)
    return {
        "n"  : ParagraphStyle("n",  **b, spaceAfter=4),
        "j"  : ParagraphStyle("j",  **b, alignment=TA_JUSTIFY, spaceAfter=6),
        "h1" : ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=13,
                               leading=18, textColor=W),
        "h2" : ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11,
                               leading=15, textColor=NAVY,
                               spaceAfter=4, spaceBefore=10),
        "h3" : ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=10,
                               leading=14, textColor=NAVY,
                               spaceAfter=3, spaceBefore=6),
        "lbl": ParagraphStyle("lbl", fontName="Helvetica-Bold", fontSize=9,
                               leading=12, textColor=MUTED),
        "val": ParagraphStyle("val", fontName="Helvetica", fontSize=10,
                               leading=13, textColor=TEXT, spaceAfter=4),
        "sm" : ParagraphStyle("sm",  fontName="Helvetica", fontSize=8,
                               leading=11, textColor=TEXT),
        "smm": ParagraphStyle("smm", fontName="Helvetica", fontSize=8,
                               leading=11, textColor=MUTED),
        "alrt":ParagraphStyle("alrt",fontName="Helvetica-Bold", fontSize=9,
                               leading=13, textColor=ALERT, spaceAfter=4),
        "it" : ParagraphStyle("it",  fontName="Helvetica-Oblique", fontSize=9,
                               leading=13, textColor=MUTED, spaceAfter=4,
                               alignment=TA_JUSTIFY),
        "concl":ParagraphStyle("concl",fontName="Helvetica-Bold",fontSize=14,
                                leading=20, textColor=NAVY, alignment=TA_CENTER),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# COMPOSANTS PDF RÉUTILISABLES
# ═══════════════════════════════════════════════════════════════════════════════
class _Comp:
    def __init__(self, S):
        self.S = S

    def section(self, titre):
        t = Table([[Paragraph(titre, self.S["h1"])]], colWidths=[CW])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), NAVY),
            ("TOPPADDING",    (0,0),(-1,-1), 7),
            ("BOTTOMPADDING", (0,0),(-1,-1), 7),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
            ("LINEBELOW",     (0,0),(-1,-1), 2, GOLD),
        ]))
        return t

    def kv(self, rows, c1=6*cm):
        c2 = CW - c1
        data = [[Paragraph(f"<b>{k}</b>", self.S["lbl"]),
                 Paragraph(str(v), self.S["val"])] for k, v in rows]
        t = Table(data, colWidths=[c1, c2])
        t.setStyle(TableStyle([
            ("VALIGN",        (0,0),(-1,-1), "TOP"),
            ("TOPPADDING",    (0,0),(-1,-1), 4),
            ("BOTTOMPADDING", (0,0),(-1,-1), 4),
            ("LEFTPADDING",   (0,0),(-1,-1), 6),
            ("ROWBACKGROUNDS",(0,0),(-1,-1), [W, LIGHT]),
            ("LINEBELOW",     (0,0),(-1,-1), 0.3, BORDER),
        ]))
        return t

    def legal(self, texte):
        t = Table([[Paragraph(texte, self.S["sm"])]], colWidths=[CW])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), colors.HexColor("#EEF3FA")),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
            ("TOPPADDING",    (0,0),(-1,-1), 6),
            ("BOTTOMPADDING", (0,0),(-1,-1), 6),
            ("LINELEFT",      (0,0),(-1,-1), 3, NAVY),
        ]))
        return t

    def reserve(self, texte, couleur=ALERT, bg="#FDF6E3"):
        style = ParagraphStyle("r", fontName="Helvetica-Bold", fontSize=9,
                                leading=13, textColor=couleur)
        t = Table([[Paragraph(f"Réserve : {texte}", style)]], colWidths=[CW])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), colors.HexColor(bg)),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
            ("TOPPADDING",    (0,0),(-1,-1), 6),
            ("BOTTOMPADDING", (0,0),(-1,-1), 6),
            ("LINELEFT",      (0,0),(-1,-1), 3, couleur),
        ]))
        return t

    def conclusion_box(self, val_min, val_ret, val_max):
        fmt = lambda n: f"{n:,.0f}\u202f€".replace(",", "\u202f")
        data = [
            [Paragraph("<b>VALEUR VÉNALE RETENUE</b>",
                        ParagraphStyle("cv", fontName="Helvetica-Bold",
                                       fontSize=11, textColor=W,
                                       alignment=TA_CENTER)),
             Paragraph(f"<b>{fmt(val_ret)}</b>",
                        ParagraphStyle("cv2", fontName="Helvetica-Bold",
                                       fontSize=22, textColor=GOLD,
                                       alignment=TA_CENTER))],
            [Paragraph("Fourchette basse", self.S["smm"]),
             Paragraph(fmt(val_min), self.S["smm"])],
            [Paragraph("Fourchette haute", self.S["smm"]),
             Paragraph(fmt(val_max), self.S["smm"])],
            [Paragraph("Hors fiscalité — hors frais d'acte", self.S["it"]),
             Paragraph("", self.S["smm"])],
        ]
        t = Table(data, colWidths=[CW * 0.45, CW * 0.55])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0),  NAVY),
            ("BACKGROUND",    (0,1),(-1,-1), LIGHT),
            ("TOPPADDING",    (0,0),(-1,-1), 8),
            ("BOTTOMPADDING", (0,0),(-1,-1), 8),
            ("LEFTPADDING",   (0,0),(-1,-1), 12),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
            ("LINEBELOW",     (0,0),(-1,-1), 0.5, BORDER),
            ("BOX",           (0,0),(-1,-1), 2, GOLD),
        ]))
        return t

    def dvf_table(self, refs, pm2_median):
        header = [Paragraph(f"<b>{h}</b>", self.S["lbl"]) for h in
                  ["Date","Localisation / Résidence","Type","SDP","Valeur","€/m²","Statut"]]
        rows = [header]
        for r in refs:
            retenu = r.get("retenu", True)
            pm2 = r.get("pm2", 0)
            diff = round((pm2 - pm2_median) / pm2_median * 100) if pm2_median else 0
            sign = "+" if diff >= 0 else ""
            statut = r.get("statut", ("Retenue" if retenu else "Écartée"))
            style = self.S["smm"] if not retenu else self.S["sm"]
            rows.append([
                Paragraph(r.get("date",""), style),
                Paragraph(r.get("localisation",""), style),
                Paragraph(r.get("type",""), style),
                Paragraph(f"{r.get('surface',0)} m²", style),
                Paragraph(f"{r.get('valeur',0):,.0f}\u202f€".replace(",","\u202f"), style),
                Paragraph(f"{pm2:,}\u202f€".replace(",","\u202f"), style),
                Paragraph(statut, self.S["smm"] if not retenu else
                          ParagraphStyle("ok",fontName="Helvetica-Bold",
                                         fontSize=8,textColor=GREEN) if "principale" in statut.lower()
                          else style),
            ])
        # Ligne médiane
        rows.append([
            Paragraph("<b>MÉDIANE RETENUE</b>", self.S["lbl"]),
            Paragraph(f"{sum(1 for r in refs if r.get('retenu',True))} références", self.S["smm"]),
            Paragraph("", self.S["smm"]),
            Paragraph("", self.S["smm"]),
            Paragraph("", self.S["smm"]),
            Paragraph(f"<b>{pm2_median:,}\u202f€/m²</b>".replace(",","\u202f"), self.S["lbl"]),
            Paragraph("Base de calcul", self.S["smm"]),
        ])
        widths = [2.2*cm, 4.5*cm, 1.5*cm, 1.8*cm, 2.8*cm, 2.5*cm, CW-15.3*cm]
        t = Table(rows, colWidths=widths)
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  NAVY),
            ("TEXTCOLOR",     (0,0), (-1,0),  W),
            ("FONTSIZE",      (0,0), (-1,0),  8),
            ("ROWBACKGROUNDS",(0,1), (-1,-2), [W, LIGHT]),
            ("BACKGROUND",    (0,-1),(-1,-1), colors.HexColor("#EAF0E8")),
            ("LINEABOVE",     (0,-1),(-1,-1), 2, GOLD),
            ("GRID",          (0,0), (-1,-1), 0.3, BORDER),
            ("TOPPADDING",    (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING",   (0,0), (-1,-1), 4),
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ]))
        return t

    def risque_table(self, risques):
        header = [Paragraph(f"<b>{h}</b>", self.S["lbl"]) for h in
                  ["Risque","Niveau","Impact valeur","Source"]]
        rows = [header]
        for r in risques:
            rows.append([Paragraph(c, self.S["sm"]) for c in r])
        widths = [4.5*cm, 2.5*cm, 7*cm, CW-14*cm]
        t = Table(rows, colWidths=widths)
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0),  NAVY),
            ("TEXTCOLOR",     (0,0),(-1,0),  W),
            ("FONTSIZE",      (0,0),(-1,0),  8),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [W, LIGHT]),
            ("GRID",          (0,0),(-1,-1), 0.3, BORDER),
            ("TOPPADDING",    (0,0),(-1,-1), 4),
            ("BOTTOMPADDING", (0,0),(-1,-1), 4),
            ("LEFTPADDING",   (0,0),(-1,-1), 5),
            ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ]))
        return t

    def synth_table(self, methodes):
        header = [Paragraph(f"<b>{h}</b>", self.S["lbl"]) for h in
                  ["Méthode","Valeur","Pondération","Contribution"]]
        rows = [header]
        for m in methodes:
            rows.append([Paragraph(str(c), self.S["sm"]) for c in m])
        widths = [7*cm, 3.5*cm, 3*cm, CW-13.5*cm]
        t = Table(rows, colWidths=widths)
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  NAVY),
            ("TEXTCOLOR",     (0,0), (-1,0),  W),
            ("FONTSIZE",      (0,0), (-1,0),  8),
            ("ROWBACKGROUNDS",(0,1), (-1,-2), [W, LIGHT]),
            ("BACKGROUND",    (0,-1),(-1,-1), colors.HexColor("#EAF0E8")),
            ("LINEABOVE",     (0,-1),(-1,-1), 2, GOLD),
            ("GRID",          (0,0), (-1,-1), 0.3, BORDER),
            ("TOPPADDING",    (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING",   (0,0), (-1,-1), 6),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        return t


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CALLBACKS
# ═══════════════════════════════════════════════════════════════════════════════
def _cover_callback(p):
    """Retourne une fonction callback de couverture paramétrée."""
    def draw(canvas, doc):
        canvas.saveState()
        # Fond navy
        canvas.setFillColor(NAVY)
        canvas.rect(0, PAGE_H/2, PAGE_W, PAGE_H/2, fill=1, stroke=0)
        canvas.setFillColor(GOLD)
        canvas.rect(0, PAGE_H/2 - 4*mm, PAGE_W, 4*mm, fill=1, stroke=0)

        # En-tête cabinet
        canvas.setFillColor(W)
        canvas.setFont("Helvetica-Bold", 22)
        canvas.drawCentredString(PAGE_W/2, PAGE_H - 3.5*cm, CABINET["nom"])
        canvas.setFont("Helvetica", 10)
        canvas.drawCentredString(PAGE_W/2, PAGE_H - 4.3*cm, CABINET["sous_nom"])
        canvas.setFillColor(GOLD)
        canvas.setFont("Helvetica", 9)
        canvas.drawCentredString(PAGE_W/2, PAGE_H - 5.0*cm, "Guadeloupe")

        # Titre rapport
        canvas.setFillColor(W)
        canvas.setFont("Helvetica-Bold", 26)
        canvas.drawCentredString(PAGE_W/2, PAGE_H - 7.0*cm, "RAPPORT D'EXPERTISE")
        canvas.setFont("Helvetica", 12)
        canvas.drawCentredString(PAGE_W/2, PAGE_H - 7.9*cm,
                                 "Évaluation en valeur vénale")

        canvas.setStrokeColor(GOLD)
        canvas.line(3*cm, PAGE_H/2+4.5*cm, PAGE_W-3*cm, PAGE_H/2+4.5*cm)

        # Bloc bien
        y = PAGE_H/2 - 1.2*cm
        canvas.setFillColor(NAVY)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawCentredString(PAGE_W/2, y, "BIEN EXPERTISÉ")
        y -= 0.65*cm
        canvas.setFont("Helvetica-Bold", 12)
        bien_titre = p.get("adresse_bien", p.get("commune","")).upper()
        canvas.drawCentredString(PAGE_W/2, y, bien_titre[:70])
        y -= 0.55*cm
        canvas.setFont("Helvetica", 10)
        sous = f"{p.get('type_bien_label','Bien immobilier')} — {p.get('commune','')} ({p.get('code_postal','')})"
        canvas.drawCentredString(PAGE_W/2, y, sous)

        # Bloc demandeur
        y -= 1.3*cm
        canvas.setFillColor(LIGHT)
        canvas.roundRect(2.5*cm, y-1.8*cm, PAGE_W-5*cm, 1.8*cm, 4*mm, fill=1, stroke=0)
        canvas.setFillColor(NAVY)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(3.0*cm, y-0.6*cm, "Demandeur :")
        canvas.setFont("Helvetica", 9)
        canvas.drawString(3.0*cm, y-1.1*cm, p.get("demandeur_nom",""))
        canvas.drawString(3.0*cm, y-1.5*cm, f"Mission : {p.get('objet_mission','Estimation en valeur vénale')}")

        # Infos
        y -= 3.2*cm
        infos = [
            ("Référence dossier", p.get("ref", "")),
            ("Date de visite",    p.get("date_visite", "")),
            ("Date du rapport",   p.get("date_rapport", "")),
            ("Hypothèse",         p.get("hypothese", "Valeur vénale — pleine propriété — hors fiscalité")),
        ]
        for lbl, val in infos:
            canvas.setFont("Helvetica-Bold", 8.5); canvas.setFillColor(MUTED)
            canvas.drawString(3*cm, y, lbl)
            canvas.setFont("Helvetica", 8.5); canvas.setFillColor(NAVY)
            canvas.drawString(9*cm, y, str(val)); y -= 0.55*cm

        # Pied de page couverture
        y = 2.2*cm
        canvas.setStrokeColor(BORDER); canvas.setLineWidth(0.5)
        canvas.line(ML, y+0.8*cm, PAGE_W-MR, y+0.8*cm)
        canvas.setFont("Helvetica-Bold", 8.5); canvas.setFillColor(NAVY)
        canvas.drawString(ML, y+0.3*cm, CABINET["expert"])
        canvas.setFont("Helvetica", 8); canvas.setFillColor(MUTED)
        canvas.drawString(ML, y-0.15*cm, f"{CABINET['titre']}  •  {CABINET['adresse']}")
        canvas.drawString(ML, y-0.55*cm,
                          f"{CABINET['rc']}  •  SIRET {CABINET['siret']}  •  RCP : {CABINET['rcp']}")
        canvas.drawRightString(PAGE_W-MR, y-0.15*cm, CABINET["tel"])
        canvas.restoreState()
    return draw


def _header_footer_callback(p):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, PAGE_H-1.5*cm, PAGE_W, 1.5*cm, fill=1, stroke=0)
        canvas.setFillColor(W); canvas.setFont("Helvetica-Bold", 8.5)
        canvas.drawString(ML, PAGE_H-0.95*cm, f"SAGETRIM — {CABINET['expert']}")
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(PAGE_W-MR, PAGE_H-0.95*cm,
            f"{p.get('ref','')}  •  {p.get('demandeur_nom','').split()[0] if p.get('demandeur_nom') else ''}  •  {p.get('date_rapport','')}")
        canvas.setStrokeColor(GOLD); canvas.setLineWidth(1.5)
        canvas.line(0, PAGE_H-1.52*cm, PAGE_W, PAGE_H-1.52*cm)
        canvas.setStrokeColor(BORDER); canvas.setLineWidth(0.5)
        canvas.line(ML, 1.6*cm, PAGE_W-MR, 1.6*cm)
        canvas.setFillColor(MUTED); canvas.setFont("Helvetica", 7.5)
        canvas.drawString(ML, 1.1*cm,
            f"Rapport établi conformément à la {CABINET['norme']}.")
        canvas.drawRightString(PAGE_W-MR, 0.65*cm, f"Page {doc.page}")
        canvas.restoreState()
    return draw


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════
class RapportExpertise:
    """
    Générateur de rapport d'expertise SAGETRIM.

    Paramètres (dict) → PDF professionnel conforme Charte TEGoVA.

    Adapte automatiquement les méthodes d'évaluation selon le type de bien :
    - maison      → comparaison + sol & construction + actualisation (si vente antérieure)
    - appartement → comparaison directe uniquement
    - terrain     → méthode terrain uniquement
    """

    def __init__(self, params: dict):
        self.p = self._valider(params)
        self.S = _styles()
        self.C = _Comp(self.S)
        self.story = []
        self._reserves = []   # accumulateur de réserves automatiques

    # ── VALIDATION ────────────────────────────────────────────────────────────
    def _valider(self, p):
        type_bien = p.get("type_bien", "maison")
        labels = {"maison":"Maison individuelle","appartement":"Appartement en copropriété","terrain":"Terrain nu"}
        p["type_bien"] = type_bien
        p["type_bien_label"] = labels.get(type_bien, type_bien)
        # Valeurs par défaut
        p.setdefault("hypothese", "Valeur vénale — pleine propriété — hors fiscalité")
        p.setdefault("objet_mission", "Estimation en valeur vénale")
        p.setdefault("zone_sismique", "V")
        p.setdefault("assainissement", "Collectif")
        p.setdefault("reserves_initiales", "Néant sauf indication contraire")
        return p

    # ── RÉSERVES AUTOMATIQUES ─────────────────────────────────────────────────
    def _ajouter_reserve(self, texte, niveau="alerte"):
        self._reserves.append((texte, niveau))

    def _collecter_reserves(self):
        """Génère les réserves automatiques selon les diagnostics manquants."""
        diags = {
            "diag_amiante" : "Diagnostic amiante non fourni (obligatoire si construction avant 1997)",
            "diag_termites": "Diagnostic termites non fourni (obligatoire en zone contaminée)",
            "diag_elec"    : "Diagnostic électricité non fourni (obligatoire si installation > 15 ans)",
            "diag_dpe"     : "DPE non fourni — classe énergétique inconnue",
        }
        for key, msg in diags.items():
            if not self.p.get(key, False):
                self._ajouter_reserve(msg)
        if not self.p.get("sdp"):
            self._ajouter_reserve("Surface de Plancher (SDP) non renseignée — valeur indicative", "info")

    # ── HELPERS STORY ─────────────────────────────────────────────────────────
    def _add(self, *items):
        for item in items:
            if item is not None:
                self.story.append(item)

    def _sp(self, h=6):
        return Spacer(1, h)

    def _fmt(self, n):
        """Formate un nombre en euros avec séparateur espace insécable."""
        return f"{n:,.0f}\u202f€".replace(",", "\u202f")

    # ═════════════════════════════════════════════════════════════════════════
    # SECTIONS DU RAPPORT
    # ═════════════════════════════════════════════════════════════════════════

    def _section_I_serment(self):
        p = self.p
        self._add(
            self.C.section("I  —  PRESTATION DE SERMENT"),
            self._sp(8),
            Paragraph(
                f"Je soussigné, <b>{CABINET['expert']}</b>, {CABINET['titre']}, "
                f"domicilié au {CABINET['adresse']}, avoir pris acte de la mission "
                f"qui m'a été confiée par <b>{p.get('demandeur_nom','')}</b>.",
                self.S["j"]),
            self._sp(4),
            Paragraph("Je déclare accepter la présente mission.", self.S["j"]),
            self._sp(4),
            Paragraph("Je m'engage à la remplir fidèlement, consciencieusement et impartialement, "
                      f"conformément aux dispositions de la <b>{CABINET['norme']}</b>.",
                      self.S["j"]),
            self._sp(20),
            Paragraph(f"<b>{CABINET['nom']}</b>",
                      ParagraphStyle("cab", fontName="Helvetica-Bold", fontSize=11,
                                     alignment=TA_RIGHT, textColor=NAVY)),
            self._sp(4),
            Paragraph(f"<b>{CABINET['expert']}</b>",
                      ParagraphStyle("exp", fontName="Helvetica-Bold", fontSize=11,
                                     alignment=TA_RIGHT, textColor=NAVY)),
            self._sp(8),
        )

    def _section_II_clause(self):
        self._add(
            self.C.section("II  —  CLAUSE SPÉCIFIQUE DE CONFIDENTIALITÉ"),
            self._sp(6),
            Paragraph(
                "Il est formellement convenu qu'il est interdit au client d'utiliser le présent "
                "rapport d'expertise de façon partielle en isolant telle ou telle partie de son contenu.",
                self.S["j"]),
            self._sp(4),
            Paragraph(
                "Le présent rapport d'expertise, en tout ou partie, ne pourra être cité ni même "
                "mentionné dans aucun document, aucune circulaire et aucune déclaration destinés à être "
                "publiés, ne pourra l'être d'une quelconque manière sans l'accord écrit de l'expert "
                "quant à la forme et aux circonstances dans lesquelles il pourra paraître.",
                self.S["j"]),
            self._sp(6),
            self.C.legal(
                f"Ce rapport est établi en deux exemplaires originaux. "
                f"Réf. dossier : {self.p.get('ref','')}  •  Expert : {CABINET['expert']}  •  "
                f"RCP : {CABINET['rcp']}"
            ),
            self._sp(8),
        )

    def _section_III_mission(self):
        p = self.p
        docs = p.get("documents_transmis", ["Titre de propriété"])
        docs_str = "\n".join(f"• {d}" for d in docs) if docs else "Titre de propriété"

        self._add(
            self.C.section("III  —  MISSION"),
            self._sp(6),
            Paragraph("1  —  Identité du demandeur", self.S["h2"]),
            self.C.kv([
                ("Demandeur",  p.get("demandeur_nom","")),
                ("Qualité",    p.get("demandeur_qualite","")),
                ("Adresse",    p.get("demandeur_adresse","")),
            ]),
            self._sp(4),
            Paragraph("2  —  Objet de la mission", self.S["h2"]),
            self.C.kv([
                ("Mission",     p.get("objet_mission","")),
                ("Bien",        f"{p.get('type_bien_label','')} — {p.get('adresse_bien','')}"),
                ("Hypothèse",   p.get("hypothese","")),
                ("Réserves",    p.get("reserves_initiales","Néant")),
            ]),
            self._sp(4),
            Paragraph("3  —  Visite et documents transmis", self.S["h2"]),
            self.C.kv([
                ("Date de visite",  p.get("date_visite","")),
                ("Présence",        p.get("accompagnateur", p.get("demandeur_nom",""))),
                ("Documents fournis", docs_str),
            ]),
            self.C.legal(
                f"Référence dossier : {p.get('ref','')}  •  "
                f"Date du rapport : {p.get('date_rapport','')}  •  "
                f"Méthodes : {self._label_methodes()}"
            ),
            self._sp(8),
        )

    def _label_methodes(self):
        t = self.p.get("type_bien","maison")
        if t == "appartement":
            return "Comparaison directe (DVF)"
        elif t == "terrain":
            return "Méthode terrain"
        else:
            methodes = ["Comparaison directe (DVF)", "Sol & Construction"]
            if self.p.get("vente_anterieure"):
                methodes.append("Actualisation par indice ICC")
            return " + ".join(methodes)

    def _section_IV_travaux(self):
        p = self.p
        # Construire le texte de situation géographique
        env_parts = []
        if p.get("env_distance_centre"):
            env_parts.append(f"Distance centre : {p['env_distance_centre']}.")
        if p.get("env_acces"):
            env_parts.append(f"Accès : {p['env_acces']}.")
        if p.get("env_transports"):
            env_parts.append(f"Transports : {p['env_transports']}.")
        if p.get("env_commerces"):
            env_parts.append(f"Commerces / services : {p['env_commerces']}.")
        env_text = " ".join(env_parts) or p.get("environnement_immediat","")

        # Marché local
        marche_text = ""
        if p.get("marche_tendance") or p.get("marche_tension"):
            marche_text = (
                f"Le marché immobilier local présente une tendance <b>{p.get('marche_tendance','Stable').lower()}</b> "
                f"avec une tension offre/demande <b>{p.get('marche_tension','équilibrée').lower()}</b> "
                f"au moment de l'expertise."
            )

        self._add(
            self.C.section("IV  —  TRAVAUX D'EXPERTISE"),
            self._sp(6),
            Paragraph("1  —  Situation géographique et marché", self.S["h2"]),
            Paragraph(p.get("situation_geographique",
                "Le bien immobilier se situe dans la commune de "
                f"{p.get('commune','')}, dans un secteur "
                f"{p.get('zone_urbanisme','urbanisé résidentiel')}. "
                f"{env_text}"), self.S["j"]),
        )
        if marche_text:
            self._add(self._sp(3), Paragraph(marche_text, self.S["j"]))
        self._add(
            self._sp(4),
            Paragraph("2  —  Situation juridique", self.S["h2"]),
            Paragraph("<b>Droit de propriété</b>", self.S["h3"]),
            Paragraph(p.get("origine_propriete",
                f"{p.get('demandeur_nom','')} est propriétaire du bien "
                "dont l'origine de propriété est précisée dans le titre transmis."),
                self.S["j"]),
            self._sp(4),
            Paragraph("<b>Données cadastrales et urbanisme</b>", self.S["h3"]),
            self.C.kv([
                ("Référence cadastrale", f"Section {p.get('cadastre_section','')} — N° {p.get('cadastre_num','')}"),
                ("Lieu-dit",             p.get("lieu_dit","")),
                ("Contenance",           f"{p.get('terrain_m2','')} m²"),
                ("Zonage PLU",           p.get("zonage_plu","")),
                ("Lot de copropriété",   p.get("lot_copro","—") if p.get("type_bien")=="appartement" else "—"),
                ("Millièmes",            p.get("millesimes","—") if p.get("type_bien")=="appartement" else "—"),
            ]),
            self._sp(6),
        )
        self._section_IV_description()
        self._section_IV_risques()

    # ─── TABLEAU VÉTUSTÉ DÉCOMPOSÉE ───────────────────────────────────────────
    def _vetuste_table(self, postes):
        """Renvoie un Table ReportLab avec le détail vétusté par poste."""
        header = [Paragraph(f"<b>{h}</b>", self.S["lbl"]) for h in
                  ["Poste", "% coût", "Âge eff.", "Durée vie", "Vét. poste", "Contrib."]]
        rows = [header]
        total_contrib = 0.0
        for p in postes:
            age  = float(p.get("age_effectif", 0) or 0)
            dv   = float(p.get("duree_vie", 1) or 1)
            pct  = float(p.get("pct_cout", 0) or 0)
            vet  = min(age / dv, 1.0)
            contrib = pct * vet
            total_contrib += contrib
            rows.append([
                Paragraph(p.get("poste", ""), self.S["sm"]),
                Paragraph(f"{pct:.0f} %", self.S["sm"]),
                Paragraph(f"{age:.0f} ans", self.S["sm"]),
                Paragraph(f"{dv:.0f} ans", self.S["sm"]),
                Paragraph(f"{vet*100:.0f} %", self.S["sm"]),
                Paragraph(f"{contrib:.1f} %", self.S["sm"]),
            ])
        rows.append([
            Paragraph("<b>VÉTUSTÉ GLOBALE PONDÉRÉE</b>", self.S["lbl"]),
            Paragraph("", self.S["sm"]),
            Paragraph("", self.S["sm"]),
            Paragraph("", self.S["sm"]),
            Paragraph("", self.S["sm"]),
            Paragraph(f"<b>{total_contrib:.1f} %</b>", self.S["lbl"]),
        ])
        widths = [6.5*cm, 1.5*cm, 1.8*cm, 2*cm, 1.8*cm, CW - 13.6*cm]
        t = Table(rows, colWidths=widths)
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0),  NAVY),
            ("TEXTCOLOR",     (0,0),(-1,0),  W),
            ("FONTSIZE",      (0,0),(-1,0),  8),
            ("ROWBACKGROUNDS",(0,1),(-1,-2), [W, LIGHT]),
            ("BACKGROUND",    (0,-1),(-1,-1),colors.HexColor("#EAF0E8")),
            ("LINEABOVE",     (0,-1),(-1,-1),2,GOLD),
            ("GRID",          (0,0),(-1,-1), 0.3, BORDER),
            ("TOPPADDING",    (0,0),(-1,-1), 3),
            ("BOTTOMPADDING", (0,0),(-1,-1), 3),
            ("LEFTPADDING",   (0,0),(-1,-1), 4),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ]))
        return t

    # ─── TABLEAU CARACTÉRISTIQUES PHYSIQUES ────────────────────────────────────
    def _carac_physiques_table(self, postes):
        header = [Paragraph(f"<b>{h}</b>", self.S["lbl"]) for h in
                  ["Poste", "État constaté", "Observations"]]
        rows = [header]
        for c in postes:
            rows.append([
                Paragraph(c.get("poste", ""), self.S["sm"]),
                Paragraph(c.get("etat", ""), self.S["sm"]),
                Paragraph(c.get("notes", ""), self.S["smm"]),
            ])
        widths = [4.5*cm, 3*cm, CW - 7.5*cm]
        t = Table(rows, colWidths=widths)
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0),  NAVY),
            ("TEXTCOLOR",     (0,0),(-1,0),  W),
            ("FONTSIZE",      (0,0),(-1,0),  8),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [W, LIGHT]),
            ("GRID",          (0,0),(-1,-1), 0.3, BORDER),
            ("TOPPADDING",    (0,0),(-1,-1), 3),
            ("BOTTOMPADDING", (0,0),(-1,-1), 3),
            ("LEFTPADDING",   (0,0),(-1,-1), 4),
            ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ]))
        return t

    # ─── EMBED PHOTOS ─────────────────────────────────────────────────────────
    def _embed_photos(self, photos):
        """Insère les photos 2 par ligne avec légende."""
        MAX_W = (CW - 0.5*cm) / 2
        MAX_H = MAX_W * 0.75  # ratio 4:3
        elements = []
        for i in range(0, len(photos), 2):
            pair = photos[i:i+2]
            img_cells = []
            cap_cells = []
            for photo in pair:
                data_url = photo.get("data","")
                caption  = photo.get("caption","") or photo.get("name","")
                try:
                    if "," in data_url:
                        raw = base64.b64decode(data_url.split(",",1)[1])
                    else:
                        raw = base64.b64decode(data_url)
                    buf = io.BytesIO(raw)
                    img = RLImage(buf, width=MAX_W, height=MAX_H)
                    img_cells.append(img)
                except Exception:
                    img_cells.append(Paragraph("[Photo indisponible]", self.S["smm"]))
                cap_cells.append(Paragraph(caption or "", self.S["smm"]))
            # Pad to 2 cols
            while len(img_cells) < 2:
                img_cells.append(Paragraph("", self.S["sm"]))
                cap_cells.append(Paragraph("", self.S["sm"]))
            t_imgs = Table([img_cells], colWidths=[MAX_W, MAX_W])
            t_imgs.setStyle(TableStyle([
                ("ALIGN",        (0,0),(-1,-1), "CENTER"),
                ("LEFTPADDING",  (0,0),(-1,-1), 4),
                ("RIGHTPADDING", (0,0),(-1,-1), 4),
                ("TOPPADDING",   (0,0),(-1,-1), 2),
            ]))
            t_caps = Table([cap_cells], colWidths=[MAX_W, MAX_W])
            t_caps.setStyle(TableStyle([
                ("ALIGN",       (0,0),(-1,-1), "CENTER"),
                ("FONTSIZE",    (0,0),(-1,-1), 8),
                ("TEXTCOLOR",   (0,0),(-1,-1), MUTED),
                ("TOPPADDING",  (0,0),(-1,-1), 2),
                ("BOTTOMPADDING",(0,0),(-1,-1), 6),
            ]))
            elements.append(t_imgs)
            elements.append(t_caps)
        return elements

    def _section_IV_description(self):
        p = self.p
        t = p.get("type_bien","maison")
        self._add(Paragraph("3  —  Description des biens", self.S["h2"]))

        if t == "maison":
            self._add(
                Paragraph(f"3-1  La {p.get('type_bien_label','maison')}", self.S["h3"]),
                Paragraph(p.get("description_construction",
                    f"Construction datant de {p.get('annee_construction','')}. "
                    f"État général : {p.get('etat_general','bon état')}. "
                    f"Surface de plancher (SDP) : {p.get('sdp','')} m²."),
                    self.S["j"]),
                self._sp(4),
                Paragraph("3-1-1  Disposition", self.S["h3"]),
            )
            distribution = p.get("distribution", [])
            if distribution:
                for item in distribution:
                    self._add(Paragraph(f"• {item}", self.S["n"]))
            self._add(self._sp(4))

            # Constructions secondaires
            for extra in p.get("constructions_secondaires", []):
                self._add(
                    Paragraph(f"3-{extra.get('num','X')}  {extra.get('titre','')}", self.S["h3"]),
                    Paragraph(extra.get("description",""), self.S["j"]),
                )
                for item in extra.get("distribution",[]):
                    self._add(Paragraph(f"• {item}", self.S["n"]))
                self._add(self._sp(4))

            # Terrain
            self._add(
                Paragraph("3-X  Le terrain d'assiette", self.S["h3"]),
                Paragraph(p.get("description_terrain",
                    f"Terrain d'une surface cadastrale de {p.get('terrain_m2','')} m². "
                    f"{p.get('terrain_notes','')}"), self.S["j"]),
                self._sp(4),
            )

        elif t == "appartement":
            self._add(
                Paragraph("3-1  L'appartement", self.S["h3"]),
                Paragraph(p.get("description_construction",
                    f"Appartement de type {p.get('type_appart','F3')} situé "
                    f"{p.get('niveau_etage','au')} du bâtiment "
                    f"{p.get('batiment','')}. "
                    f"État général : {p.get('etat_general','bon')}." ),
                    self.S["j"]),
                self._sp(4),
                Paragraph("3-1-1  Disposition", self.S["h3"]),
            )
            for item in p.get("distribution",[]):
                self._add(Paragraph(f"• {item}", self.S["n"]))
            if p.get("millesimes"):
                self._add(Paragraph(
                    f"Et les {p['millesimes']} des parties communes générales de l'immeuble.",
                    self.S["j"]))
            self._add(self._sp(4))

        elif t == "terrain":
            self._add(
                Paragraph("3-1  Le terrain", self.S["h3"]),
                Paragraph(p.get("description_terrain",
                    f"Terrain d'une surface de {p.get('terrain_m2','')} m². "
                    f"{p.get('terrain_notes','')}"), self.S["j"]),
                self._sp(4),
            )

        # Caractéristiques physiques par poste
        carac = p.get("carac_physiques")
        if carac and t != "terrain":
            self._add(
                self._sp(4),
                Paragraph("3-X  État des composants — Constat lors de la visite", self.S["h3"]),
                self._carac_physiques_table(carac),
                self._sp(4),
            )

        # Vétusté décomposée (maison uniquement)
        if t == "maison":
            postes_vet = p.get("vetuste_postes")
            if postes_vet and len(postes_vet) > 0:
                self._add(
                    Paragraph("3-X  Vétusté décomposée par poste (méthode pondérée)", self.S["h3"]),
                    self.C.legal(
                        "La vétusté est calculée poste par poste, pondérée par le "
                        "pourcentage de coût de chaque élément. La vétusté globale est la somme des contributions."
                    ),
                    self._sp(4),
                    self._vetuste_table(postes_vet),
                    self._sp(4),
                )

        # Note SDP obligatoire
        self._add(
            self.C.legal(
                "Surface de Plancher (SDP) — art. R. 111-22 Code de l'urbanisme "
                "(décret 2011-2054 du 29/12/2011, en vigueur depuis le 1ᵉʳ mars 2012). "
                "La SHOB et la SHON sont des notions abrogées et ne peuvent plus être utilisées."
            ),
            self._sp(8),
        )

    def _section_IV_risques(self):
        p = self.p
        self._add(Paragraph("4  —  Analyse qualitative et risques", self.S["h2"]))

        zone = p.get("zone_sismique","V")
        risques = [
            ["Amiante",
             "Diagnostic requis" if not p.get("diag_amiante") else p.get("resultat_amiante","Néant"),
             "Diagnostic à confier à un professionnel habilité." if not p.get("diag_amiante")
             else "Diagnostic fourni.",
             "CCH art. L. 271-4"],
            ["Termites",
             "Zone contaminée" if p.get("termites_zone",True) else "Hors zone",
             ("Diagnostic termites OBLIGATOIRE." if not p.get("diag_termites") else "Diagnostic fourni."),
             "Arrêté préfectoral Guadeloupe"],
            ["Sismicité",
             f"Zone {zone}",
             f"Zone {zone} — {'maximale (Guadeloupe)' if zone=='V' else 'forte'}. "
             "Conformité parasismique à vérifier pour les constructions antérieures à 2010.",
             "Décret 2010-1255"],
            ["Cyclones",
             "Zone exposée",
             "Territoire soumis au risque cyclonique — facteur intégré dans les prix de marché.",
             "PPRN applicable"],
            ["PPRN",
             "Applicable" if p.get("pprn",True) else "Non applicable",
             f"Plan de Prévention des Risques Naturels — commune de {p.get('commune','')}. "
             "Consulter le PPRN pour tout projet ou mise en conformité.",
             "Géorisques"],
        ]
        self._add(self.C.risque_table(risques), self._sp(8))

    # ─── SECTION V — ÉVALUATION ───────────────────────────────────────────────
    def _section_V_evaluation(self):
        t = self.p.get("type_bien","maison")
        self._add(
            self.C.section("V  —  ÉVALUATION"),
            self._sp(6),
            Paragraph(
                "Compte tenu des éléments d'information mis à notre disposition et de notre visite "
                "des lieux, nous retenons les méthodes de calcul suivantes :",
                self.S["j"]),
            self._sp(4),
        )

        if t == "maison":
            self._add(
                Paragraph("— Méthode 1 : Par comparaison directe (DVF)", self.S["n"]),
                Paragraph("— Méthode 2 : Par sol et construction", self.S["n"]),
            )
            if self.p.get("vente_anterieure"):
                self._add(Paragraph("— Méthode 3 : Par actualisation (indice ICC)", self.S["n"]))
            self._add(self._sp(8))
            v1 = self._methode_comparaison()
            v2 = self._methode_sol_construction()
            v3 = self._methode_actualisation() if self.p.get("vente_anterieure") else None
            self._synthese_methodes(v1, v2, v3)

        elif t == "appartement":
            self._add(
                Paragraph("— Méthode unique : Par comparaison directe (DVF)",  self.S["n"]),
                self._sp(4),
                self.C.legal(
                    "Pour un appartement en copropriété, la méthode par comparaison directe "
                    "est la seule méthode appropriée. La méthode par sol et construction s'applique "
                    "aux maisons individuelles. Aucun abattement de vétusté ne s'applique sur une "
                    "valeur obtenue par comparaison : la vétusté est intégrée dans les prix de marché."
                ),
                self._sp(8),
            )
            v1 = self._methode_comparaison()
            self._conclure_appart(v1)

        elif t == "terrain":
            self._add(self._sp(4))
            self._methode_terrain()

    def _methode_comparaison(self):
        p = self.p
        refs = p.get("dvf_refs", [])
        pm2_median = p.get("pm2_median", 0)

        self._add(
            Paragraph("5-1  Méthode par comparaison directe — Source DVF+", self.S["h2"]),
            Paragraph(
                f"Source : Base DVF+ open-data (DGFiP — data.gouv.fr). "
                f"Transactions retenues : {p.get('type_bien_label','bien similaire')} "
                f"— secteur {p.get('commune','')}{' et communes comparables' if p.get('communes_comparables') else ''}. "
                f"Période : {p.get('periode_dvf','24 mois glissants')}.",
                self.S["it"]),
            self._sp(4),
        )

        if refs:
            self._add(self.C.dvf_table(refs, pm2_median), self._sp(6))

        # Corrections
        corrections = p.get("corrections_comparaison", [])
        if corrections:
            self._add(Paragraph("Corrections appliquées :", self.S["h3"]))
            corr_data = [[Paragraph("<b>Critère</b>",self.S["lbl"]),
                          Paragraph("<b>Taux</b>",self.S["lbl"]),
                          Paragraph("<b>Justification</b>",self.S["lbl"])]]
            total_corr = 0
            for c in corrections:
                taux = c.get("taux",0)
                total_corr += taux
                sign = "+" if taux >= 0 else ""
                corr_data.append([
                    Paragraph(c.get("critere",""), self.S["sm"]),
                    Paragraph(f"{sign}{taux} %", self.S["sm"]),
                    Paragraph(c.get("justification",""), self.S["smm"]),
                ])
            pm2_corrige = round(pm2_median * (1 + total_corr/100))
            corr_data.append([
                Paragraph("<b>Prix corrigé retenu</b>", self.S["lbl"]),
                Paragraph(f"<b>{pm2_corrige:,}\u202f€/m²</b>".replace(",","\u202f"), self.S["lbl"]),
                Paragraph(f"Base {pm2_median:,} €/m² × correction nette {'+' if total_corr>=0 else ''}{total_corr} %".replace(",","\u202f"), self.S["smm"]),
            ])
            t_corr = Table(corr_data, colWidths=[5.5*cm, 2.5*cm, CW-8*cm])
            t_corr.setStyle(TableStyle([
                ("BACKGROUND",   (0,0),(-1,0),  NAVY),("TEXTCOLOR",(0,0),(-1,0),W),("FONTSIZE",(0,0),(-1,0),8),
                ("ROWBACKGROUNDS",(0,1),(-1,-2),[W,LIGHT]),
                ("BACKGROUND",   (0,-1),(-1,-1),colors.HexColor("#EAF0E8")),
                ("LINEABOVE",    (0,-1),(-1,-1),1.5,GOLD),
                ("GRID",         (0,0),(-1,-1),0.3,BORDER),
                ("TOPPADDING",   (0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
                ("LEFTPADDING",  (0,0),(-1,-1),5),("VALIGN",(0,0),(-1,-1),"TOP"),
            ]))
            self._add(t_corr, self._sp(4))
        else:
            pm2_corrige = pm2_median

        sdp = float(p.get("sdp",0) or 0)
        val_comp = round(sdp * pm2_corrige / 1000) * 1000 if sdp else 0

        self._add(
            self.C.kv([
                ("SDP retenue",         f"{sdp} m²"),
                ("Prix corrigé /m²",    f"{pm2_corrige:,}\u202f€/m²".replace(",","\u202f")),
                ("<b>Valeur méthode 1</b>", f"<b>{self._fmt(val_comp)}</b>"),
            ]),
            self._sp(8),
        )
        return val_comp

    def _methode_sol_construction(self):
        p = self.p
        self._add(Paragraph("5-2  Méthode par sol et construction", self.S["h2"]))

        # Terrain
        terrain_m2   = float(p.get("terrain_m2",0) or 0)
        prix_m2_brut = float(p.get("prix_terrain_brut",120) or 120)
        decote_occu  = float(p.get("decote_occupation",20) or 20) / 100
        vt_brut      = terrain_m2 * prix_m2_brut
        vt_nette     = round(vt_brut * (1 - decote_occu))

        self._add(
            Paragraph("<b>1) Valeur du terrain</b>", self.S["h3"]),
            self.C.kv([
                ("Surface cadastrale",    f"{terrain_m2:.0f} m²"),
                ("Prix brut /m²",         f"{prix_m2_brut:.0f} €/m²"),
                ("Valeur brute",          self._fmt(vt_brut)),
                (f"Décote terrain occupé ({decote_occu*100:.0f} %)", f"− {self._fmt(vt_brut*decote_occu)}"),
                ("<b>Valeur terrain (VT)</b>", f"<b>{self._fmt(vt_nette)}</b>"),
            ]),
            self._sp(6),
        )

        # Construction
        sdp          = float(p.get("sdp",0) or 0)
        cout_m2      = float(p.get("cout_construction_m2", 1450) or 1450)
        vetuste      = float(p.get("vetuste_taux",20) or 20) / 100
        vc_neuf      = sdp * cout_m2
        vc_nette     = round(vc_neuf * (1 - vetuste))

        self._add(
            Paragraph("<b>2) Valeur de la construction</b>", self.S["h3"]),
            self.C.kv([
                ("Surface de plancher (SDP)",         f"{sdp:.0f} m²"),
                ("Coût de reconstruction au m² SDP",  f"{cout_m2:.0f} €/m²  (indice BT01 Guadeloupe — 2026)"),
                ("Valeur à neuf",                     self._fmt(vc_neuf)),
                (f"Vétusté pondérée ({vetuste*100:.0f} %)", f"− {self._fmt(vc_neuf*vetuste)}"),
                (f"Justification vétusté",            p.get("justification_vetuste",
                    f"Bâtiment de {datetime.date.today().year - int(p.get('annee_construction',2000) or 2000)} ans — vétusté pondérée par poste")),
                ("<b>Valeur construction (VC)</b>",   f"<b>{self._fmt(vc_nette)}</b>"),
            ]),
            self._sp(6),
        )

        val_sc = round((vt_nette + vc_nette) / 1000) * 1000
        self._add(
            self.C.kv([
                ("VT (terrain)",           self._fmt(vt_nette)),
                ("VC (construction)",      self._fmt(vc_nette)),
                ("<b>Valeur méthode 2</b>", f"<b>{self._fmt(val_sc)}</b>"),
            ]),
            self.C.legal(
                "Note : le coût de 1 450 €/m² est calculé sur la Surface de Plancher (SDP) "
                "conformément à l'art. R. 111-22 du Code de l'urbanisme. "
                "La SHOB (Surface Hors Œuvre Brute) est une notion abrogée depuis mars 2012."
            ),
            self._sp(8),
        )
        return val_sc

    def _methode_actualisation(self):
        p = self.p
        va = p.get("vente_anterieure", {})
        prix_base = float(va.get("prix",0) or 0)
        indice_b  = float(va.get("indice_base",1671) or 1671)
        indice_r  = float(va.get("indice_revision",2146) or 2146)
        val_act   = round(prix_base * indice_r / indice_b / 1000) * 1000

        self._add(
            Paragraph("5-3  Méthode par actualisation — Indice ICC", self.S["h2"]),
            Paragraph(
                f"Le présent bien a fait l'objet d'une vente le {va.get('date','')} "
                f"pour un montant de {self._fmt(prix_base)} net vendeur. "
                "L'actualisation s'effectue selon l'indice du coût de la construction (ICC — INSEE).",
                self.S["j"]),
            self._sp(4),
            self.C.kv([
                ("Date de la vente antérieure", va.get("date","")),
                ("Prix de référence",           self._fmt(prix_base)),
                ("Indice base (ICC)",           f"{indice_b:.0f}  —  {va.get('trimestre_base','')}"),
                ("Indice révision (ICC)",       f"{indice_r:.0f}  —  {va.get('trimestre_revision','')}"),
                ("Formule",                     f"{prix_base:.0f} × {indice_r:.0f} / {indice_b:.0f}"),
                ("<b>Valeur actualisée</b>",    f"<b>{self._fmt(val_act)}</b>"),
            ]),
            self._sp(8),
        )
        return val_act

    def _methode_terrain(self):
        p = self.p
        terrain_m2  = float(p.get("terrain_m2",0) or 0)
        prix_m2     = float(p.get("prix_terrain_brut",50) or 50)
        val_terrain = round(terrain_m2 * prix_m2 / 1000) * 1000
        self._add(
            Paragraph("5-1  Évaluation du terrain", self.S["h2"]),
            self.C.kv([
                ("Surface cadastrale",    f"{terrain_m2:.0f} m²"),
                ("Prix unitaire retenu",  f"{prix_m2:.0f} €/m²"),
                ("<b>Valeur terrain</b>", f"<b>{self._fmt(val_terrain)}</b>"),
            ]),
            self._sp(6),
        )
        val_ret = val_terrain
        self._add(self.C.conclusion_box(
            round(val_ret*0.93/1000)*1000, val_ret, round(val_ret*1.05/1000)*1000))
        return val_ret

    def _synthese_methodes(self, v1, v2, v3=None):
        p = self.p
        methodes = []
        poids = []
        if v1:
            methodes.append(("M1 — Comparaison directe DVF", v1,
                             p.get("poids_comparaison",45)))
        if v2:
            methodes.append(("M2 — Sol & Construction", v2,
                             p.get("poids_sol_construction",35)))
        if v3:
            methodes.append(("M3 — Actualisation ICC", v3,
                             p.get("poids_actualisation",20)))

        total_poids = sum(m[2] for m in methodes) or 100
        val_pond = sum(m[1] * m[2] / total_poids for m in methodes)
        val_ret  = round(val_pond / 1000) * 1000

        # Décote SCI éventuelle
        decote_sci = p.get("decote_sci",0)
        if decote_sci:
            val_avant = val_ret
            val_ret   = round(val_ret * (1 - decote_sci/100) / 1000) * 1000
            self._add(
                self.C.reserve(
                    f"SCI — Décote de {decote_sci} % appliquée pour illiquidité des parts "
                    f"({self._fmt(val_avant)} × {100-decote_sci} % = {self._fmt(val_ret)}). "
                    "Fondée sur la doctrine BOFiP (IS - BIC Immobilier).",
                    couleur=ORANGE, bg="#FFF3E6"))

        val_min = round(val_ret * 0.93 / 1000) * 1000
        val_max = round(val_ret * 1.05 / 1000) * 1000

        rows = [[m[0], self._fmt(m[1]), f"{m[2]} %",
                 self._fmt(m[1]*m[2]/total_poids)] for m in methodes]
        rows.append(["<b>VALEUR RETENUE</b>", f"<b>{self._fmt(val_ret)}</b>",
                     "100 %", f"<b>{self._fmt(val_ret)}</b>"])

        self._add(
            Paragraph("5-X  Synthèse — Pondération des méthodes", self.S["h2"]),
            self.C.synth_table(rows),
            self._sp(10),
            self.C.conclusion_box(val_min, val_ret, val_max),
            self._sp(8),
        )
        return val_ret

    def _conclure_appart(self, val):
        val_min = round(val * 0.93 / 1000) * 1000
        val_max = round(val * 1.05 / 1000) * 1000
        self._add(self.C.conclusion_box(val_min, val, val_max), self._sp(8))
        return val

    # ─── SECTION VI — CONCLUSIONS ─────────────────────────────────────────────
    def _section_VI_conclusions(self):
        p = self.p
        self._add(
            self.C.section("VI  —  CONCLUSIONS"),
            self._sp(10),
            Paragraph(self._build_conclusion_text(), self.S["j"]),
            self._sp(6),
            Paragraph(
                "Les chiffres ci-dessus sont donnés hors fiscalité et hors frais d'acte.",
                self.S["it"]),
            self._sp(6),
        )

        # Valeur locative et taux de capitalisation
        val_loc = float(p.get("valeur_locative_mensuelle") or 0)
        val_retenue_txt = p.get("valeur_retenue_texte","")
        # Essayer d'extraire une valeur numérique pour le taux capi
        import re
        val_num = 0
        if val_retenue_txt:
            m = re.search(r"([\d\s ]+)", val_retenue_txt.replace(",",""))
            if m:
                try:
                    val_num = float(m.group(1).replace(" ","").replace(" ",""))
                except ValueError:
                    pass
        if val_loc > 0 and val_num > 0:
            taux_capi = val_loc * 12 / val_num * 100
            self._add(
                Paragraph("Valeur locative de marché", self.S["h3"]),
                self.C.kv([
                    ("Loyer mensuel de marché estimé",   f"{val_loc:,.0f} € / mois (charges non comprises)".replace(","," ")),
                    ("Revenu locatif annuel estimé",      f"{val_loc*12:,.0f} € / an".replace(","," ")),
                    ("Taux de capitalisation brut",       f"{taux_capi:.1f} %  (Marché Guadeloupe : 5–8 % brut typique)"),
                ]),
                self._sp(4),
            )

        # Valeur de liquidation rapide
        decote_liq = float(p.get("decote_liquidation") or 15)
        if val_num > 0 and decote_liq > 0:
            val_liq = round(val_num * (1 - decote_liq/100) / 1000) * 1000
            self._add(
                Paragraph("Valeur de liquidation rapide", self.S["h3"]),
                Paragraph(
                    f"Dans l'hypothèse d'une cession rapide (délai réduit — vente contrainte), "
                    f"une décote de {decote_liq:.0f} % est usuellement retenue sur le marché guadeloupéen.",
                    self.S["j"]),
                self.C.kv([
                    ("Valeur vénale",         self._fmt(val_num)),
                    (f"Décote liquidation ({decote_liq:.0f} %)", f"− {self._fmt(val_num*decote_liq/100)}"),
                    ("<b>Valeur de liquidation rapide</b>", f"<b>{self._fmt(val_liq)}</b>"),
                ]),
                self._sp(6),
            )

        # Durée de validité
        duree = p.get("duree_validite","6 mois à compter de la date du rapport")
        self._add(
            self.C.legal(f"Durée de validité du présent rapport : {duree}."),
            self._sp(4),
        )

        # Réserves finales
        if self._reserves:
            self._add(Paragraph("Réserves émises :", self.S["h3"]))
            for r, niveau in self._reserves:
                col = ALERT if niveau=="alerte" else NAVY
                self._add(self.C.reserve(r, couleur=col))
            self._add(self._sp(6))

        self._add(
            Paragraph(
                "Arrêté le présent rapport d'expertise pour servir et valoir ce que de droit. "
                "Il a été établi en deux exemplaires originaux.",
                self.S["j"]),
            self._sp(16),
            self.C.kv([
                ("Lieu et date",    f"Les Abymes (Guadeloupe), le {p.get('date_rapport','')}"),
                ("Expert",          f"{CABINET['expert']} — {CABINET['titre']}"),
                ("Cabinet",         f"{CABINET['nom']}  |  {CABINET['adresse']}"),
                ("Qualifications",  f"{CABINET['rc']}  •  SIRET {CABINET['siret']}  •  RCP : {CABINET['rcp']}"),
            ]),
            self._sp(16),
            Paragraph("____________________________________",
                       ParagraphStyle("s1",fontName="Helvetica",fontSize=10,
                                      alignment=TA_RIGHT,textColor=MUTED)),
            Paragraph("Signature et cachet de l'expert",
                       ParagraphStyle("s2",fontName="Helvetica",fontSize=8,
                                      alignment=TA_RIGHT,textColor=MUTED)),
            self._sp(10),
            self.C.legal(CABINET["refs_legales"]),
        )

    # ─── SECTION VII — ANNEXES ────────────────────────────────────────────────

    def _build_conclusion_text(self):
        p = self.p
        sdp_part = f" — SDP {p['sdp']} m²" if p.get("sdp") else ""
        terrain_part = f" — terrain {p['terrain_m2']} m²" if p.get("terrain_m2") else ""
        return (
            f"Nous évaluons en définitive le bien immobilier situé "
            f"<b>{p.get('adresse_bien','')}, {p.get('commune','')} "
            f"({p.get('code_postal','')})</b> "
            f"({p.get('type_bien_label','')}{sdp_part}{terrain_part}), "
            f"en valeur vénale et en pleine propriété, "
            f"à la somme de <b>{p.get('valeur_retenue_texte','…')}.</b>"
        )

    def _section_VII_annexes(self):
        p = self.p
        annexes = p.get("annexes", [
            "Titre de propriété",
            "Extrait du plan cadastral",
            "État des risques naturels et technologiques (ERP)",
            "Arrêté Préfectoral termites",
        ])
        self._add(
            self.C.section("VII  —  ANNEXES"),
            self._sp(6),
            Paragraph("A — Reportage photographique", self.S["h2"]),
        )
        photos = p.get("photos")
        if photos and len(photos) > 0:
            self._add(
                Paragraph(
                    f"Visite du {p.get('date_visite','')} — "
                    f"{len(photos)} photographie(s) jointe(s).",
                    self.S["it"]),
                self._sp(4),
            )
            for elem in self._embed_photos(photos):
                self._add(elem)
        else:
            self._add(Paragraph(
                "Aucune photographie transmise dans le présent dossier.",
                self.S["it"]))
        self._add(
            self._sp(6),
            Paragraph("B — Documents exploités", self.S["h2"]),
        )
        for i, a in enumerate(annexes, 1):
            self._add(Paragraph(f"{i}.  {a}", self.S["n"]))
        self._add(self._sp(8))

    # ═════════════════════════════════════════════════════════════════════════
    # GÉNÉRATION
    # ═════════════════════════════════════════════════════════════════════════
    def generer(self, output_path: str) -> str:
        """
        Génère le rapport PDF.
        Retourne le chemin du fichier produit.
        """
        self._collecter_reserves()
        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            leftMargin=ML, rightMargin=MR,
            topMargin=MT_TOP, bottomMargin=MB_BOT)

        # Page de couverture
        self.story.append(PageBreak())

        # Corps du rapport
        self._section_I_serment()
        self._section_II_clause()
        self._section_III_mission()
        self._section_IV_travaux()
        self._section_V_evaluation()
        self._section_VI_conclusions()
        self._section_VII_annexes()

        doc.build(
            self.story,
            onFirstPage=_cover_callback(self.p),
            onLaterPages=_header_footer_callback(self.p))

        print(f"✓  Rapport généré : {output_path}")
        return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# EXEMPLES DE PARAMÈTRES
# ═══════════════════════════════════════════════════════════════════════════════

EXEMPLE_MAISON = {
    # ── MISSION ──
    "ref"              : "SAGETRIM-2026-003",
    "demandeur_nom"    : "M. et Mme VINGADASSALOM Raymond et Louisette",
    "demandeur_qualite": "Particuliers",
    "demandeur_adresse": "96 Rue Siméon Pioche — 97130 Capesterre-Belle-Eau",
    "objet_mission"    : "Estimation en valeur vénale d'une maison individuelle",
    "date_visite"      : "13 février 2026",
    "date_rapport"     : "05 mars 2026",
    "accompagnateur"   : "M. et Mme VINGADASSALOM",
    "documents_transmis": ["Titre de propriété (donation-partage 2015)", "Plan cadastral"],

    # ── BIEN ──
    "type_bien"        : "maison",
    "adresse_bien"     : "96 Rue Siméon Pioche — Lieu-dit Les Sources Pérou",
    "commune"          : "CAPESTERRE-BELLE-EAU",
    "code_postal"      : "97130",
    "lieu_dit"         : "Les Sources Pérou",
    "cadastre_section" : "AO",
    "cadastre_num"     : "142",
    "terrain_m2"       : 290,
    "zonage_plu"       : "Zone UB — Résidentielle périphérique (PLU CBE, révision juin 2018)",
    "assainissement"   : "Collectif",

    # ── DESCRIPTION ──
    "annee_construction": 1967,
    "sdp"              : 195,
    "description_construction":
        "Maison individuelle R+1, datant de 1967, ayant fait l'objet d'une réhabilitation "
        "complète et d'un aménagement d'étage avec toiture en tôles ondulées réalisé en 2018. "
        "Construction sur fondations béton armé. Façade sur rue d'environ 7,50 m linéaires.",
    "distribution"     : [
        "RDC : Cuisine — Séjour — Salle à manger — 2 chambres (dont 1 avec salle d'eau)",
        "RDC : Salle d'eau — WC — Grande terrasse couverte — Couloir traversant",
        "Étage (2018) : Séjour — Cuisine ouverte — 2 chambres avec placards — Salle d'eau — WC",
    ],
    "description_terrain":
        "Terrain de 290 m², forme rectangulaire, plat. Portail métallique automatisé. "
        "Allée bétonnée carrelée en pierre de Bavière. Clôture périphérique complète. "
        "Jardin soigneusement entretenu.",
    "etat_general"     : "Bon — réhabilitation partielle 2018",

    # ── RISQUES ──
    "zone_sismique"    : "V",
    "termites_zone"    : True,
    "pprn"             : True,
    "diag_amiante"     : False,
    "diag_termites"    : False,
    "diag_elec"        : False,
    "diag_dpe"         : False,

    # ── ÉVALUATION ──
    "dvf_refs" : [
        {"date":"13/06/2022","localisation":"Capesterre — secteur similaire","type":"Maison R+1","surface":179,"valeur":210000,"pm2":1173,"retenu":True,"statut":"Référence principale"},
        {"date":"25/07/2024","localisation":"Capesterre — Les Sources","type":"Maison R+1","surface":180,"valeur":212000,"pm2":1178,"retenu":True,"statut":"Retenue"},
        {"date":"04/12/2023","localisation":"Gourbeyre","type":"Maison R+1","surface":200,"valeur":235000,"pm2":1175,"retenu":True,"statut":"Retenue"},
        {"date":"31/07/2023","localisation":"Capesterre — Pérou","type":"Maison R+1","surface":195,"valeur":205000,"pm2":1051,"retenu":True,"statut":"Retenue"},
    ],
    "pm2_median"       : 1176,
    "corrections_comparaison": [],
    "periode_dvf"      : "24 mois glissants",

    "prix_terrain_brut"        : 105,
    "decote_occupation"        : 20,
    "cout_construction_m2"     : 1450,
    "vetuste_taux"             : 13.8,
    "justification_vetuste"    : "Vétusté pondérée par poste (structure 10%, toiture 8%, menuiseries 15%, électricité 25%, plomberie 20%, finitions 10%, climatisation 15%)",

    "vente_anterieure" : None,   # Pas de vente antérieure dans ce dossier

    "poids_comparaison"        : 55,
    "poids_sol_construction"   : 45,

    # ── CONCLUSION ──
    "valeur_retenue_texte": "258\u202f000 € (deux cent cinquante-huit mille euros)",
}


EXEMPLE_APPART = {
    "ref"              : "SAGETRIM-2026-004",
    "demandeur_nom"    : "Madame Jovita Marie LAMBY épouse DOLMARE",
    "demandeur_qualite": "Cadre Hospitalier — Particulière",
    "demandeur_adresse": "20 Bis chemin Ffrench, Prise d'eau — 97170 Petit-Bourg",
    "objet_mission"    : "Estimation en valeur vénale d'un appartement en copropriété",
    "date_visite"      : "À préciser",
    "date_rapport"     : "24 mai 2026",
    "documents_transmis": ["Attestation de vente notariale (Me PREVALET, 30/05/2023)"],

    "type_bien"        : "appartement",
    "adresse_bien"     : "Résidence Anquetil III — Bâtiment NS3 — Escalier 1",
    "commune"          : "LES ABYMES",
    "code_postal"      : "97139",
    "lieu_dit"         : "Anquetil",
    "cadastre_section" : "CO",
    "cadastre_num"     : "20",
    "terrain_m2"       : None,
    "lot_copro"        : "59",
    "millesimes"       : "662/100\u202f000 des parties communes générales",
    "zonage_plu"       : "Zone UA — Urbaine dense (PLU Les Abymes)",
    "assainissement"   : "Collectif",

    "annee_construction": 1980,
    "sdp"              : 40,
    "type_appart"      : "F3",
    "batiment"         : "NS3",
    "niveau_etage"     : "au 4ᵉ étage (porte de gauche, escalier 1)",
    "description_construction":
        "Appartement de type F3 situé au 4ᵉ étage d'un immeuble R+4 sans ascenseur, "
        "construit depuis plus de quarante ans. Appartement très bien entretenu. "
        "Parties communes en état de dégradation avancée.",
    "distribution"     : [
        "1 entrée","1 salle de séjour","2 chambres","1 cuisine",
        "1 dégagement","1 salle d'eau aménagée","1 WC indépendant","2 loggias","1 placard",
    ],
    "etat_general"     : "Très bon — irréprochable",

    "zone_sismique"    : "V",
    "termites_zone"    : True,
    "pprn"             : True,
    "diag_amiante"     : False,
    "diag_termites"    : False,
    "diag_elec"        : False,
    "diag_dpe"         : False,

    "dvf_refs": [
        {"date":"13/06/2022","localisation":"Anquetil 2","type":"T3","surface":79,"valeur":92900,"pm2":1176,"retenu":True,"statut":"Référence principale — T3 / secteur identique"},
        {"date":"31/07/2023","localisation":"Anquetil 2","type":"T4","surface":81,"valeur":142500,"pm2":1759,"retenu":True,"statut":"Retenue"},
        {"date":"30/05/2023","localisation":"Anquetil 3","type":"T4","surface":80,"valeur":85000,"pm2":1063,"retenu":True,"statut":"Retenue"},
        {"date":"31/08/2023","localisation":"Anquetil 3","type":"T4","surface":80,"valeur":126000,"pm2":1575,"retenu":True,"statut":"Retenue"},
        {"date":"09/10/2024","localisation":"Anquetil 3","type":"T4","surface":56,"valeur":145000,"pm2":2589,"retenu":False,"statut":"Écartée — anomalie de prix"},
        {"date":"31/03/2025","localisation":"Anquetil 3","type":"T5","surface":86,"valeur":65000,"pm2":756,"retenu":False,"statut":"Écartée — valeur atypique"},
    ],
    "pm2_median"       : 1176,
    "corrections_comparaison": [
        {"critere":"4ᵉ étage sans ascenseur","taux":-10,"justification":"Standard marché : −8 à −12 %"},
        {"critere":"Parties communes dégradées","taux":-5,"justification":"Constaté lors de la visite"},
        {"critere":"Très bon état intérieur","taux":3,"justification":"Appartement irréprochable"},
    ],
    "periode_dvf"      : "36 mois glissants",

    "valeur_retenue_texte": "42\u202f000 € (quarante-deux mille euros)",
}


# ═══════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import os
    os.makedirs("/mnt/user-data/outputs", exist_ok=True)

    print("Génération rapport MAISON…")
    RapportExpertise(EXEMPLE_MAISON).generer(
        "/mnt/user-data/outputs/template_rapport_maison.pdf")

    print("Génération rapport APPARTEMENT…")
    RapportExpertise(EXEMPLE_APPART).generer(
        "/mnt/user-data/outputs/template_rapport_appart.pdf")

    print("\nTerminé.")
