import { describe, it, expect } from 'vitest'
import { HttpTrialBridgeApi, LocalMockApi } from '../adapter'
import { DEMO_PATIENT_NOTES } from '../../data/demoPatient'

/**
 * Contract-parity test.
 *
 * Proves the backend's /api/trials and /api/extract-facts return byte-for-byte
 * the SAME domain shapes the frontend's LocalMockApi produces. Run against a
 * live backend:
 *
 *   RUN_PARITY=1 PARITY_BASE=http://127.0.0.1:8000/api npm run test -- parity
 *
 * Skipped by default so the normal offline test suite needs no backend.
 */
const RUN = process.env.RUN_PARITY === '1'
const BASE = process.env.PARITY_BASE || 'http://127.0.0.1:8000/api'

describe.skipIf(!RUN)('backend ↔ frontend contract parity', () => {
  const http = new HttpTrialBridgeApi(BASE)
  const local = new LocalMockApi()

  it('getTrials() matches the local mock exactly', async () => {
    const [remote, mock] = await Promise.all([
      http.getTrials(),
      local.getTrials(),
    ])
    expect(remote).toEqual(mock)
  })

  it('extractFacts() matches the local parser for the demo note', async () => {
    const remote = await http.extractFacts(DEMO_PATIENT_NOTES)
    const mock = await local.extractFacts(DEMO_PATIENT_NOTES)
    // Backend uses a different id namespace by design; compare facts + notes.
    expect(remote.facts).toEqual(mock.facts)
    expect(remote.rawNotes).toEqual(mock.rawNotes)
  })
})
