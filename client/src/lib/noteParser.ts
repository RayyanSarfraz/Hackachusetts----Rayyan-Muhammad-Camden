import type { FactKey, PatientFact, PatientProfile } from '../types/domain'
import { FACT_DEFINITIONS } from '../data/facts'

/**
 * Deterministic, local record parser.
 *
 * This is NOT an LLM and makes no network calls. It extracts a small set of
 * explicitly supported facts from the normalized plain text of a patient's
 * uploaded records using simple, transparent pattern matching.
 *
 * Anything not clearly stated is left Unknown (value `null`). Missing
 * information is never treated as a negative finding.
 *
 * Values can be a single string/number or a list of strings (for medications,
 * allergies and prior treatments).
 */

type ParsedValue = string | number | string[]
type ParseResult = { value: ParsedValue; evidence: string } | null

function makeUnknownFact(key: FactKey, label: string): PatientFact {
  return { key, label, value: null, known: false, source: 'parsed' }
}

/** Extract age like "54-year-old", "age 54", "54 yo", or "DOB" is ignored. */
function parseAge(text: string): ParseResult {
  const patterns: RegExp[] = [
    /(\d{1,3})[\s-]*year[\s-]*old/i,
    /\bage[:\s]+(\d{1,3})\b/i,
    /\b(\d{1,3})\s*(?:yo|y\/o|yrs?)\b/i,
  ]
  for (const re of patterns) {
    const m = text.match(re)
    if (m) {
      const age = Number(m[1])
      if (age > 0 && age < 120) return { value: age, evidence: m[0].trim() }
    }
  }
  return null
}

/** Extract sex / sex assigned at birth. */
function parseSex(text: string): ParseResult {
  const labeled = text.match(/\b(?:sex|gender)[:\s]+(male|female|m|f)\b/i)
  if (labeled) {
    const v = labeled[1].toLowerCase()
    return { value: v === 'm' ? 'male' : v === 'f' ? 'female' : v, evidence: labeled[0].trim() }
  }
  const bare = text.match(/\b(\d{1,3})[\s-]*year[\s-]*old\s+(male|female|man|woman)\b/i)
  if (bare) {
    const v = /man|male/i.test(bare[2]) ? 'male' : 'female'
    return { value: v, evidence: bare[0].trim() }
  }
  return null
}

/**
 * Extract the primary condition / diagnosis. Recognizes an explicit
 * "Diagnosis:" / "Condition:" line, or a known set of common condition names.
 */
function parseCondition(text: string): ParseResult {
  const labeled = text.match(/\b(?:diagnosis|condition|dx)[:\s]+([^.\n;]+)/i)
  if (labeled) {
    const value = labeled[1].trim().replace(/\s+/g, ' ')
    if (value.length > 1) return { value: titleCaseCondition(value), evidence: labeled[0].trim() }
  }
  // Fall back to recognizing a few well-known condition names anywhere.
  const known: Array<[RegExp, string]> = [
    [/non[\s-]?small[\s-]?cell lung cancer|\bNSCLC\b/i, 'Non-small cell lung cancer'],
    [/small[\s-]?cell lung cancer|\bSCLC\b/i, 'Small cell lung cancer'],
    [/breast cancer/i, 'Breast cancer'],
    [/colorectal cancer|colon cancer/i, 'Colorectal cancer'],
    [/prostate cancer/i, 'Prostate cancer'],
    [/melanoma/i, 'Melanoma'],
    [/type 2 diabetes|type ii diabetes|\bT2DM\b/i, 'Type 2 diabetes'],
    [/rheumatoid arthritis/i, 'Rheumatoid arthritis'],
    [/multiple sclerosis/i, 'Multiple sclerosis'],
    [/parkinson'?s disease/i, "Parkinson's disease"],
    [/alzheimer'?s disease/i, "Alzheimer's disease"],
  ]
  for (const [re, label] of known) {
    const m = text.match(re)
    if (m) return { value: label, evidence: m[0].trim() }
  }
  return null
}

function titleCaseCondition(s: string): string {
  // Leave known acronyms alone; otherwise capitalize the first letter.
  return s.charAt(0).toUpperCase() + s.slice(1)
}

/** Extract a "City, ST" style location. */
function parseLocation(text: string): ParseResult {
  const labeled = text.match(/location[:\s]+([A-Za-z.\s]+,\s*[A-Z]{2})\b/i)
  if (labeled) return { value: labeled[1].trim(), evidence: labeled[0].trim() }
  const bare = text.match(/\b([A-Z][a-zA-Z.]+(?:\s[A-Z][a-zA-Z.]+)*,\s*[A-Z]{2})\b/)
  if (bare) return { value: bare[1].trim(), evidence: bare[1].trim() }
  return null
}

/**
 * Extract a list of current medications. Recognizes every "Medications:" /
 * "Current medications:" / "Meds:" / "Medication:" line (normalized FHIR/CSV
 * output emits one per drug) and merges their items into a de-duplicated list.
 */
function parseMedications(text: string): ParseResult {
  return collectLabeledList(
    text,
    /\b(?:current medications?|medications?|meds)[:\s]+([^\n]+)/gi,
  )
}

/** Extract a list of allergies, or recognize an explicit "no known allergies". */
function parseAllergies(text: string): ParseResult {
  if (/\b(?:no known (?:drug )?allergies|NKDA|NKA)\b/i.test(text)) {
    const m = text.match(/\b(?:no known (?:drug )?allergies|NKDA|NKA)\b/i)
    return { value: ['No known allergies'], evidence: m ? m[0].trim() : 'NKDA' }
  }
  return collectLabeledList(text, /\ballergies?[:\s]+([^\n]+)/gi)
}

/**
 * Collect the items from every line matching a global labeled-list pattern,
 * merging and de-duplicating them. Returns null if nothing is found.
 */
function collectLabeledList(text: string, re: RegExp): ParseResult {
  const items: string[] = []
  let firstEvidence = ''
  for (const m of text.matchAll(re)) {
    if (!firstEvidence) firstEvidence = m[0].trim()
    for (const item of splitList(m[1])) {
      if (!items.some((x) => x.toLowerCase() === item.toLowerCase())) items.push(item)
    }
  }
  if (items.length === 0) return null
  return { value: items, evidence: firstEvidence }
}

/** Extract documented prior treatments / procedures. */
function parsePriorTreatments(text: string): ParseResult {
  const labeled = text.match(
    /\b(?:treatment history|prior treatments?|past (?:medical|surgical) history|prior therapy)[:\s]+([^\n]+)/i,
  )
  if (labeled) {
    const list = splitList(labeled[1])
    if (list.length > 0) return { value: list, evidence: labeled[0].trim() }
  }
  // Otherwise scan for any recognized treatment keywords.
  const found: string[] = []
  const keywords: Array<[RegExp, string]> = [
    [/chemotherapy|chemo\b/i, 'Chemotherapy'],
    [/radiation|radiotherapy/i, 'Radiation'],
    [/immunotherapy/i, 'Immunotherapy'],
    [/\bsurgery\b|resection/i, 'Surgery'],
    [/targeted therapy/i, 'Targeted therapy'],
  ]
  let evidence = ''
  for (const [re, label] of keywords) {
    const m = text.match(re)
    if (m && !found.includes(label)) {
      found.push(label)
      if (!evidence) evidence = m[0].trim()
    }
  }
  if (found.length === 0) return null
  return { value: found, evidence }
}

/**
 * Extract biomarker / genetic marker status as a list. Generalizes the previous
 * EGFR-only logic: recognizes every named biomarker with a positive/negative-
 * style result. Conservative — a marker explicitly "not documented" stays
 * Unknown (it is omitted from the list rather than guessed).
 */
function parseBiomarkers(text: string): ParseResult {
  const markers = ['EGFR', 'ALK', 'ROS1', 'KRAS', 'BRAF', 'HER2', 'PD-L1', 'BRCA', 'MSI']
  const found: string[] = []
  let firstEvidence = ''

  for (const marker of markers) {
    const undoc = new RegExp(
      `${marker}[^.\\n]*\\b(not documented|unknown|pending|not available|no result)\\b`,
      'i',
    )
    if (undoc.test(text)) continue // explicitly undocumented → stay Unknown for this marker
    const pos = new RegExp(
      `${marker}[^.\\n]*\\b(positive|mutation|mutant|detected|activating|amplified|high)\\b`,
      'i',
    )
    const neg = new RegExp(
      `${marker}[^.\\n]*\\b(negative|wild[\\s-]?type|not detected|wildtype|absent|low)\\b`,
      'i',
    )
    const pm = text.match(pos)
    if (pm) {
      found.push(`${marker} positive`)
      if (!firstEvidence) firstEvidence = pm[0].trim()
      continue
    }
    const nm = text.match(neg)
    if (nm) {
      found.push(`${marker} negative`)
      if (!firstEvidence) firstEvidence = nm[0].trim()
    }
  }

  if (found.length === 0) return null
  return { value: found, evidence: firstEvidence }
}

/** Extract a documented disease stage only when clearly stated. */
function parseDiseaseStage(text: string): ParseResult {
  if (/stage[^.\n]*\b(not documented|unknown|pending|not available)\b/i.test(text)) {
    return null
  }
  const m = text.match(/\bstage\s+(IV|III|II|I|4|3|2|1)\b/i)
  if (m) return { value: `Stage ${normalizeStage(m[1])}`, evidence: m[0].trim() }
  return null
}

function normalizeStage(raw: string): string {
  const map: Record<string, string> = { '1': 'I', '2': 'II', '3': 'III', '4': 'IV' }
  const upper = raw.toUpperCase()
  return map[upper] ?? upper
}

/** Extract documented ECOG performance status only when clearly stated. */
function parsePerformanceStatus(text: string): ParseResult {
  if (/ecog[^.\n]*\b(not documented|unknown|pending|not available)\b/i.test(text)) {
    return null
  }
  const m = text.match(/ecog[^.\n]*?\b([0-4])\b/i)
  if (m) return { value: Number(m[1]), evidence: m[0].trim() }
  return null
}

/** Split a comma / semicolon / "and" separated list into clean items. */
function splitList(raw: string): string[] {
  return raw
    .split(/[,;]|\band\b/i)
    .map((s) => s.trim().replace(/\.$/, ''))
    .filter((s) => s.length > 0 && !/^none$/i.test(s))
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
}

const PARSERS: Record<FactKey, (text: string) => ParseResult> = {
  age: parseAge,
  sex: parseSex,
  primaryCondition: parseCondition,
  location: parseLocation,
  medications: parseMedications,
  allergies: parseAllergies,
  priorTreatments: parsePriorTreatments,
  biomarkers: parseBiomarkers,
  diseaseStage: parseDiseaseStage,
  performanceStatus: parsePerformanceStatus,
}

/**
 * Parse normalized record text into a structured patient profile. Everything
 * is deterministic and local. Unsupported or undocumented facts stay Unknown.
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
