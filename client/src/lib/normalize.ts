import type { IntakeDocumentKind } from '../types/domain'

/**
 * Format normalizers.
 *
 * Every uploaded record — whatever its format — is reduced to clean plain text
 * so it can be (a) fed to the deterministic local parser and (b) sent to the
 * cloud-hosted model as a single consistent text payload. Each normalizer turns
 * one source format into readable, line-oriented text that preserves the
 * meaningful content (labels, values, key/value pairs) without markup noise.
 *
 * All parsing happens locally in the browser. Nothing is uploaded here.
 */

export interface NormalizedDoc {
  /** Clean plain text suitable for the parser and the hosted model. */
  text: string
  /** Lightweight structural info for the UI (page/row/resource counts). */
  meta: {
    rows?: number
    columns?: number
    resources?: number
  }
}

/** Decide a document kind from a file name extension. */
export function kindFromFilename(name: string): IntakeDocumentKind | null {
  const lower = name.toLowerCase()
  if (lower.endsWith('.pdf')) return 'pdf'
  if (lower.endsWith('.txt')) return 'txt'
  if (lower.endsWith('.csv')) return 'csv'
  if (lower.endsWith('.json')) return 'json'
  if (lower.endsWith('.xml')) return 'xml'
  return null
}

// ---------------------------------------------------------------------------
// CSV
// ---------------------------------------------------------------------------

/** Parse a CSV string into a header + rows grid (RFC-4180-ish, handles quotes). */
export function parseCsv(raw: string): { header: string[]; rows: string[][] } {
  const records: string[][] = []
  let field = ''
  let row: string[] = []
  let inQuotes = false

  for (let i = 0; i < raw.length; i++) {
    const c = raw[i]
    if (inQuotes) {
      if (c === '"') {
        if (raw[i + 1] === '"') {
          field += '"'
          i++
        } else {
          inQuotes = false
        }
      } else {
        field += c
      }
    } else if (c === '"') {
      inQuotes = true
    } else if (c === ',') {
      row.push(field)
      field = ''
    } else if (c === '\r') {
      // ignore; handled by \n
    } else if (c === '\n') {
      row.push(field)
      records.push(row)
      row = []
      field = ''
    } else {
      field += c
    }
  }
  // Flush the last field/row if the file didn't end with a newline.
  if (field.length > 0 || row.length > 0) {
    row.push(field)
    records.push(row)
  }

  const nonEmpty = records.filter((r) => r.some((cell) => cell.trim() !== ''))
  if (nonEmpty.length === 0) return { header: [], rows: [] }
  const [header, ...rows] = nonEmpty
  return { header: header.map((h) => h.trim()), rows }
}

/** CSV → text: "header: value" pairs per row, so lab tables read naturally. */
export function csvToText(raw: string): NormalizedDoc {
  const { header, rows } = parseCsv(raw)
  if (header.length === 0) return { text: '', meta: { rows: 0, columns: 0 } }

  const lines = rows.map((row, idx) => {
    const pairs = header
      .map((h, i) => {
        const v = (row[i] ?? '').trim()
        return v ? `${h}: ${v}` : ''
      })
      .filter(Boolean)
    return `Row ${idx + 1} — ${pairs.join('; ')}`
  })

  const text = [`Columns: ${header.join(', ')}`, ...lines].join('\n')
  return { text, meta: { rows: rows.length, columns: header.length } }
}

// ---------------------------------------------------------------------------
// JSON (incl. FHIR bundles from Apple Health / SMART-on-FHIR exports)
// ---------------------------------------------------------------------------

/**
 * JSON → text. Detects FHIR bundles and summarizes the clinically relevant
 * resources (Patient, Condition, Observation, MedicationStatement/Request,
 * AllergyIntolerance, Procedure). Falls back to a flattened key/value dump for
 * arbitrary JSON.
 */
export function jsonToText(raw: string): NormalizedDoc {
  let data: unknown
  try {
    data = JSON.parse(raw)
  } catch (e) {
    throw new Error(
      `Invalid JSON: ${e instanceof Error ? e.message : 'could not parse file'}`,
    )
  }

  const fhir = tryFhirBundle(data)
  if (fhir) return fhir

  // Generic fallback: flatten to "path: value" lines.
  const lines: string[] = []
  flatten(data, '', lines)
  return { text: lines.join('\n'), meta: {} }
}

type FhirResource = Record<string, unknown>

function tryFhirBundle(data: unknown): NormalizedDoc | null {
  if (!isRecord(data)) return null

  // A FHIR bundle has entry[].resource; a single resource has resourceType.
  let resources: FhirResource[] = []
  if (data.resourceType === 'Bundle' && Array.isArray(data.entry)) {
    resources = data.entry
      .map((e) => (isRecord(e) ? (e.resource as FhirResource) : null))
      .filter((r): r is FhirResource => isRecord(r))
  } else if (typeof data.resourceType === 'string') {
    resources = [data as FhirResource]
  } else {
    return null
  }
  if (resources.length === 0) return null

  const lines: string[] = ['FHIR health record export']
  for (const r of resources) {
    const line = summarizeFhirResource(r)
    if (line) lines.push(line)
  }
  return { text: lines.join('\n'), meta: { resources: resources.length } }
}

function summarizeFhirResource(r: FhirResource): string | null {
  const type = String(r.resourceType ?? '')
  switch (type) {
    case 'Patient': {
      const parts: string[] = []
      if (r.gender) parts.push(`Sex: ${String(r.gender)}`)
      if (typeof r.birthDate === 'string') {
        parts.push(`Age: ${ageFromBirthDate(r.birthDate)}`)
      }
      const addr = firstAddress(r)
      if (addr) parts.push(`Location: ${addr}`)
      return parts.length ? `Patient — ${parts.join('; ')}` : null
    }
    case 'Condition': {
      const name = codeableText(r.code)
      return name ? `Diagnosis: ${name}` : null
    }
    case 'Observation': {
      const name = codeableText(r.code)
      const value = observationValue(r)
      if (!name) return null
      return value ? `Observation — ${name}: ${value}` : `Observation — ${name}`
    }
    case 'MedicationStatement':
    case 'MedicationRequest': {
      const name = codeableText(r.medicationCodeableConcept) || medicationRef(r)
      return name ? `Medication: ${name}` : null
    }
    case 'AllergyIntolerance': {
      const name = codeableText(r.code)
      return name ? `Allergy: ${name}` : null
    }
    case 'Procedure': {
      const name = codeableText(r.code)
      return name ? `Procedure / prior treatment: ${name}` : null
    }
    default:
      return null
  }
}

function codeableText(cc: unknown): string {
  if (!isRecord(cc)) return ''
  if (typeof cc.text === 'string' && cc.text.trim()) return cc.text.trim()
  if (Array.isArray(cc.coding)) {
    for (const c of cc.coding) {
      if (isRecord(c) && typeof c.display === 'string' && c.display.trim()) {
        return c.display.trim()
      }
    }
  }
  return ''
}

function observationValue(r: FhirResource): string {
  if (isRecord(r.valueQuantity)) {
    const q = r.valueQuantity
    const v = q.value ?? ''
    const u = q.unit ?? ''
    return `${v} ${u}`.trim()
  }
  if (typeof r.valueString === 'string') return r.valueString
  const cc = codeableText(r.valueCodeableConcept)
  return cc
}

function medicationRef(r: FhirResource): string {
  if (isRecord(r.medicationReference) && typeof r.medicationReference.display === 'string') {
    return r.medicationReference.display
  }
  return ''
}

function firstAddress(r: FhirResource): string {
  if (!Array.isArray(r.address)) return ''
  const a = r.address[0]
  if (!isRecord(a)) return ''
  const city = typeof a.city === 'string' ? a.city : ''
  const state = typeof a.state === 'string' ? a.state : ''
  return [city, state].filter(Boolean).join(', ')
}

function ageFromBirthDate(birthDate: string): number | string {
  const d = new Date(birthDate)
  if (Number.isNaN(d.getTime())) return birthDate
  const now = new Date()
  let age = now.getFullYear() - d.getFullYear()
  const m = now.getMonth() - d.getMonth()
  if (m < 0 || (m === 0 && now.getDate() < d.getDate())) age--
  return age
}

function flatten(value: unknown, path: string, out: string[], depth = 0): void {
  if (depth > 6) return
  if (Array.isArray(value)) {
    value.forEach((v, i) => flatten(v, `${path}[${i}]`, out, depth + 1))
  } else if (isRecord(value)) {
    for (const [k, v] of Object.entries(value)) {
      flatten(v, path ? `${path}.${k}` : k, out, depth + 1)
    }
  } else if (value !== null && value !== undefined) {
    out.push(`${path}: ${String(value)}`)
  }
}

// ---------------------------------------------------------------------------
// XML (Apple Health export.xml, Google Health, generic clinical XML)
// ---------------------------------------------------------------------------

/**
 * XML → text. Uses the browser's DOMParser. Recognizes Apple Health
 * export.xml (Record / Me elements) and otherwise flattens every element's
 * text content and attributes into readable "tag: value" lines.
 */
export function xmlToText(raw: string): NormalizedDoc {
  const parser = new DOMParser()
  const doc = parser.parseFromString(raw, 'application/xml')
  const err = doc.querySelector('parsererror')
  if (err) throw new Error('Invalid XML: the file could not be parsed.')

  const root = doc.documentElement
  if (!root) return { text: '', meta: {} }

  // Apple Health export: <HealthData><Me .../><Record type="..." .../></HealthData>
  if (root.nodeName === 'HealthData') {
    return appleHealthToText(root)
  }

  const lines: string[] = []
  walkXml(root, lines)
  return { text: lines.join('\n'), meta: {} }
}

function appleHealthToText(root: Element): NormalizedDoc {
  const lines: string[] = ['Apple Health export']

  const me = root.querySelector('Me')
  if (me) {
    const sex = me.getAttribute('HKCharacteristicTypeIdentifierBiologicalSex')
    const dob = me.getAttribute('HKCharacteristicTypeIdentifierDateOfBirth')
    if (sex) lines.push(`Sex: ${sex.replace(/^HKBiologicalSex/, '')}`)
    if (dob) lines.push(`Age: ${ageFromBirthDate(dob)}`)
  }

  // Summarize Record elements by type (there can be thousands; aggregate).
  const records = Array.from(root.querySelectorAll('Record'))
  const byType = new Map<string, { count: number; last?: string; unit?: string }>()
  for (const rec of records) {
    const type = (rec.getAttribute('type') ?? 'Unknown').replace(
      /^HKQuantityTypeIdentifier|^HKCategoryTypeIdentifier/,
      '',
    )
    const entry = byType.get(type) ?? { count: 0 }
    entry.count++
    const value = rec.getAttribute('value')
    if (value) entry.last = value
    const unit = rec.getAttribute('unit')
    if (unit) entry.unit = unit
    byType.set(type, entry)
  }
  for (const [type, info] of byType) {
    const latest = info.last ? `, latest ${info.last}${info.unit ? ` ${info.unit}` : ''}` : ''
    lines.push(`${type}: ${info.count} record${info.count === 1 ? '' : 's'}${latest}`)
  }

  const resources = records.length + (me ? 1 : 0)
  return { text: lines.join('\n'), meta: { resources } }
}

function walkXml(el: Element, out: string[], depth = 0): void {
  if (depth > 8) return
  const attrs = Array.from(el.attributes)
    .map((a) => `${a.name}=${a.value}`)
    .join(' ')
  const directText = Array.from(el.childNodes)
    .filter((n) => n.nodeType === Node.TEXT_NODE)
    .map((n) => (n.textContent ?? '').trim())
    .filter(Boolean)
    .join(' ')

  const label = el.nodeName
  if (directText || attrs) {
    out.push(`${label}${attrs ? ` (${attrs})` : ''}${directText ? `: ${directText}` : ''}`)
  }
  for (const child of Array.from(el.children)) {
    walkXml(child, out, depth + 1)
  }
}

// ---------------------------------------------------------------------------

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v)
}
