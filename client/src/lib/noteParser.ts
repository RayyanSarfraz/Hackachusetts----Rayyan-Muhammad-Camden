import type { FactKey, PatientFact, PatientProfile } from '../types/domain'
import { FACT_DEFINITIONS } from '../data/demoPatient'

/**
 * Deterministic, local note parser.
 *
 * This is NOT an LLM and makes no network calls. It extracts a small set of
 * explicitly supported facts using simple, transparent pattern matching.
 * Anything not clearly stated is left Unknown (value `null`). Missing
 * information is never treated as a negative finding.
 */

function makeUnknownFact(key: FactKey, label: string): PatientFact {
  return { key, label, value: null, known: false, source: 'parsed' }
}

/** Extract age like "54-year-old" or "age 54" or "54 yo". */
function parseAge(notes: string): { value: number; evidence: string } | null {
  const patterns: RegExp[] = [
    /(\d{1,3})[\s-]*year[\s-]*old/i,
    /\bage[:\s]+(\d{1,3})\b/i,
    /\b(\d{1,3})\s*(?:yo|y\/o|yrs?)\b/i,
  ]
  for (const re of patterns) {
    const m = notes.match(re)
    if (m) {
      const age = Number(m[1])
      if (age > 0 && age < 120) {
        return { value: age, evidence: m[0].trim() }
      }
    }
  }
  return null
}

/** Only recognizes NSCLC — the demo's supported condition. */
function parseCondition(
  notes: string,
): { value: string; evidence: string } | null {
  const re = /non[\s-]?small[\s-]?cell lung cancer|\bNSCLC\b/i
  const m = notes.match(re)
  if (m) {
    return { value: 'Non-small cell lung cancer', evidence: m[0].trim() }
  }
  return null
}

/** Extract a "City, ST" style location. */
function parseLocation(
  notes: string,
): { value: string; evidence: string } | null {
  // Prefer an explicit "Location: City, ST" line.
  const labeled = notes.match(/location[:\s]+([A-Za-z.\s]+,\s*[A-Z]{2})\b/i)
  if (labeled) {
    return { value: labeled[1].trim(), evidence: labeled[0].trim() }
  }
  // Otherwise look for a bare "City, ST" token.
  const bare = notes.match(/\b([A-Z][a-zA-Z.]+(?:\s[A-Z][a-zA-Z.]+)*,\s*[A-Z]{2})\b/)
  if (bare) {
    return { value: bare[1].trim(), evidence: bare[1].trim() }
  }
  return null
}

/** Recognize documented previous treatment (chemotherapy/radiation/surgery). */
function parsePreviousTreatment(
  notes: string,
): { value: string; evidence: string } | null {
  const re = /\b(chemotherapy|chemo|radiation|radiotherapy|immunotherapy|surgery|resection)\b/i
  const m = notes.match(re)
  if (!m) return null
  const token = m[1].toLowerCase()
  const normalized =
    token === 'chemo' ? 'Chemotherapy' : token[0].toUpperCase() + token.slice(1)
  return { value: normalized, evidence: m[0].trim() }
}

/**
 * EGFR is deliberately conservative: it is only extracted when an actual
 * positive/negative result is stated. Phrases like "not documented" leave it
 * Unknown (returns null) rather than guessing.
 */
function parseEgfr(
  notes: string,
): { value: string; evidence: string } | null {
  // Explicitly undocumented → stay Unknown.
  if (/egfr[^.\n]*\b(not documented|unknown|pending|not available|no result)\b/i.test(notes)) {
    return null
  }
  if (/egfr[^.\n]*\b(positive|mutation|mutant|detected|activating)\b/i.test(notes)) {
    const m = notes.match(/egfr[^.\n]*\b(positive|mutation|mutant|detected|activating)\b/i)
    return { value: 'positive', evidence: m ? m[0].trim() : 'EGFR positive' }
  }
  if (/egfr[^.\n]*\b(negative|wild[\s-]?type|not detected|wildtype)\b/i.test(notes)) {
    const m = notes.match(/egfr[^.\n]*\b(negative|wild[\s-]?type|not detected|wildtype)\b/i)
    return { value: 'negative', evidence: m ? m[0].trim() : 'EGFR negative' }
  }
  return null
}

/** Extract a documented cancer stage only when clearly stated. */
function parseStage(
  notes: string,
): { value: string; evidence: string } | null {
  if (/stage[^.\n]*\b(not documented|unknown|pending|not available)\b/i.test(notes)) {
    return null
  }
  const m = notes.match(/\bstage\s+(IV|III|II|I|4|3|2|1)\b/i)
  if (m) {
    const roman = normalizeStage(m[1])
    return { value: roman, evidence: m[0].trim() }
  }
  return null
}

function normalizeStage(raw: string): string {
  const map: Record<string, string> = {
    '1': 'I',
    '2': 'II',
    '3': 'III',
    '4': 'IV',
  }
  const upper = raw.toUpperCase()
  return map[upper] ?? upper
}

/** Extract documented ECOG performance status only when clearly stated. */
function parseEcog(
  notes: string,
): { value: number; evidence: string } | null {
  if (/ecog[^.\n]*\b(not documented|unknown|pending|not available)\b/i.test(notes)) {
    return null
  }
  const m = notes.match(/ecog[^.\n]*?\b([0-4])\b/i)
  if (m) {
    return { value: Number(m[1]), evidence: m[0].trim() }
  }
  return null
}

const PARSERS: Record<
  FactKey,
  (notes: string) => { value: string | number; evidence: string } | null
> = {
  age: parseAge,
  condition: parseCondition,
  location: parseLocation,
  previousTreatment: parsePreviousTreatment,
  egfrStatus: parseEgfr,
  cancerStage: parseStage,
  ecogStatus: parseEcog,
}

/**
 * Parse free-text notes into a structured patient profile. Everything is
 * deterministic and local. Unsupported or undocumented facts stay Unknown.
 */
export function parseNotes(notes: string, id = 'patient-local'): PatientProfile {
  const facts = {} as PatientProfile['facts']

  for (const def of FACT_DEFINITIONS) {
    const base = makeUnknownFact(def.key, def.label)
    const result = PARSERS[def.key](notes)
    if (result) {
      facts[def.key] = {
        ...base,
        value: result.value,
        known: true,
        evidence: result.evidence,
      }
    } else {
      facts[def.key] = base
    }
  }

  return { id, facts, rawNotes: notes }
}

/** Build an empty (all-Unknown) profile. */
export function emptyProfile(id = 'patient-local'): PatientProfile {
  const facts = {} as PatientProfile['facts']
  for (const def of FACT_DEFINITIONS) {
    facts[def.key] = makeUnknownFact(def.key, def.label)
  }
  return { id, facts, rawNotes: '' }
}
