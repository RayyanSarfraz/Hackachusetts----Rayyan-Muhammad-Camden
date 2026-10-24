import type { PatientProfile, Trial } from '../types/domain'
import { DEMO_TRIALS } from '../data/trials'
import { parseNotes } from '../lib/noteParser'

/**
 * API adapter boundary.
 *
 * The demo runs fully offline on local mock data by default. This module is the
 * single seam a real backend plugs into. Two implementations are provided:
 *
 *   - LocalMockApi  : offline, deterministic, no network (the default).
 *   - HttpTrialBridgeApi : calls the Django backend over the documented
 *                          endpoints and returns the SAME domain shapes.
 *
 * Which one is active is decided by `VITE_USE_HTTP_API` at build/startup time,
 * so the offline demo keeps working untouched and the HTTP path is opt-in.
 */

export interface TrialBridgeApi {
  /** Return the candidate trials. */
  getTrials(): Promise<Trial[]>
  /**
   * Extract structured facts from free-text notes. The local implementation
   * uses a deterministic parser; the HTTP implementation calls the backend,
   * which runs the same deterministic extraction server-side.
   */
  extractFacts(notes: string): Promise<PatientProfile>
}

/** Local, offline implementation backed by mock JSON + the deterministic parser. */
export class LocalMockApi implements TrialBridgeApi {
  async getTrials(): Promise<Trial[]> {
    // Deep clone so callers never mutate the shared mock source.
    return structuredClone(DEMO_TRIALS)
  }

  async extractFacts(notes: string): Promise<PatientProfile> {
    return parseNotes(notes)
  }
}

/**
 * HTTP implementation against the Django backend.
 *
 * Endpoints (see api/apps/integration/views.py + config/urls.py):
 *
 *   GET  /api/trials
 *        -> Trial[]  (unassessed; criteria carry dependsOn/kind/estimatedEffort)
 *
 *   POST /api/extract-facts   { notes: string }
 *        -> PatientProfile    (facts keyed by FactKey; unknown facts = null)
 *
 * The Vite dev server proxies /api to the backend (see vite.config.ts), so the
 * default base path is same-origin "/api". Override with VITE_API_BASE if the
 * backend lives elsewhere.
 *
 * Both responses already match src/types/domain.ts, so no field remapping is
 * needed; the backend is a faithful port of the local mock + parser. The
 * frontend's own assessor / ranking / Next Best Question engine then run on
 * this data exactly as they do offline.
 */
export class HttpTrialBridgeApi implements TrialBridgeApi {
  private readonly base: string

  constructor(base: string = import.meta.env.VITE_API_BASE || '/api') {
    // Normalize: no trailing slash on the base.
    this.base = base.replace(/\/$/, '')
  }

  async getTrials(): Promise<Trial[]> {
    const res = await fetch(`${this.base}/trials/`, {
      headers: { Accept: 'application/json' },
    })
    if (!res.ok) {
      throw new Error(`getTrials failed: ${res.status} ${res.statusText}`)
    }
    return (await res.json()) as Trial[]
  }

  async extractFacts(notes: string): Promise<PatientProfile> {
    const res = await fetch(`${this.base}/extract-facts/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({ notes }),
    })
    if (!res.ok) {
      throw new Error(`extractFacts failed: ${res.status} ${res.statusText}`)
    }
    return (await res.json()) as PatientProfile
  }
}

/**
 * The active API.
 *
 * Defaults to the offline mock so the demo always works with zero backend.
 * Set VITE_USE_HTTP_API=true to route through the Django backend instead.
 */
const useHttp = import.meta.env.VITE_USE_HTTP_API === 'true'

export const api: TrialBridgeApi = useHttp
  ? new HttpTrialBridgeApi()
  : new LocalMockApi()
