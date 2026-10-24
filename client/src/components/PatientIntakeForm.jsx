import { useRef, useState } from 'react'
import { postIntake, findTrials } from '../api/engine'
import { FICTIONAL_DEMO_PATIENT } from './demoPreset'

const SEX_OPTIONS = [
  { value: '', label: 'Select (optional)' },
  { value: 'female', label: 'Female' },
  { value: 'male', label: 'Male' },
  { value: 'intersex', label: 'Intersex' },
  { value: 'unknown', label: 'Unknown / Prefer not to specify' },
]

const EMPTY_FORM = {
  age: '',
  primary_condition: '',
  city: '',
  state: 'MA',
  sex_for_eligibility: '',
  medical_note: '',
  medications: '',
  other_conditions: '',
  symptoms: '',
  previous_treatments: '',
  lab_results: '',
}

// Split a free-text, line/comma separated field into a clean string list.
function toList(text) {
  if (!text) return []
  return text
    .split(/[\n,]+/)
    .map((s) => s.trim())
    .filter(Boolean)
}

// Parse "Naltrexone 50 mg (current)" -> { name, dosage, status }. Only the name
// is required; the rest stay null when not provided (never fabricated).
function toMedications(text) {
  return toList(text).map((line) => {
    const status = /\(([^)]+)\)/.exec(line)?.[1]?.trim() || null
    const withoutStatus = line.replace(/\([^)]*\)/, '').trim()
    const dosage = /(\d+\s?\w+.*)$/.exec(withoutStatus)?.[0]?.trim() || null
    const name = (dosage ? withoutStatus.replace(dosage, '') : withoutStatus).trim()
    return { name: name || withoutStatus, dosage, status }
  })
}

function buildPatientPayload(form) {
  return {
    age: form.age === '' ? null : Number(form.age),
    primary_condition: form.primary_condition.trim(),
    sex_for_eligibility: form.sex_for_eligibility || null,
    location: { state: form.state.trim() || 'MA', city: form.city.trim() },
    conditions: toList(form.other_conditions),
    symptoms: toList(form.symptoms),
    medications: toMedications(form.medications),
    previous_treatments: toList(form.previous_treatments),
    lab_results: toList(form.lab_results),
    medical_note: form.medical_note.trim(),
  }
}

function factLabel(fact) {
  const v = fact?.value
  if (v && typeof v === 'object') {
    return [v.name, v.dosage, v.status].filter(Boolean).join(' · ')
  }
  return String(v ?? '')
}

export default function PatientIntakeForm() {
  const [form, setForm] = useState(EMPTY_FORM)
  const [showAdditional, setShowAdditional] = useState(false)
  const [errors, setErrors] = useState({})

  const [analyzing, setAnalyzing] = useState(false)
  const [searching, setSearching] = useState(false)
  const [apiError, setApiError] = useState(null)

  const [profile, setProfile] = useState(null)
  const [modelAvailable, setModelAvailable] = useState(null)
  const [trials, setTrials] = useState(null)

  const abortRef = useRef(null)

  const update = (field) => (e) =>
    setForm((f) => ({ ...f, [field]: e.target.value }))

  function validate() {
    const next = {}
    if (!form.primary_condition.trim() && !form.medical_note.trim()) {
      next.primary_condition =
        'Enter a primary condition or describe the history in the note.'
    }
    if (form.age !== '' && (Number(form.age) < 0 || Number(form.age) > 150)) {
      next.age = 'Enter an age between 0 and 150.'
    }
    setErrors(next)
    return Object.keys(next).length === 0
  }

  async function handleAnalyze(e) {
    e.preventDefault()
    setApiError(null)
    setTrials(null)
    if (!validate()) return

    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setAnalyzing(true)
    try {
      const data = await postIntake(buildPatientPayload(form), {
        signal: controller.signal,
      })
      setProfile(data.profile)
      setModelAvailable(data.model_available)
    } catch (err) {
      if (err?.type !== 'canceled') setApiError(err?.message || 'Analysis failed.')
    } finally {
      setAnalyzing(false)
    }
  }

  async function handleFindTrials() {
    if (!profile) return
    setApiError(null)
    setSearching(true)
    try {
      const data = await findTrials(profile)
      setTrials(data)
    } catch (err) {
      if (err?.type !== 'canceled') setApiError(err?.message || 'Trial search failed.')
    } finally {
      setSearching(false)
    }
  }

  function loadDemo() {
    setForm({ ...EMPTY_FORM, ...FICTIONAL_DEMO_PATIENT })
    setShowAdditional(true)
    setProfile(null)
    setTrials(null)
    setApiError(null)
    setErrors({})
  }

  // Let the user correct an extracted/added fact before searching.
  function editFact(listName, index, newLabel) {
    setProfile((p) => {
      const list = [...(p[listName] || [])]
      const fact = { ...list[index] }
      if (fact.value && typeof fact.value === 'object') {
        fact.value = { ...fact.value, name: newLabel }
      } else {
        fact.value = newLabel
      }
      list[index] = fact
      return { ...p, [listName]: list }
    })
  }

  function removeFact(listName, index) {
    setProfile((p) => {
      const list = [...(p[listName] || [])]
      list.splice(index, 1)
      return { ...p, [listName]: list }
    })
  }

  return (
    <div className="intake">
      <header className="intake__head">
        <p className="intake__kicker">Clinical-Trial Prescreening Copilot</p>
        <h1 className="intake__title">Patient intake</h1>
        <p className="intake__lede">
          Share what you know. Fields can stay blank — we never guess missing
          medical details.
        </p>
        <p className="intake__disclaimer">
          Hackathon demonstration. Not for clinical use.
        </p>
      </header>

      <form className="intake__form" onSubmit={handleAnalyze} noValidate>
        <fieldset className="panel">
          <legend className="panel__legend">Basic information</legend>

          <div className="grid">
            <label className="field">
              <span className="field__label">Age</span>
              <input
                type="number"
                min="0"
                max="150"
                value={form.age}
                onChange={update('age')}
                placeholder="Optional"
                aria-invalid={Boolean(errors.age)}
              />
              {errors.age && <span className="field__error">{errors.age}</span>}
            </label>

            <label className="field field--wide">
              <span className="field__label">Primary medical condition</span>
              <input
                type="text"
                value={form.primary_condition}
                onChange={update('primary_condition')}
                placeholder="e.g. Alcohol Use Disorder"
                aria-invalid={Boolean(errors.primary_condition)}
              />
              {errors.primary_condition && (
                <span className="field__error">{errors.primary_condition}</span>
              )}
            </label>

            <label className="field">
              <span className="field__label">City</span>
              <input
                type="text"
                value={form.city}
                onChange={update('city')}
                placeholder="Optional"
              />
            </label>

            <label className="field">
              <span className="field__label">State</span>
              <input type="text" value={form.state} onChange={update('state')} />
            </label>

            <label className="field field--wide">
              <span className="field__label">Sex for eligibility screening</span>
              <select
                value={form.sex_for_eligibility}
                onChange={update('sex_for_eligibility')}
              >
                {SEX_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </fieldset>

        <fieldset className="panel">
          <legend className="panel__legend">Medical history</legend>
          <label className="field">
            <span className="field__label">Medical history / clinical notes</span>
            <textarea
              rows={6}
              value={form.medical_note}
              onChange={update('medical_note')}
              placeholder="Free-text history. We extract structured facts from this when the model is available."
            />
          </label>

          <button
            type="button"
            className="disclosure"
            aria-expanded={showAdditional}
            onClick={() => setShowAdditional((v) => !v)}
          >
            {showAdditional ? 'Hide' : 'Show'} additional medical information
          </button>

          {showAdditional && (
            <div className="grid grid--single">
              <label className="field">
                <span className="field__label">Current medications</span>
                <textarea
                  rows={2}
                  value={form.medications}
                  onChange={update('medications')}
                  placeholder="One per line, e.g. Naltrexone 50 mg (current)"
                />
              </label>
              <label className="field">
                <span className="field__label">Other diagnosed conditions</span>
                <textarea rows={2} value={form.other_conditions} onChange={update('other_conditions')} />
              </label>
              <label className="field">
                <span className="field__label">Symptoms</span>
                <textarea rows={2} value={form.symptoms} onChange={update('symptoms')} />
              </label>
              <label className="field">
                <span className="field__label">Previous treatments</span>
                <textarea rows={2} value={form.previous_treatments} onChange={update('previous_treatments')} />
              </label>
              <label className="field">
                <span className="field__label">Laboratory results</span>
                <textarea rows={2} value={form.lab_results} onChange={update('lab_results')} />
              </label>
            </div>
          )}
        </fieldset>

        {apiError && <p className="banner banner--error">{apiError}</p>}

        <div className="actions">
          <button type="submit" className="btn btn--primary" disabled={analyzing}>
            {analyzing ? 'Analyzing…' : 'Analyze medical information'}
          </button>
          <button
            type="button"
            className="btn btn--ghost"
            onClick={handleFindTrials}
            disabled={!profile || searching}
            title={profile ? '' : 'Analyze first to enable trial search'}
          >
            {searching ? 'Searching…' : 'Find clinical trials'}
          </button>
          <button type="button" className="btn btn--link" onClick={loadDemo}>
            Load fictional example
          </button>
        </div>
      </form>

      {profile && (
        <section className="review" aria-live="polite">
          <h2 className="review__title">Review extracted information</h2>
          <p className="review__note">
            {modelAvailable
              ? 'The model extracted additional facts from the note. Correct anything before searching.'
              : 'The extraction model is unavailable, so only what you entered is shown. Nothing was inferred.'}
          </p>

          {profile.extraction_conflicts?.length > 0 && (
            <p className="banner banner--warn">
              {profile.extraction_conflicts.length} value(s) you entered differ
              from what the note suggests. Your values were kept.
            </p>
          )}

          <div className="review__grid">
            <FactList title="Conditions" listName="conditions" profile={profile} onEdit={editFact} onRemove={removeFact} />
            <FactList title="Symptoms" listName="symptoms" profile={profile} onEdit={editFact} onRemove={removeFact} />
            <FactList title="Medications" listName="medications" profile={profile} onEdit={editFact} onRemove={removeFact} />
            <FactList title="Previous treatments" listName="previous_treatments" profile={profile} onEdit={editFact} onRemove={removeFact} />
            <FactList title="Lab results" listName="lab_results" profile={profile} onEdit={editFact} onRemove={removeFact} />
          </div>
        </section>
      )}

      {trials && (
        <section className="results" aria-live="polite">
          <h2 className="review__title">Clinical trials</h2>
          {trials.retrieval_available ? (
            trials.results.length ? (
              <ol className="trial-list">
                {trials.results.map((t, i) => (
                  <li key={t.trial_id || i} className="trial">
                    <span className="trial__id">{t.trial_id}</span>
                    <span className="trial__meta">{t.metadata?.title || ''}</span>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="banner">No matching trials were found.</p>
            )
          ) : (
            <p className="banner banner--warn">
              {trials.detail ||
                'Trial retrieval is unavailable. No results can be shown yet.'}
            </p>
          )}
        </section>
      )}
    </div>
  )
}

function FactList({ title, listName, profile, onEdit, onRemove }) {
  const list = profile[listName] || []
  return (
    <div className="factgroup">
      <h3 className="factgroup__title">{title}</h3>
      {list.length === 0 ? (
        <p className="factgroup__empty">None</p>
      ) : (
        <ul className="factgroup__list">
          {list.map((fact, i) => (
            <li key={`${listName}-${i}`} className="factrow">
              <input
                className="factrow__input"
                value={factLabel(fact)}
                onChange={(e) => onEdit(listName, i, e.target.value)}
              />
              <span className={`tag tag--${fact.source}`}>{fact.source}</span>
              <button
                type="button"
                className="factrow__remove"
                aria-label={`Remove ${factLabel(fact)}`}
                onClick={() => onRemove(listName, i)}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
