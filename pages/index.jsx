import { useState, useCallback } from 'react'
import Head from 'next/head'

// ─── Configuration des étapes ────────────────────────────────────────────────
const STEPS = [
  { id: 'mission',     icon: '📋', title: 'Mission',        sub: 'Demandeur et dates' },
  { id: 'bien',        icon: '🏠', title: 'Identification',  sub: 'Adresse et cadastre' },
  { id: 'description', icon: '📐', title: 'Description',    sub: 'Surfaces et composition' },
  { id: 'risques',     icon: '⚠️',  title: 'Risques',        sub: 'Naturels et diagnostics' },
  { id: 'evaluation',  icon: '📊', title: 'Évaluation',     sub: 'DVF et calcul de valeur' },
  { id: 'generation',  icon: '✅', title: 'Génération',     sub: 'Vérification et PDF' },
]

// ─── État initial ─────────────────────────────────────────────────────────────
const initialData = {
  // Mission
  ref: 'SAGETRIM-2026-',
  demandeur_nom: '',
  demandeur_qualite: '',
  demandeur_adresse: '',
  date_visite: '',
  date_rapport: new Date().toISOString().substring(0, 10),
  objet_mission: 'Estimation en valeur vénale',

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

  // Description
  sdp: '',
  annee_construction: '',
  niveau_etage: '',
  ascenseur: false,
  type_appart: 'F3',
  batiment: '',
  etat_general: 'Bon état d\'usage',
  distribution: ['', '', '', '', ''],

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

  // Conclusion
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

  // Calculer la valeur estimée pour la prévisualisation
  const computeValue = () => {
    const retained = data.dvf_refs.filter(r => r.retenu && r.pm2)
    const pm2s = retained.map(r => parseFloat(r.pm2)).filter(v => v > 0).sort((a,b) => a-b)
    const median = pm2s.length ? pm2s[Math.floor(pm2s.length/2)] : parseFloat(data.pm2_median) || 0
    const sdp = parseFloat(data.sdp) || 0
    return sdp && median ? Math.round(sdp * median / 1000) * 1000 : 0
  }

  // Générer le PDF
  const generer = async () => {
    setLoading(true)
    setError(null)
    setSuccess(false)

    // Construire le texte de valeur
    const valeur = computeValue()
    const params = {
      ...data,
      valeur_retenue_texte: data.valeur_retenue_texte ||
        (valeur ? `${valeur.toLocaleString('fr-FR')}\u202f€` : ''),
      distribution: data.distribution.filter(Boolean),
      dvf_refs: data.dvf_refs.filter(r => r.date || r.localisation).map(r => ({
        ...r,
        surface: parseFloat(r.surface) || 0,
        valeur:  parseFloat(r.valeur)  || 0,
        pm2:     parseFloat(r.pm2)     || 0,
      })),
      pm2_median: parseFloat(data.pm2_median) || 0,
      terrain_m2: parseFloat(data.terrain_m2) || 0,
      sdp:        parseFloat(data.sdp)        || 0,
    }

    try {
      const res = await fetch('/api/generer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }))
        throw new Error(err.error || `Erreur ${res.status}`)
      }

      // Télécharger le PDF
      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      const ref  = data.ref.replace(/\//g, '-')
      const nom  = data.demandeur_nom.split(' ')[0] || 'client'
      a.download = `rapport_expertise_${ref}_${nom}.pdf`
      a.click()
      URL.revokeObjectURL(url)
      setSuccess(true)

    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // ─── Rendu des étapes ───────────────────────────────────────────────────────
  const renderStep = () => {
    switch (step) {
      case 0: return <StepMission data={data} set={set} />
      case 1: return <StepBien data={data} set={set} />
      case 2: return <StepDescription data={data} set={set} setNested={setNested} />
      case 3: return <StepRisques data={data} set={set} />
      case 4: return <StepEvaluation data={data} set={set} setNested={setNested} />
      case 5: return <StepGeneration data={data} set={set} computeValue={computeValue}
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

      {/* Topbar */}
      <div className="topbar">
        <div>
          <div className="topbar-brand">SAGETRIM <span>·</span> ExpertForm</div>
          <div className="topbar-sub">Rapport d'expertise immobilière</div>
        </div>
        <div style={{display:'flex',gap:8,alignItems:'center'}}>
          <span style={{fontSize:11,color:'rgba(255,255,255,.4)'}}>
            {data.ref || 'Nouveau dossier'}
          </span>
        </div>
      </div>

      {/* Layout */}
      <div className="main">

        {/* Stepper */}
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

        {/* Card */}
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
            {step < STEPS.length - 1 ? (
              <button className="btn btn-primary" onClick={() => nav(1)}>
                Suivant →
              </button>
            ) : null}
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
          <option>Estimation en valeur vénale</option>
          <option>Estimation en valeur locative</option>
          <option>Estimation en valeur d'assurance</option>
          <option>Estimation en valeur d'apport</option>
          <option>Estimation en valeur de cession de parts de SCI</option>
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
function StepDescription({ data, set, setNested }) {
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
                 onChange={e => set('annee_construction', e.target.value)}
                 placeholder="1967, 1985…" />
        </Field>
        <Field label="Type appartement" style={{display: data.type_bien==='appartement'?'':'none'}}>
          <select value={data.type_appart} onChange={e => set('type_appart', e.target.value)}>
            {['F1','F2','F3','F4','F5','F6','Studio'].map(t => <option key={t}>{t}</option>)}
          </select>
        </Field>
      </div>

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
                onChange={e => setNested('distribution', i, null, null) ||
                  set('distribution', data.distribution.map((d,j) => j===i ? e.target.value : d))}
                placeholder={`Pièce / élément ${i+1} (ex. 2 chambres, 1 cuisine, terrasse…)`}
                style={{padding:'7px 10px',border:'1px solid var(--border)',
                        borderRadius:'var(--r)',fontSize:13,flex:1}}
              />
            </div>
          ))}
          <button className="btn btn-secondary"
                  style={{fontSize:12,marginTop:4}}
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
                <select value={data.etat_communs || 'Bon'} onChange={e => set('etat_communs', e.target.value)}>
                  <option>Excellent</option>
                  <option>Bon</option>
                  <option>Moyen</option>
                  <option>Dégradé — facteur dépressif</option>
                </select>
              </Field>
            )}
          </div>
        </>
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
// ÉTAPE 4 — RISQUES
// ═══════════════════════════════════════════════════════════════════════════════
function StepRisques({ data, set }) {
  return (
    <div>
      <div className="sec-title">Risques naturels</div>
      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:8,marginBottom:8}}>
        <div style={{border:'1px solid var(--border)',borderRadius:'var(--r)',padding:'10px 12px'}}>
          <div style={{fontSize:11,fontWeight:600,color:'var(--navy)',marginBottom:6}}>Zone sismique</div>
          <select value={data.zone_sismique} onChange={e => set('zone_sismique', e.target.value)}
                  style={{width:'100%',padding:'6px 8px',border:'1px solid var(--border)',
                          borderRadius:'var(--r)',fontSize:13}}>
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
                   onChange={() => set('termites_zone', true)} />
            Zone contaminée
          </label>
          <label style={{display:'flex',alignItems:'center',gap:8,fontSize:13,cursor:'pointer',marginTop:4}}>
            <input type="radio" name="termites" checked={!data.termites_zone}
                   onChange={() => set('termites_zone', false)} />
            Hors zone
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
          ['diag_amiante',  'Diagnostic amiante',          'Obligatoire si construction avant 1997'],
          ['diag_termites', 'Diagnostic termites',         'Obligatoire en zone contaminée'],
          ['diag_elec',     'Diagnostic électricité',      'Obligatoire si installation > 15 ans'],
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
// ÉTAPE 5 — ÉVALUATION
// ═══════════════════════════════════════════════════════════════════════════════
function StepEvaluation({ data, set, setNested }) {
  const retained = data.dvf_refs.filter(r => r.retenu && r.pm2)
  const pm2s = retained.map(r => parseFloat(r.pm2)).filter(v => v > 0).sort((a,b)=>a-b)
  const calcMedian = pm2s.length ? pm2s[Math.floor(pm2s.length/2)] : 0
  const sdp = parseFloat(data.sdp) || 0
  const pm2_used = parseFloat(data.pm2_median) || calcMedian
  const valeur = sdp && pm2_used ? Math.round(sdp * pm2_used / 1000) * 1000 : 0

  const addRef = () => {
    set('dvf_refs', [...data.dvf_refs, { date:'', localisation:'', type:'', surface:'', valeur:'', pm2:'', retenu:true, statut:'Retenue' }])
  }

  const toggleRef = (i, checked) => {
    const refs = data.dvf_refs.map((r,j) => j===i ? {...r, retenu:checked} : r)
    set('dvf_refs', refs)
  }

  return (
    <div>
      <Alert type="info">
        Saisissez les transactions DVF de la zone. Décochez les valeurs aberrantes.
        Le prix médian et la valeur se recalculent automatiquement.
      </Alert>

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
                         onChange={e => toggleRef(i, e.target.checked)} />
                </td>
                {['date','localisation','type','surface','valeur','pm2'].map(f => (
                  <td key={f}>
                    <input value={r[f]} onChange={e => setNested('dvf_refs', i, f, e.target.value)}
                           style={{border:'1px solid var(--border)',borderRadius:4,
                                   padding:'3px 6px',fontSize:11,width:'100%',
                                   textDecoration: !r.retenu?'line-through':'none'}} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <button className="btn btn-secondary" style={{fontSize:12,marginTop:6}} onClick={addRef}>
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
        <Field label="Prix médian retenu (€/m²)"
               hint="Laisser vide = médiane auto">
          <input type="number" value={data.pm2_median}
                 onChange={e => set('pm2_median', e.target.value)}
                 placeholder={calcMedian || '1 176'} />
        </Field>
        {data.type_bien !== 'appartement' && (
          <>
            <Field label="Coût reconstruction (€/m² SDP)"
                   hint="Indice BT01 Guadeloupe 2026">
              <input type="number" value={data.cout_construction_m2}
                     onChange={e => set('cout_construction_m2', e.target.value)} />
            </Field>
            <Field label="Vétusté pondérée (%)">
              <input type="number" value={data.vetuste_taux}
                     onChange={e => set('vetuste_taux', e.target.value)} />
            </Field>
          </>
        )}
      </div>

      {valeur > 0 && (
        <div className="value-box">
          <div>
            <div className="value-box-label">VALEUR ESTIMÉE</div>
            <div className="value-box-amount">{valeur.toLocaleString('fr-FR')} €</div>
            <div className="value-box-range">
              {Math.round(valeur*0.93/1000)*1000} — {Math.round(valeur*1.05/1000)*1000} €
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
// ÉTAPE 6 — GÉNÉRATION
// ═══════════════════════════════════════════════════════════════════════════════
function StepGeneration({ data, set, computeValue, generer, loading, error, success }) {
  const valeur = computeValue()
  const missingDiag = [
    ['diag_amiante','Amiante'],['diag_termites','Termites'],
    ['diag_elec','Électricité'],['diag_dpe','DPE'],
  ].filter(([k]) => !data[k]).map(([,l]) => l)

  return (
    <div>
      {success ? (
        <Alert type="ok">
          ✓ Rapport généré avec succès ! Le PDF a été téléchargé.
        </Alert>
      ) : null}

      {error ? (
        <Alert type="err">
          Erreur de génération : {error}
        </Alert>
      ) : null}

      <div className="sec-title">Récapitulatif du dossier</div>
      <div className="summary-grid">
        <div className="summary-item">
          <div className="summary-item-label">Référence</div>
          <div className="summary-item-value">{data.ref || '—'}</div>
        </div>
        <div className="summary-item">
          <div className="summary-item-label">Date rapport</div>
          <div className="summary-item-value">{data.date_rapport || '—'}</div>
        </div>
        <div className="summary-item">
          <div className="summary-item-label">Demandeur</div>
          <div className="summary-item-value">{data.demandeur_nom || '—'}</div>
        </div>
        <div className="summary-item">
          <div className="summary-item-label">Bien</div>
          <div className="summary-item-value">{data.commune || data.adresse_bien || '—'}</div>
        </div>
        <div className="summary-item">
          <div className="summary-item-label">SDP</div>
          <div className="summary-item-value">
            {data.sdp ? `${data.sdp} m²` : <span style={{color:'var(--alert)'}}>⚠ Non renseignée</span>}
          </div>
        </div>
        <div className="summary-item">
          <div className="summary-item-label">Réf. DVF retenues</div>
          <div className="summary-item-value">{data.dvf_refs.filter(r=>r.retenu).length} / {data.dvf_refs.length}</div>
        </div>
      </div>

      {valeur > 0 && (
        <div className="value-box">
          <div>
            <div className="value-box-label">VALEUR VÉNALE ESTIMÉE</div>
            <div className="value-box-amount">{valeur.toLocaleString('fr-FR')} €</div>
            <div className="value-box-range">
              Fourchette : {(Math.round(valeur*0.93/1000)*1000).toLocaleString('fr-FR')} – {(Math.round(valeur*1.05/1000)*1000).toLocaleString('fr-FR')} €
            </div>
          </div>
        </div>
      )}

      {missingDiag.length > 0 && (
        <Alert type="warn">
          Réserves automatiques — diagnostics manquants : {missingDiag.join(', ')}.
          Ces réserves apparaîtront dans le rapport généré.
        </Alert>
      )}

      <div className="sep" />
      <Field label="Texte de la valeur retenue (pour la conclusion)"
             hint="Optionnel — sera calculé automatiquement si vide">
        <input value={data.valeur_retenue_texte}
               onChange={e => set('valeur_retenue_texte', e.target.value)}
               placeholder={`${(valeur||0).toLocaleString('fr-FR')}\u202f€ (${''} euros)`} />
      </Field>

      <button className="btn-generate" onClick={generer} disabled={loading || !data.demandeur_nom}>
        {loading ? (
          <><span className="spinner" /> Génération du rapport en cours…</>
        ) : (
          <>📄 Générer le rapport PDF</>
        )}
      </button>

      <div style={{marginTop:8,textAlign:'center',fontSize:11,color:'var(--muted)'}}>
        Le PDF SAGETRIM sera téléchargé automatiquement · Conforme Charte TEGoVA
      </div>
    </div>
  )
}
