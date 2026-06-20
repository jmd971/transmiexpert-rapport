import { useState, useCallback, useRef } from 'react'
import Head from 'next/head'

// ─── Configuration des étapes ────────────────────────────────────────────────
const STEPS = [
  { id: 'mission',     icon: '📋', title: 'Mission',        sub: 'Demandeur et dates' },
  { id: 'bien',        icon: '🏠', title: 'Identification',  sub: 'Adresse et cadastre' },
  { id: 'description', icon: '📐', title: 'Description',    sub: 'Surfaces et vétusté' },
  { id: 'photos',      icon: '📷', title: 'Photos',         sub: 'Reportage de visite' },
  { id: 'risques',     icon: '⚠️',  title: 'Risques',        sub: 'Naturels et diagnostics' },
  { id: 'evaluation',  icon: '📊', title: 'Évaluation',     sub: 'DVF et calcul de valeur' },
  { id: 'generation',  icon: '✅', title: 'Génération',     sub: 'Vérification et Word' },
]

// ─── Vétusté standard Guadeloupe ─────────────────────────────────────────────
const VETUSTE_POSTES_DEFAUT = [
  { poste: 'Structure (fondations, poteaux, plancher)', pct_cout: 30, duree_vie: 80 },
  { poste: 'Toiture (charpente + couverture)',          pct_cout: 15, duree_vie: 25 },
  { poste: 'Menuiseries (portes, fenêtres, volets)',    pct_cout: 10, duree_vie: 30 },
  { poste: 'Électricité',                               pct_cout: 12, duree_vie: 25 },
  { poste: 'Plomberie / sanitaires',                    pct_cout: 10, duree_vie: 30 },
  { poste: 'Finitions (carrelage, peinture, enduits)',  pct_cout: 13, duree_vie: 20 },
  { poste: 'Climatisation / VMC',                       pct_cout: 10, duree_vie: 15 },
]

function initVetustePostes(annee) {
  const age = annee ? Math.max(0, new Date().getFullYear() - parseInt(annee)) : 0
  return VETUSTE_POSTES_DEFAUT.map(p => ({ ...p, age_effectif: age }))
}

// ─── État initial ─────────────────────────────────────────────────────────────
const initialData = {
  // Mission
  ref: 'SAGETRIM-2026-',
  demandeur_nom: '',
  demandeur_qualite: '',
  demandeur_adresse: '',
  date_visite: '',
  date_rapport: new Date().toISOString().substring(0, 10),
  objet_mission: 'Estimation en valeur vénale — pleine propriété',

  // Bien
  type_bien: 'maison',
  adresse_bien: '',
  commune: '',
  code_postal: '',
  lieu_dit: '',
  cadastre_section: '',
  cadastre_num: '',
  terrain_m2: '',
  lot_copro: '',
  millesimes: '',
  zonage_plu: '',
  assainissement: 'Collectif',

  // Urbanisme & situation juridique
  constructibilite: '',
  dpu: 'À vérifier',
  servitudes: '',
  mitoyennete: '',
  situation_occupation: 'Libre de toute occupation',
  bail_details: '',
  origine_nature: 'Acquisition à titre onéreux',
  origine_date_acquisition: '',
  origine_prix_acquisition: '',
  origine_notaire: '',
  origine_indice_icc: '',
  origine_indice_icc_actuel: '',

  // Surfaces complémentaires
  surface_habitable: '',
  surface_carrez: '',

  // Environnement & marché
  env_distance_centre: '',
  env_acces: '',
  env_transports: '',
  env_commerces: '',
  marche_tendance: 'Stable',
  marche_tension: 'Équilibrée',

  // Description
  sdp: '',
  annee_construction: '',
  niveau_etage: '',
  ascenseur: false,
  type_appart: 'F3',
  batiment: '',
  etat_general: "Bon état d'usage",
  etat_communs: 'Bon',
  distribution: ['', '', '', '', ''],

  // Caractéristiques physiques par poste
  carac_physiques: [
    { poste: 'Structure / Fondations',     etat: 'Bon', notes: '' },
    { poste: 'Toiture (couverture)',        etat: 'Bon', notes: '' },
    { poste: 'Menuiseries extérieures',     etat: 'Bon', notes: '' },
    { poste: 'Installations électriques',   etat: 'Bon', notes: '' },
    { poste: 'Plomberie / sanitaires',      etat: 'Bon', notes: '' },
    { poste: 'Revêtements / finitions',     etat: 'Bon', notes: '' },
    { poste: 'Climatisation / ventilation', etat: 'Bon', notes: '' },
  ],

  // Vétusté décomposée
  vetuste_postes: [],

  // Photos
  photos: [],

  // Risques
  zone_sismique: 'V',
  termites_zone: true,
  pprn: true,
  diag_amiante: false,
  diag_termites: false,
  diag_elec: false,
  diag_dpe: false,

  // Évaluation
  dvf_refs: [
    { date:'', localisation:'', type:'', surface:'', valeur:'', pm2:'', retenu:true, statut:'Retenue' },
  ],
  pm2_median: '',
  corrections_comparaison: [],
  periode_dvf: '24 mois glissants',
  prix_terrain_brut: 120,
  decote_occupation: 20,
  cout_construction_m2: 1450,
  vetuste_taux: 20,
  vente_anterieure: null,
  poids_comparaison: 55,
  poids_sol_construction: 45,
  valeur_locative_mensuelle: '',

  // Conclusion
  duree_validite: '6 mois à compter de la date du rapport',
  decote_liquidation: 15,
  valeur_retenue_texte: '',
}

// ─── Composants UI ────────────────────────────────────────────────────────────
function Field({ label, children, hint, required }) {
  return (
    <div className="field">
      <label className="label">{label}{required && <span className="req">*</span>}</label>
      {children}
      {hint && <div className="hint">{hint}</div>}
    </div>
  )
}

function Toggle({ label, sub, checked, onChange }) {
  return (
    <div className="toggle-row">
      <div>
        <div className="toggle-label">{label}</div>
        {sub && <div className="toggle-sub">{sub}</div>}
      </div>
      <label className="switch">
        <input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)} />
        <span className="slider-sw" />
      </label>
    </div>
  )
}

function Alert({ type = 'info', children }) {
  return <div className={`alert alert-${type}`}><span>{children}</span></div>
}

// ─── Composant principal ──────────────────────────────────────────────────────
export default function ExpertForm() {
  const [step, setStep] = useState(0)
  const [data, setData] = useState(initialData)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  const set = useCallback((key, value) => {
    setData(prev => ({ ...prev, [key]: value }))
  }, [])

  const setNested = useCallback((key, index, field, value) => {
    setData(prev => {
      const arr = [...(prev[key] || [])]
      arr[index] = { ...arr[index], [field]: value }
      return { ...prev, [key]: arr }
    })
  }, [])

  const nav = (dir) => {
    const next = step + dir
    if (next >= 0 && next < STEPS.length) {
      setStep(next)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  const computeValue = () => {
    const retained = data.dvf_refs.filter(r => r.retenu && r.pm2)
    const pm2s = retained.map(r => parseFloat(r.pm2)).filter(v => v > 0).sort((a,b) => a-b)
    const median = pm2s.length ? pm2s[Math.floor(pm2s.length/2)] : parseFloat(data.pm2_median) || 0
    const sdp = parseFloat(data.sdp) || 0
    return sdp && median ? Math.round(sdp * median / 1000) * 1000 : 0
  }

  const generer = async () => {
    setLoading(true)
    setError(null)
    setSuccess(false)

    const valeur = computeValue()

    // Vétusté globale depuis le tableau décomposé
    const postes = data.vetuste_postes || []
    const vetusteGlobale = postes.length
      ? postes.reduce((acc, p) => {
          const v = Math.min(parseFloat(p.age_effectif||0) / (parseFloat(p.duree_vie||1)||1), 1)
          return acc + parseFloat(p.pct_cout||0) * v
        }, 0)
      : parseFloat(data.vetuste_taux) || 20

    const params = {
      ...data,
      valeur_retenue_texte: data.valeur_retenue_texte ||
        (valeur ? `${valeur.toLocaleString('fr-FR')} €` : ''),
      distribution: data.distribution.filter(Boolean),
      dvf_refs: data.dvf_refs.filter(r => r.date || r.localisation).map(r => ({
        ...r,
        surface: parseFloat(r.surface) || 0,
        valeur:  parseFloat(r.valeur)  || 0,
        pm2:     parseFloat(r.pm2)     || 0,
      })),
      pm2_median:    parseFloat(data.pm2_median) || 0,
      terrain_m2:    parseFloat(data.terrain_m2) || 0,
      sdp:           parseFloat(data.sdp)        || 0,
      vetuste_taux:  parseFloat(vetusteGlobale.toFixed(1)),
      vetuste_postes: postes.map(p => ({
        ...p,
        age_effectif: parseFloat(p.age_effectif) || 0,
        duree_vie:    parseFloat(p.duree_vie)    || 1,
        pct_cout:     parseFloat(p.pct_cout)     || 0,
      })),
    }

    try {
      // Construire FormData avec paramètres JSON + fichiers photos en binaire
      const formData = new FormData()
      formData.append('data', JSON.stringify(params))

      // Convertir les photos (dataURL → Blob) et les ajouter à FormData
      if (data.photos && data.photos.length > 0) {
        for (let i = 0; i < data.photos.length; i++) {
          const photo = data.photos[i]
          // Convertir dataURL en Blob
          const [header, base64] = photo.data.split(',')
          const mimeMatch = header.match(/:(.*?);/)
          const mime = mimeMatch ? mimeMatch[1] : 'image/jpeg'
          const binary = atob(base64)
          const bytes = new Uint8Array(binary.length)
          for (let j = 0; j < binary.length; j++) bytes[j] = binary.charCodeAt(j)
          const blob = new Blob([bytes], { type: mime })
          formData.append(`photo_${i}`, blob, photo.name)
          formData.append(`photo_${i}_caption`, photo.caption || '')
        }
      }

      const res = await fetch('/api/generer', {
        method: 'POST',
        body: formData,
        // NE PAS définir Content-Type — le navigateur l'ajoute automatiquement avec la boundary
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }))
        throw new Error(err.error || `Erreur ${res.status}`)
      }
      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      const ref  = data.ref.replace(/\//g, '-')
      const nom  = data.demandeur_nom.split(' ')[0] || 'client'
      a.download = `rapport_expertise_${ref}_${nom}.docx`
      a.click()
      URL.revokeObjectURL(url)
      setSuccess(true)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const renderStep = () => {
    switch (step) {
      case 0: return <StepMission data={data} set={set} />
      case 1: return <StepBien data={data} set={set} />
      case 2: return <StepDescription data={data} set={set} />
      case 3: return <StepPhotos data={data} set={set} />
      case 4: return <StepRisques data={data} set={set} />
      case 5: return <StepEvaluation data={data} set={set} setNested={setNested} />
      case 6: return <StepGeneration data={data} set={set} computeValue={computeValue}
                       generer={generer} loading={loading} error={error} success={success} />
    }
  }

  const progress = Math.round((step / (STEPS.length - 1)) * 100)

  return (
    <>
      <Head>
        <title>ExpertForm · SAGETRIM</title>
        <meta name="description" content="Générateur de rapport d'expertise immobilière SAGETRIM" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="topbar">
        <div>
          <div className="topbar-brand">SAGETRIM <span>·</span> ExpertForm</div>
          <div className="topbar-sub">Rapport d'expertise immobilière</div>
        </div>
        <span style={{fontSize:11,color:'rgba(255,255,255,.4)'}}>
          {data.ref || 'Nouveau dossier'}
        </span>
      </div>

      <div className="main">
        <nav className="stepper">
          <div className="stepper-title">Progression</div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          {STEPS.map((s, i) => {
            const cls = i === step ? 'active' : i < step ? 'done' : ''
            return (
              <div key={s.id} className={`step-item ${cls}`}
                   onClick={() => i <= step + 1 && setStep(i)}>
                <div className="step-dot">{i < step ? '✓' : i + 1}</div>
                <div>
                  <div className="step-label">{s.title}</div>
                  <div className="step-sub">{s.sub}</div>
                </div>
              </div>
            )
          })}
        </nav>

        <div className="card">
          <div className="card-header">
            <div className="card-header-icon">{STEPS[step].icon}</div>
            <div>
              <div className="card-header-title">{STEPS[step].title}</div>
              <div className="card-header-sub">{STEPS[step].sub}</div>
            </div>
            <div className="card-header-step">{step + 1} / {STEPS.length}</div>
          </div>

          <div className="card-body">{renderStep()}</div>

          <div className="card-footer">
            <button className="btn btn-secondary" onClick={() => nav(-1)} disabled={step === 0}>
              ← Précédent
            </button>
            <span style={{fontSize:11,color:'var(--muted)'}}>
              Étape {step + 1} sur {STEPS.length}
            </span>
            {step < STEPS.length - 1 && (
              <button className="btn btn-primary" onClick={() => nav(1)}>
                Suivant →
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// ÉTAPE 1 — MISSION
// ═══════════════════════════════════════════════════════════════════════════════
function StepMission({ data, set }) {
  return (
    <div>
      <div className="sec-title">Référence et demandeur</div>
      <div className="grid-2">
        <Field label="Référence dossier" required>
          <input value={data.ref} onChange={e => set('ref', e.target.value)}
                 placeholder="SAGETRIM-2026-005" />
        </Field>
        <Field label="Date du rapport" required>
          <input type="date" value={data.date_rapport}
                 onChange={e => set('date_rapport', e.target.value)} />
        </Field>
      </div>
      <Field label="Nom complet du demandeur" required>
        <input value={data.demandeur_nom}
               onChange={e => set('demandeur_nom', e.target.value)}
               placeholder="M. Dupont Jean — ou Mme Dupont Marie épouse MARTIN" />
      </Field>
      <div className="grid-2">
        <Field label="Qualité">
          <select value={data.demandeur_qualite} onChange={e => set('demandeur_qualite', e.target.value)}>
            <option value="">—</option>
            <option>Particulier</option>
            <option>SCI</option>
            <option>Entreprise</option>
            <option>Notaire / Mandataire</option>
            <option>Banque / Établissement de crédit</option>
          </select>
        </Field>
        <Field label="Date de visite" required>
          <input type="date" value={data.date_visite}
                 onChange={e => set('date_visite', e.target.value)} />
        </Field>
      </div>
      <Field label="Adresse du demandeur">
        <input value={data.demandeur_adresse}
               onChange={e => set('demandeur_adresse', e.target.value)}
               placeholder="20 rue de la Paix — 97139 Les Abymes" />
      </Field>
      <div className="sep" />
      <div className="sec-title">Objet de la mission</div>
      <Field label="Mission">
        <select value={data.objet_mission} onChange={e => set('objet_mission', e.target.value)}>
          <optgroup label="Valeur vénale">
            <option>Estimation en valeur vénale — pleine propriété</option>
            <option>Estimation pour partage successoral / donation-partage</option>
            <option>Estimation pour garantie de passif</option>
            <option>Estimation en valeur d'apport (SCI / société)</option>
            <option>Estimation en valeur de cession de parts de SCI</option>
            <option>Expertise contradictoire</option>
          </optgroup>
          <optgroup label="Autres bases">
            <option>Estimation en valeur locative de marché</option>
            <option>Estimation en valeur vénale et locative</option>
            <option>Estimation en valeur d'assurance (reconstruction)</option>
          </optgroup>
        </select>
      </Field>
      <Alert type="info">
        Le rapport sera généré conformément à la Charte de l'Expertise en Évaluation Immobilière (5ᵉ éd.)
        et aux normes TEGoVA (EVS 2022).
      </Alert>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// ÉTAPE 2 — IDENTIFICATION DU BIEN
// ═══════════════════════════════════════════════════════════════════════════════
function StepBien({ data, set }) {
  const [iccMsg, setIccMsg] = useState(null)
  const [iccLoading, setIccLoading] = useState(false)

  const recupICC = async () => {
    const s = data.origine_date_acquisition || ''
    const ym = s.match(/(?:19|20)\d{2}/)
    if (!ym) { setIccMsg({ type:'warn', text:"Renseignez d'abord la date d'acquisition (avec l'année)." }); return }
    const annee = ym[0]
    const mois = ['janvier','février','fevrier','mars','avril','mai','juin','juillet','août','aout','septembre','octobre','novembre','décembre','decembre']
    const moisNum = [1,2,2,3,4,5,6,7,8,8,9,10,11,12,12]
    const idx = mois.findIndex(m => s.toLowerCase().includes(m))
    const trimestre = idx >= 0 ? Math.floor((moisNum[idx] - 1) / 3) + 1 : ''
    setIccLoading(true); setIccMsg(null)
    try {
      const res = await fetch(`/api/icc?annee=${annee}${trimestre ? `&trimestre=${trimestre}` : ''}`)
      const out = await res.json()
      if (!res.ok) throw new Error(out.error || `Erreur ${res.status}`)
      if (out.acquisition) set('origine_indice_icc', String(out.acquisition.indice))
      if (out.actuel) set('origine_indice_icc_actuel', String(out.actuel.indice))
      setIccMsg({ type:'ok', text:`${out.acquisition ? `Acquisition : ${out.acquisition.periode} = ${out.acquisition.indice}  ·  ` : ''}Actuel : ${out.actuel.periode} = ${out.actuel.indice} (INSEE).` })
    } catch (e) {
      setIccMsg({ type:'err', text:`Récupération ICC impossible : ${e.message}` })
    } finally {
      setIccLoading(false)
    }
  }

  return (
    <div>
      <div className="sec-title">Type de bien</div>
      <Field label="Type" required hint="Détermine les méthodes d'évaluation utilisées">
        <select value={data.type_bien} onChange={e => set('type_bien', e.target.value)}>
          <option value="maison">Maison individuelle</option>
          <option value="appartement">Appartement en copropriété</option>
          <option value="terrain">Terrain nu</option>
        </select>
      </Field>

      <div className="sep" />
      <div className="sec-title">Localisation</div>
      <Field label="Adresse complète du bien" required>
        <input value={data.adresse_bien} onChange={e => set('adresse_bien', e.target.value)}
               placeholder="96 Rue Siméon Pioche — Lieu-dit Les Sources Pérou" />
      </Field>
      <div className="grid-3">
        <Field label="Code postal">
          <input value={data.code_postal} onChange={e => set('code_postal', e.target.value)}
                 placeholder="97130" />
        </Field>
        <Field label="Commune" required>
          <input value={data.commune} onChange={e => set('commune', e.target.value)}
                 placeholder="CAPESTERRE-BELLE-EAU" />
        </Field>
        <Field label="Assainissement">
          <select value={data.assainissement} onChange={e => set('assainissement', e.target.value)}>
            <option>Collectif</option>
            <option>Autonome</option>
            <option>Mixte</option>
          </select>
        </Field>
      </div>
      <Field label="Lieu-dit">
        <input value={data.lieu_dit} onChange={e => set('lieu_dit', e.target.value)}
               placeholder="Les Sources Pérou, Anquetil, Le Helleux…" />
      </Field>

      <div className="sep" />
      <div className="sec-title">Données cadastrales</div>
      <div className="grid-3">
        <Field label="Section cadastrale" required>
          <input value={data.cadastre_section} onChange={e => set('cadastre_section', e.target.value)}
                 placeholder="AO, CO, AC…" />
        </Field>
        <Field label="Numéro de parcelle" required>
          <input value={data.cadastre_num} onChange={e => set('cadastre_num', e.target.value)}
                 placeholder="142, 20, 1103…" />
        </Field>
        <Field label="Surface terrain (m²)">
          <input type="number" value={data.terrain_m2} onChange={e => set('terrain_m2', e.target.value)}
                 placeholder="290" />
        </Field>
      </div>
      <Field label="Zonage PLU">
        <input value={data.zonage_plu} onChange={e => set('zonage_plu', e.target.value)}
               placeholder="Zone UB — Résidentielle périphérique (PLU …)" />
      </Field>
      <div className="grid-2">
        <Field label="Constructibilité résiduelle" hint="Extension / emprise au sol restante">
          <input value={data.constructibilite} onChange={e => set('constructibilite', e.target.value)}
                 placeholder="Extension possible — emprise résiduelle ~80 m²" />
        </Field>
        <Field label="Droit de préemption urbain (DPU)">
          <select value={data.dpu} onChange={e => set('dpu', e.target.value)}>
            <option>À vérifier</option>
            <option>Soumis au DPU</option>
            <option>Non soumis au DPU</option>
          </select>
        </Field>
      </div>

      <div className="sep" />
      <div className="sec-title">Origine de propriété (acte)</div>
      <Alert type="info">
        À renseigner depuis l'acte de propriété. La date et le prix d'acquisition, avec les
        indices ICC, alimentent automatiquement la méthode d'actualisation (maison).
      </Alert>
      <div className="grid-2" style={{marginTop:'.5rem'}}>
        <Field label="Nature de l'acquisition">
          <select value={data.origine_nature} onChange={e => set('origine_nature', e.target.value)}>
            <option>Acquisition à titre onéreux</option>
            <option>Donation-partage</option>
            <option>Succession</option>
            <option>Apport en société</option>
            <option>Autre</option>
          </select>
        </Field>
        <Field label="Date d'acquisition" hint="Telle qu'indiquée sur l'acte">
          <input value={data.origine_date_acquisition} onChange={e => set('origine_date_acquisition', e.target.value)}
                 placeholder="15 mars 2015" />
        </Field>
      </div>
      <div className="grid-2">
        <Field label="Prix d'acquisition (€)" hint="Net vendeur">
          <input type="number" value={data.origine_prix_acquisition} onChange={e => set('origine_prix_acquisition', e.target.value)}
                 placeholder="180000" />
        </Field>
        <Field label="Notaire / étude">
          <input value={data.origine_notaire} onChange={e => set('origine_notaire', e.target.value)}
                 placeholder="Me Dupont — Pointe-à-Pitre" />
        </Field>
      </div>
      <div className="grid-2">
        <Field label="Indice ICC à l'acquisition" hint="INSEE — trimestre de l'acte">
          <input type="number" value={data.origine_indice_icc} onChange={e => set('origine_indice_icc', e.target.value)}
                 placeholder="1671" />
        </Field>
        <Field label="Indice ICC actuel" hint="INSEE — dernier trimestre publié">
          <input type="number" value={data.origine_indice_icc_actuel} onChange={e => set('origine_indice_icc_actuel', e.target.value)}
                 placeholder="2146" />
        </Field>
      </div>
      <div style={{display:'flex',alignItems:'center',gap:10,marginTop:8,flexWrap:'wrap'}}>
        <button className="btn btn-secondary" style={{fontSize:13}} onClick={recupICC} disabled={iccLoading}>
          {iccLoading ? '⏳ Récupération…' : '⟳ Récupérer l\'ICC automatiquement (INSEE)'}
        </button>
        <span style={{fontSize:11,color:'var(--muted)'}}>Remplit les deux indices d'après la date d'acquisition</span>
      </div>
      {iccMsg && (
        <div style={{marginTop:8}}>
          <Alert type={iccMsg.type === 'ok' ? 'ok' : iccMsg.type === 'warn' ? 'warn' : 'err'}>{iccMsg.text}</Alert>
        </div>
      )}

      <div className="sep" />
      <div className="sec-title">Servitudes, mitoyenneté & occupation</div>
      <Field label="Servitudes" hint="Passage, vue, réseaux… (figurent sur l'acte)">
        <textarea value={data.servitudes} onChange={e => set('servitudes', e.target.value)}
                  placeholder="Servitude de passage au profit de la parcelle AO 143 ; canalisation enterrée…" />
      </Field>
      <Field label="Mitoyenneté">
        <input value={data.mitoyennete} onChange={e => set('mitoyennete', e.target.value)}
               placeholder="Mur mitoyen côté Est avec la parcelle AO 141" />
      </Field>
      <div className="grid-2">
        <Field label="Situation d'occupation">
          <select value={data.situation_occupation} onChange={e => set('situation_occupation', e.target.value)}>
            <option>Libre de toute occupation</option>
            <option>Occupé par le propriétaire</option>
            <option>Loué — bail en cours</option>
            <option>Occupé à titre gratuit</option>
          </select>
        </Field>
        <Field label="Détail du bail (si loué)" hint="Loyer, type, échéance">
          <input value={data.bail_details} onChange={e => set('bail_details', e.target.value)}
                 placeholder="Bail d'habitation — 750 €/mois — échéance 06/2027" />
        </Field>
      </div>

      <div className="sep" />
      <div className="sec-title">Environnement immédiat</div>
      <div className="grid-2">
        <Field label="Distance centre-ville / bourg">
          <input value={data.env_distance_centre}
                 onChange={e => set('env_distance_centre', e.target.value)}
                 placeholder="1,5 km du centre-bourg" />
        </Field>
        <Field label="Accès / voiries">
          <input value={data.env_acces}
                 onChange={e => set('env_acces', e.target.value)}
                 placeholder="RN1, voie communale bitumée…" />
        </Field>
        <Field label="Transports en commun">
          <input value={data.env_transports}
                 onChange={e => set('env_transports', e.target.value)}
                 placeholder="Bus Karulis — arrêt à 200 m" />
        </Field>
        <Field label="Commerces / écoles / services">
          <input value={data.env_commerces}
                 onChange={e => set('env_commerces', e.target.value)}
                 placeholder="Carrefour à 800 m, école primaire à 400 m" />
        </Field>
      </div>

      <div className="sep" />
      <div className="sec-title">Marché immobilier local</div>
      <div className="grid-2">
        <Field label="Tendance de marché" hint="Au moment de l'expertise">
          <select value={data.marche_tendance} onChange={e => set('marche_tendance', e.target.value)}>
            <option>Stable</option>
            <option>Haussier — demande supérieure à l'offre</option>
            <option>Baissier — offre supérieure à la demande</option>
            <option>Atone — peu de transactions</option>
          </select>
        </Field>
        <Field label="Tension offre / demande">
          <select value={data.marche_tension} onChange={e => set('marche_tension', e.target.value)}>
            <option>Équilibrée</option>
            <option>Forte demande — pénurie d'offre</option>
            <option>Offre abondante — demande faible</option>
            <option>Marché spéculatif</option>
          </select>
        </Field>
      </div>

      {data.type_bien === 'appartement' && (
        <>
          <div className="sep" />
          <div className="sec-title">Copropriété</div>
          <div className="grid-2">
            <Field label="Numéro de lot">
              <input value={data.lot_copro} onChange={e => set('lot_copro', e.target.value)}
                     placeholder="59" />
            </Field>
            <Field label="Millièmes de copropriété">
              <input value={data.millesimes} onChange={e => set('millesimes', e.target.value)}
                     placeholder="662/100000 des parties communes générales" />
            </Field>
          </div>
          <div className="grid-2">
            <Field label="Bâtiment">
              <input value={data.batiment} onChange={e => set('batiment', e.target.value)}
                     placeholder="NS3, Bât. A…" />
            </Field>
            <Field label="Niveau / Étage">
              <input value={data.niveau_etage} onChange={e => set('niveau_etage', e.target.value)}
                     placeholder="au 4ᵉ étage, porte de gauche, escalier 1" />
            </Field>
          </div>
        </>
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// ÉTAPE 3 — DESCRIPTION
// ═══════════════════════════════════════════════════════════════════════════════
function StepDescription({ data, set }) {
  const annee = parseInt(data.annee_construction) || 0
  const ageGlobal = annee ? new Date().getFullYear() - annee : 0

  const handleAnneeChange = (val) => {
    set('annee_construction', val)
    const a = parseInt(val)
    if (a > 1800 && a <= new Date().getFullYear()) {
      if (!data.vetuste_postes || data.vetuste_postes.length === 0) {
        set('vetuste_postes', initVetustePostes(a))
      }
    }
  }

  const postes = data.vetuste_postes || []
  const vetusteGlobale = postes.reduce((acc, p) => {
    const v = Math.min(parseFloat(p.age_effectif||0) / (parseFloat(p.duree_vie||1)||1), 1)
    return acc + parseFloat(p.pct_cout||0) * v
  }, 0)

  const updatePoste = (i, field, val) => {
    set('vetuste_postes', postes.map((p, j) => j === i ? { ...p, [field]: val } : p))
  }

  const updateCarac = (i, field, val) => {
    set('carac_physiques', (data.carac_physiques||[]).map((c, j) => j === i ? { ...c, [field]: val } : c))
  }

  return (
    <div>
      <div className="sec-title">Surfaces</div>
      <Alert type="warn">
        La Surface de Plancher (SDP) est obligatoire — art. R. 111-22 Code urbanisme.
        La SHOB et la SHON sont abrogées depuis mars 2012.
      </Alert>
      <div className="grid-3" style={{marginTop:'.75rem'}}>
        <Field label="Surface de plancher SDP (m²)" required>
          <input type="number" value={data.sdp} onChange={e => set('sdp', e.target.value)}
                 placeholder="150, 195, 40…" />
        </Field>
        <Field label="Année de construction">
          <input type="number" value={data.annee_construction}
                 onChange={e => handleAnneeChange(e.target.value)}
                 placeholder="1967, 1985…" />
        </Field>
        {data.type_bien === 'appartement' && (
          <Field label="Type appartement">
            <select value={data.type_appart} onChange={e => set('type_appart', e.target.value)}>
              {['F1','F2','F3','F4','F5','F6','Studio'].map(t => <option key={t}>{t}</option>)}
            </select>
          </Field>
        )}
      </div>

      {data.type_bien !== 'terrain' && (
        <div className="grid-2" style={{marginTop:'.5rem'}}>
          <Field label="Surface habitable (m²)" hint="Surface réelle (hors annexes)">
            <input type="number" value={data.surface_habitable} onChange={e => set('surface_habitable', e.target.value)}
                   placeholder="160" />
          </Field>
          {data.type_bien === 'appartement' && (
            <Field label="Surface loi Carrez (m²)" hint="Obligatoire en copropriété">
              <input type="number" value={data.surface_carrez} onChange={e => set('surface_carrez', e.target.value)}
                     placeholder="58.5" />
            </Field>
          )}
        </div>
      )}

      {data.type_bien !== 'terrain' && (
        <>
          <Toggle label="Ascenseur" sub="Si non : facteur correctif négatif appliqué"
                  checked={data.ascenseur} onChange={v => set('ascenseur', v)} />

          <div className="sep" />
          <div className="sec-title">Composition</div>
          {data.distribution.map((item, i) => (
            <div key={i} style={{display:'flex',gap:8,marginBottom:6}}>
              <input
                value={item}
                onChange={e => set('distribution', data.distribution.map((d,j) => j===i ? e.target.value : d))}
                placeholder={`Pièce / élément ${i+1} (ex. 2 chambres, 1 cuisine, terrasse…)`}
                style={{padding:'7px 10px',border:'1px solid var(--border)',
                        borderRadius:'var(--r)',fontSize:13,flex:1}}
              />
            </div>
          ))}
          <button className="btn btn-secondary" style={{fontSize:12,marginTop:4}}
                  onClick={() => set('distribution', [...data.distribution, ''])}>
            + Ajouter une ligne
          </button>

          <div className="sep" />
          <div className="sec-title">État général</div>
          <div className="grid-2">
            <Field label="État intérieur">
              <select value={data.etat_general} onChange={e => set('etat_general', e.target.value)}>
                <option>Excellent — aucun défaut</option>
                <option>Bon état d'usage</option>
                <option>État moyen — travaux à prévoir</option>
                <option>Mauvais état — gros travaux</option>
              </select>
            </Field>
            {data.type_bien === 'appartement' && (
              <Field label="Parties communes">
                <select value={data.etat_communs} onChange={e => set('etat_communs', e.target.value)}>
                  <option>Excellent</option>
                  <option>Bon</option>
                  <option>Moyen</option>
                  <option>Dégradé — facteur dépressif</option>
                </select>
              </Field>
            )}
          </div>

          <div className="sep" />
          <div className="sec-title">Caractéristiques par poste</div>
          <Alert type="info">
            État constaté lors de la visite — apparaît dans le rapport (§ Description des biens).
          </Alert>
          <div className="vet-table-wrap" style={{marginTop:'.6rem'}}>
            <table className="vet-tbl">
              <thead>
                <tr>
                  <th style={{width:'35%'}}>Poste</th>
                  <th style={{width:'20%'}}>État constaté</th>
                  <th>Observations</th>
                </tr>
              </thead>
              <tbody>
                {(data.carac_physiques||[]).map((c, i) => (
                  <tr key={i}>
                    <td className="vet-poste">{c.poste}</td>
                    <td>
                      <select value={c.etat} onChange={e => updateCarac(i, 'etat', e.target.value)}
                              style={{fontSize:11,padding:'3px 5px',border:'1px solid var(--border)',borderRadius:4,width:'100%'}}>
                        <option>Neuf / récent</option>
                        <option>Bon</option>
                        <option>Moyen</option>
                        <option>Mauvais</option>
                        <option>Rénové</option>
                        <option>Non visible</option>
                      </select>
                    </td>
                    <td>
                      <input value={c.notes} onChange={e => updateCarac(i, 'notes', e.target.value)}
                             placeholder="Ex. toiture refaite 2018, clim reversible…"
                             style={{width:'100%',fontSize:11,padding:'3px 6px',border:'1px solid var(--border)',borderRadius:4}} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Vétusté décomposée — maison uniquement */}
      {data.type_bien === 'maison' && postes.length > 0 && (
        <>
          <div className="sep" />
          <div className="sec-title">Vétusté par poste</div>
          <Alert type="info">
            Modifiez l'âge effectif si un élément a été rénové (ex. toiture refaite en 2018 → 8 ans).
            La vétusté globale se recalcule automatiquement.
          </Alert>
          <div className="vet-table-wrap" style={{marginTop:'.6rem'}}>
            <table className="vet-tbl">
              <thead>
                <tr>
                  <th>Poste</th><th>% coût</th><th>Âge eff.</th>
                  <th>Durée vie</th><th>Vét.</th><th>Contrib.</th>
                </tr>
              </thead>
              <tbody>
                {postes.map((p, i) => {
                  const vet = Math.min(parseFloat(p.age_effectif||0) / (parseFloat(p.duree_vie||1)||1), 1)
                  return (
                    <tr key={i}>
                      <td className="vet-poste">{p.poste}</td>
                      <td style={{textAlign:'center',color:'var(--muted)'}}>{p.pct_cout} %</td>
                      <td>
                        <input type="number" min="0" max="150" value={p.age_effectif}
                               onChange={e => updatePoste(i, 'age_effectif', e.target.value)}
                               className="vet-input" />
                      </td>
                      <td>
                        <input type="number" min="1" max="200" value={p.duree_vie}
                               onChange={e => updatePoste(i, 'duree_vie', e.target.value)}
                               className="vet-input" />
                      </td>
                      <td style={{textAlign:'center'}}>{(vet*100).toFixed(0)} %</td>
                      <td style={{textAlign:'center',fontWeight:600,color:'var(--navy)'}}>
                        {(parseFloat(p.pct_cout||0)*vet).toFixed(1)} %
                      </td>
                    </tr>
                  )
                })}
              </tbody>
              <tfoot>
                <tr className="vet-total">
                  <td colSpan="5">Vétusté globale pondérée</td>
                  <td style={{textAlign:'center'}}>{vetusteGlobale.toFixed(1)} %</td>
                </tr>
              </tfoot>
            </table>
          </div>
          <button className="btn btn-secondary" style={{fontSize:11,marginTop:6}}
                  onClick={() => set('vetuste_postes', initVetustePostes(annee))}>
            Réinitialiser (âge = {ageGlobal} ans)
          </button>
        </>
      )}
      {data.type_bien === 'maison' && annee > 0 && postes.length === 0 && (
        <div style={{marginTop:'.75rem'}}>
          <button className="btn btn-secondary" onClick={() => set('vetuste_postes', initVetustePostes(annee))}>
            Initialiser le tableau de vétusté
          </button>
        </div>
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// ÉTAPE 4 — PHOTOS
// ═══════════════════════════════════════════════════════════════════════════════
function StepPhotos({ data, set }) {
  const inputRef = useRef()

  const handleFiles = async (files) => {
    const MAX_DIM = 1400
    const QUALITY = 0.78
    const processed = await Promise.all(Array.from(files).map(f => new Promise(resolve => {
      const reader = new FileReader()
      reader.onload = (ev) => {
        const img = new window.Image()
        img.onload = () => {
          let { width: w, height: h } = img
          if (w > MAX_DIM || h > MAX_DIM) {
            if (w >= h) { h = Math.round(h * MAX_DIM / w); w = MAX_DIM }
            else        { w = Math.round(w * MAX_DIM / h); h = MAX_DIM }
          }
          const canvas = document.createElement('canvas')
          canvas.width = w; canvas.height = h
          canvas.getContext('2d').drawImage(img, 0, 0, w, h)
          resolve({ name: f.name, data: canvas.toDataURL('image/jpeg', QUALITY), caption: '' })
        }
        img.src = ev.target.result
      }
      reader.readAsDataURL(f)
    })))
    set('photos', [...data.photos, ...processed])
  }

  return (
    <div>
      <Alert type="info">
        Ajoutez les photos prises lors de la visite. Elles s'intègrent automatiquement
        en Annexe VII du rapport, 2 par ligne avec légende.
      </Alert>

      <div className="photo-drop-zone"
           onClick={() => inputRef.current?.click()}
           onDrop={e => { e.preventDefault(); handleFiles(e.dataTransfer.files) }}
           onDragOver={e => e.preventDefault()}>
        <div className="photo-drop-icon">📷</div>
        <div className="photo-drop-label">Cliquez ou déposez vos photos ici</div>
        <div className="photo-drop-sub">JPEG · PNG · HEIC — redimensionnées automatiquement</div>
        <input ref={inputRef} type="file" multiple accept="image/*"
               style={{display:'none'}} onChange={e => handleFiles(e.target.files)} />
      </div>

      {data.photos.length > 0 && (
        <>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',margin:'.75rem 0 .4rem'}}>
            <div className="sec-title" style={{margin:0}}>
              {data.photos.length} photo{data.photos.length > 1 ? 's' : ''}
            </div>
            <button className="btn btn-secondary" style={{fontSize:11}}
                    onClick={() => set('photos', [])}>Tout supprimer</button>
          </div>
          <div className="photo-grid">
            {data.photos.map((photo, i) => (
              <div key={i} className="photo-card">
                <div className="photo-card-img-wrap">
                  <img src={photo.data} alt={photo.name} className="photo-card-img" />
                  <button className="photo-del"
                          onClick={() => set('photos', data.photos.filter((_,j) => j!==i))}>×</button>
                  <div className="photo-num">{i + 1}</div>
                </div>
                <input className="photo-caption-input" value={photo.caption}
                       onChange={e => set('photos', data.photos.map((p,j) => j===i ? {...p,caption:e.target.value} : p))}
                       placeholder="Légende (Façade, Séjour, Toiture…)" />
              </div>
            ))}
          </div>
          <div style={{fontSize:11,color:'var(--muted)',marginTop:6,textAlign:'right'}}>
            Taille estimée : {(data.photos.reduce((a,p) => a+(p.data?.length||0),0)/1024/1024*0.75).toFixed(1)} Mo
          </div>
        </>
      )}
      {data.photos.length === 0 && (
        <div style={{textAlign:'center',color:'var(--muted)',fontSize:12,padding:'1rem 0'}}>
          Aucune photo — le rapport mentionnera la visite sans reportage photographique joint.
        </div>
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// ÉTAPE 5 — RISQUES
// ═══════════════════════════════════════════════════════════════════════════════
function StepRisques({ data, set }) {
  return (
    <div>
      <div className="sec-title">Risques naturels</div>
      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:8,marginBottom:8}}>
        <div style={{border:'1px solid var(--border)',borderRadius:'var(--r)',padding:'10px 12px'}}>
          <div style={{fontSize:11,fontWeight:600,color:'var(--navy)',marginBottom:6}}>Zone sismique</div>
          <select value={data.zone_sismique} onChange={e => set('zone_sismique', e.target.value)}
                  style={{width:'100%',padding:'6px 8px',border:'1px solid var(--border)',borderRadius:'var(--r)',fontSize:13}}>
            {['I','II','III','IV','V'].map(z => (
              <option key={z} value={z}>{z}{z==='V'?' — Maximale (Guadeloupe)':''}</option>
            ))}
          </select>
          {data.zone_sismique === 'V' && (
            <div style={{marginTop:6,fontSize:11,color:'var(--alert)',fontWeight:500}}>
              Zone maximale — conformité PS92 à vérifier
            </div>
          )}
        </div>
        <div style={{border:'1px solid var(--border)',borderRadius:'var(--r)',padding:'10px 12px'}}>
          <div style={{fontSize:11,fontWeight:600,color:'var(--navy)',marginBottom:6}}>Termites</div>
          <label style={{display:'flex',alignItems:'center',gap:8,fontSize:13,cursor:'pointer'}}>
            <input type="radio" name="termites" checked={data.termites_zone}
                   onChange={() => set('termites_zone', true)} /> Zone contaminée
          </label>
          <label style={{display:'flex',alignItems:'center',gap:8,fontSize:13,cursor:'pointer',marginTop:4}}>
            <input type="radio" name="termites" checked={!data.termites_zone}
                   onChange={() => set('termites_zone', false)} /> Hors zone
          </label>
        </div>
      </div>
      <Toggle label="PPRN applicable" sub="Plan de Prévention des Risques Naturels"
              checked={data.pprn} onChange={v => set('pprn', v)} />
      <Toggle label="Zone cyclonique" sub="Territoire exposé aux cyclones"
              checked={true} onChange={() => {}} />

      <div className="sep" />
      <div className="sec-title">Diagnostics obligatoires</div>
      <Alert type="info">
        Art. L. 271-4 CCH — Cocher les diagnostics fournis. Les manquants généreront
        des réserves automatiques dans le rapport.
      </Alert>
      <div style={{marginTop:'.75rem'}}>
        {[
          ['diag_amiante',  'Diagnostic amiante',           'Obligatoire si construction avant 1997'],
          ['diag_termites', 'Diagnostic termites',          'Obligatoire en zone contaminée'],
          ['diag_elec',     'Diagnostic électricité',       'Obligatoire si installation > 15 ans'],
          ['diag_dpe',      'DPE — Performance énergétique','Obligatoire pour toute mutation'],
        ].map(([key, label, sub]) => (
          <Toggle key={key} label={label} sub={sub}
                  checked={data[key]} onChange={v => set(key, v)} />
        ))}
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// ÉTAPE 6 — ÉVALUATION
// ═══════════════════════════════════════════════════════════════════════════════
function StepEvaluation({ data, set, setNested }) {
  const retained = data.dvf_refs.filter(r => r.retenu && r.pm2)
  const pm2s = retained.map(r => parseFloat(r.pm2)).filter(v => v > 0).sort((a,b)=>a-b)
  const calcMedian = pm2s.length ? pm2s[Math.floor(pm2s.length/2)] : 0
  const sdp = parseFloat(data.sdp) || 0
  const pm2_used = parseFloat(data.pm2_median) || calcMedian
  const valeur = sdp && pm2_used ? Math.round(sdp * pm2_used / 1000) * 1000 : 0

  const [dvfLoading, setDvfLoading] = useState(false)
  const [dvfMsg, setDvfMsg] = useState(null)

  const rechercherDVF = async () => {
    setDvfLoading(true)
    setDvfMsg(null)
    try {
      const res = await fetch('/api/dvf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          commune: data.commune,
          code_postal: data.code_postal,
          adresse_bien: data.adresse_bien,
          type_bien: data.type_bien,
          sdp: data.sdp,
        }),
      })
      const out = await res.json().catch(() => ({ error: `HTTP ${res.status}` }))
      if (!res.ok) throw new Error(out.error || `Erreur ${res.status}`)
      if (out.warning) { setDvfMsg({ type: 'warn', text: out.warning }); return }
      if (!out.refs || out.refs.length === 0) {
        setDvfMsg({ type: 'warn', text: `Aucune vente trouvée pour ${out.commune || data.commune}. Vérifiez la commune ou saisissez manuellement.` })
        return
      }
      set('dvf_refs', out.refs)
      set('periode_dvf', `${out.periode_mois || 24} mois (DVF data.gouv)`)
      setDvfMsg({ type: 'ok', text: `${out.count} vente(s) importée(s) — ${out.commune} — médiane ${out.pm2_median.toLocaleString('fr-FR')} €/m²` })
    } catch (e) {
      setDvfMsg({ type: 'err', text: e.message })
    } finally {
      setDvfLoading(false)
    }
  }

  return (
    <div>
      <Alert type="info">
        Importez les ventes comparables depuis data.gouv ou saisissez-les manuellement.
        Décochez les valeurs aberrantes — médiane et valeur se recalculent automatiquement.
        La Charte recommande 5 références minimum.
      </Alert>
      {retained.length > 0 && retained.length < 5 && (
        <Alert type="warn">
          {retained.length} référence{retained.length>1?'s':''} retenue{retained.length>1?'s':''} —
          5 minimum recommandées. Élargissez la zone ou la période DVF.
        </Alert>
      )}

      <div style={{display:'flex',alignItems:'center',gap:10,marginTop:'.75rem',flexWrap:'wrap'}}>
        <button className="btn btn-primary" style={{fontSize:13}}
                onClick={rechercherDVF} disabled={dvfLoading || !data.commune}>
          {dvfLoading ? '⏳ Recherche en cours…' : '🔍 Rechercher les ventes DVF'}
        </button>
        <span style={{fontSize:11,color:'var(--muted)'}}>
          {data.commune ? `Commune : ${data.commune}` : 'Renseignez la commune (étape Identification)'}
        </span>
      </div>
      {dvfMsg && (
        <div style={{marginTop:8}}>
          <Alert type={dvfMsg.type}>{dvfMsg.text}</Alert>
        </div>
      )}

      <div className="sec-title" style={{marginTop:'.75rem'}}>Références DVF</div>
      <div className="tbl-wrap">
        <table className="dvf-tbl">
          <thead>
            <tr>
              <th>✓</th><th>Date</th><th>Localisation</th><th>Type</th>
              <th>SDP m²</th><th>Valeur €</th><th>€/m²</th>
            </tr>
          </thead>
          <tbody>
            {data.dvf_refs.map((r, i) => (
              <tr key={i} className={!r.retenu ? 'excl' : ''}>
                <td>
                  <input type="checkbox" checked={r.retenu}
                         onChange={e => {
                           const refs = data.dvf_refs.map((x,j) => j===i ? {...x,retenu:e.target.checked} : x)
                           set('dvf_refs', refs)
                         }} />
                </td>
                {['date','localisation','type','surface','valeur','pm2'].map(f => (
                  <td key={f}>
                    <input value={r[f]} onChange={e => setNested('dvf_refs', i, f, e.target.value)}
                           style={{border:'1px solid var(--border)',borderRadius:4,
                                   padding:'3px 6px',fontSize:11,width:'100%',
                                   textDecoration:!r.retenu?'line-through':'none'}} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <button className="btn btn-secondary" style={{fontSize:12,marginTop:6}}
              onClick={() => set('dvf_refs', [...data.dvf_refs, {date:'',localisation:'',type:'',surface:'',valeur:'',pm2:'',retenu:true,statut:'Retenue'}])}>
        + Ajouter une référence
      </button>

      <div className="stats-grid" style={{marginTop:'.75rem'}}>
        <div className="stat-card">
          <div className="stat-l">Références retenues</div>
          <div className="stat-v">{retained.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-l">Médiane calculée</div>
          <div className="stat-v">{calcMedian ? calcMedian.toLocaleString('fr-FR')+' €/m²' : '—'}</div>
        </div>
        <div className="stat-card">
          <div className="stat-l">Prix médian retenu</div>
          <div className="stat-v">{pm2_used ? pm2_used.toLocaleString('fr-FR')+' €/m²' : '—'}</div>
          <div className="stat-s">modifiable ci-dessous</div>
        </div>
        <div className="stat-card">
          <div className="stat-l">Valeur estimée</div>
          <div className="stat-v" style={{fontSize:14}}>{valeur ? valeur.toLocaleString('fr-FR')+' €' : '—'}</div>
        </div>
      </div>

      <div className="sep" />
      <div className="sec-title">Paramètres de calcul</div>
      <div className="grid-3">
        <Field label="Prix médian retenu (€/m²)" hint="Laisser vide = médiane auto">
          <input type="number" value={data.pm2_median}
                 onChange={e => set('pm2_median', e.target.value)}
                 placeholder={calcMedian || '1 176'} />
        </Field>
        {data.type_bien !== 'appartement' && (
          <>
            <Field label="Coût reconstruction (€/m² SDP)" hint="Indice BT01 Guadeloupe 2026">
              <input type="number" value={data.cout_construction_m2}
                     onChange={e => set('cout_construction_m2', e.target.value)} />
            </Field>
            <Field label="Vétusté pondérée (%)" hint="Auto-calculée si tableau renseigné (étape 3)">
              <input type="number" value={data.vetuste_taux}
                     onChange={e => set('vetuste_taux', e.target.value)} />
            </Field>
          </>
        )}
      </div>

      <div className="sep" />
      <div className="sec-title">Valeur locative de marché</div>
      <Alert type="info">
        Facultatif — calcule le taux de capitalisation brut pour valider la cohérence
        de la valeur vénale. Marché Guadeloupe : 5–8 % brut typique.
      </Alert>
      <div className="grid-2" style={{marginTop:'.6rem'}}>
        <Field label="Loyer mensuel de marché (€/mois)" hint="Hors charges">
          <input type="number" value={data.valeur_locative_mensuelle}
                 onChange={e => set('valeur_locative_mensuelle', e.target.value)}
                 placeholder="Ex. : 750" />
        </Field>
        {valeur > 0 && parseFloat(data.valeur_locative_mensuelle) > 0 && (() => {
          const tc = (parseFloat(data.valeur_locative_mensuelle)*12/valeur*100)
          return (
            <div className="stat-card" style={{alignSelf:'flex-end'}}>
              <div className="stat-l">Taux de capitalisation brut</div>
              <div className="stat-v" style={{fontSize:18,color:tc<4.5||tc>9?'var(--alert)':'var(--success)'}}>
                {tc.toFixed(1)} %
              </div>
              <div className="stat-s">Cible marché GP : 5–8 %</div>
            </div>
          )
        })()}
      </div>

      {valeur > 0 && (
        <div className="value-box">
          <div>
            <div className="value-box-label">VALEUR ESTIMÉE</div>
            <div className="value-box-amount">{valeur.toLocaleString('fr-FR')} €</div>
            <div className="value-box-range">
              {(Math.round(valeur*0.93/1000)*1000).toLocaleString('fr-FR')} — {(Math.round(valeur*1.05/1000)*1000).toLocaleString('fr-FR')} €
            </div>
          </div>
          <div style={{textAlign:'right',fontSize:11,color:'rgba(255,255,255,.45)'}}>
            <div>{sdp} m² × {pm2_used} €/m²</div>
            <div style={{marginTop:3}}>{retained.length} réf. DVF</div>
          </div>
        </div>
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// ÉTAPE 7 — GÉNÉRATION
// ═══════════════════════════════════════════════════════════════════════════════
function StepGeneration({ data, set, computeValue, generer, loading, error, success }) {
  const valeur = computeValue()
  const missingDiag = [
    ['diag_amiante','Amiante'],['diag_termites','Termites'],
    ['diag_elec','Électricité'],['diag_dpe','DPE'],
  ].filter(([k]) => !data[k]).map(([,l]) => l)

  const decote = parseFloat(data.decote_liquidation) || 15
  const valLiq = valeur ? Math.round(valeur*(1-decote/100)/1000)*1000 : 0
  const locMens = parseFloat(data.valeur_locative_mensuelle) || 0
  const tauxCapi = valeur && locMens ? (locMens*12/valeur*100).toFixed(1) : null

  return (
    <div>
      {success && <Alert type="ok">✓ Rapport généré avec succès ! Le document Word a été téléchargé.</Alert>}
      {error   && <Alert type="err">Erreur de génération : {error}</Alert>}

      <div className="sec-title">Récapitulatif du dossier</div>
      <div className="summary-grid">
        {[
          ['Référence',       data.ref],
          ['Date rapport',    data.date_rapport],
          ['Demandeur',       data.demandeur_nom],
          ['Bien',            data.commune || data.adresse_bien],
          ['SDP',             data.sdp ? `${data.sdp} m²` : null],
          ['Réf. DVF',        `${data.dvf_refs.filter(r=>r.retenu).length} / ${data.dvf_refs.length}`],
          ['Photos',          `${data.photos.length} photo${data.photos.length!==1?'s':''}`],
        ].map(([label, val]) => (
          <div key={label} className="summary-item">
            <div className="summary-item-label">{label}</div>
            <div className="summary-item-value">
              {val || <span style={{color:'var(--alert)'}}>⚠ Non renseigné</span>}
            </div>
          </div>
        ))}
      </div>

      {valeur > 0 && (
        <div className="synth-box">
          <div className="synth-row synth-main">
            <span>Valeur vénale retenue</span>
            <span>{valeur.toLocaleString('fr-FR')} €</span>
          </div>
          <div className="synth-row">
            <span>Fourchette basse (−7 %)</span>
            <span>{(Math.round(valeur*0.93/1000)*1000).toLocaleString('fr-FR')} €</span>
          </div>
          <div className="synth-row">
            <span>Fourchette haute (+5 %)</span>
            <span>{(Math.round(valeur*1.05/1000)*1000).toLocaleString('fr-FR')} €</span>
          </div>
          <div className="synth-row synth-liq">
            <span>Valeur de liquidation rapide (−{decote} %)</span>
            <span>{valLiq.toLocaleString('fr-FR')} €</span>
          </div>
          {tauxCapi && (
            <div className="synth-row">
              <span>Taux de capitalisation brut</span>
              <span style={{color:parseFloat(tauxCapi)<4.5||parseFloat(tauxCapi)>9?'#8B2020':'#1A4A2E',fontWeight:600}}>
                {tauxCapi} %
              </span>
            </div>
          )}
        </div>
      )}

      {missingDiag.length > 0 && (
        <Alert type="warn">
          Réserves automatiques — diagnostics manquants : {missingDiag.join(', ')}.
          Ces réserves apparaîtront dans le rapport.
        </Alert>
      )}

      <div className="sep" />
      <div className="sec-title">Paramètres de conclusion</div>
      <div className="grid-2">
        <Field label="Décote liquidation rapide (%)" hint="Banques : 15–20 % typique">
          <input type="number" min="0" max="40" value={data.decote_liquidation}
                 onChange={e => set('decote_liquidation', e.target.value)} />
        </Field>
        <Field label="Durée de validité du rapport">
          <select value={data.duree_validite} onChange={e => set('duree_validite', e.target.value)}>
            <option>6 mois à compter de la date du rapport</option>
            <option>3 mois à compter de la date du rapport</option>
            <option>12 mois à compter de la date du rapport</option>
            <option>Valeur arrêtée à la date du rapport uniquement</option>
          </select>
        </Field>
      </div>
      <Field label="Texte de la valeur retenue (conclusion)"
             hint="Optionnel — calculé automatiquement si vide">
        <input value={data.valeur_retenue_texte}
               onChange={e => set('valeur_retenue_texte', e.target.value)}
               placeholder={`${(valeur||0).toLocaleString('fr-FR')} € (… euros)`} />
      </Field>

      <button className="btn-generate" onClick={generer} disabled={loading || !data.demandeur_nom}>
        {loading ? <><span className="spinner" /> Génération du rapport en cours…</> : <>📄 Générer le rapport Word</>}
      </button>

      <div style={{marginTop:8,textAlign:'center',fontSize:11,color:'var(--muted)'}}>
        Le document Word SAGETRIM sera téléchargé automatiquement · Conforme Charte TEGoVA
      </div>
    </div>
  )
}
