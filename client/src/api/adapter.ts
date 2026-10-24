import type { PatientProfile, Trial } from '../types/domain'
import { DEMO_TRIALS } from '../data/trials'
import { parseNotes } from '../lib/noteParser'

/**
 * API adapter boundary.
 *
 * The demo runs fully offline on local mock data. This module is the single
 * seam a real backend would plug into later. It makes NO network requests and
 * assumes NO endpoints exist. When a backend is ready, implement
 * `HttpTrialBridgeApi` against the documented endpoints and swap `api` below.
 */

export interface TrialBridgeApi {
  /** Return the candidate trials. */
  getTrials(): Promise<Trial[]>
  /**
   * Extract structured facts from free-text notes. The local implementation
   * uses a deterministic parser; a backend could use a verified NLP service.
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

/*
 * Future backend integration points (not implemented — do not call):
 *
 *   GET  /api/trials
 *        -> Trial[]  (must match src/types/domain.ts shapes)
 *
 *   POST /api/extract-facts   { notes: string }
 *        -> PatientProfile    (facts keyed by FactKey; unknown facts = null)
 *
 * A real implementation would live in an `HttpTrialBridgeApi implements
 * TrialBridgeApi` class using fetch('/api/...') (the Vite dev proxy already
 * forwards /api to the Django backend). Note extraction must remain honest:
 * the backend should not fabricate facts that are not in the record.
 */

/** The active API. Swap this to an HTTP implementation when a backend exists. */
export const api: TrialBridgeApi = new LocalMockApi()
