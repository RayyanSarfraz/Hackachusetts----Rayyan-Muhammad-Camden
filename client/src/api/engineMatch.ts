/**
 * Engine match API — the REAL backend path.
 *
 * Calls POST /api/engine/match/ (public), which runs the engine's extract +
 * normalize + retrieve/match over the real trial dataset and returns matched
 * trials plus clarifying questions for any matcher-relevant gaps. Answers from
 * the generated form can be sent back to refine the match.
 *
 * This is additive and independent of the offline demo (src/api/adapter.ts):
 * the existing mock flow is untouched.
 */

const BASE = (import.meta.env.VITE_API_BASE || '/api').replace(/\/$/, '')

export interface MatchQuestion {
  question_id: string
  required_fact_key: string
  display_question: string
  answer_type: 'yes_no' | 'yes_no_unknown' | 'text' | 'number'
  related_trial_ids: string[]
  source_criterion_ids: string[]
}

export interface MatchedTrial {
  trial_id: string | null
  distance: number | null
  metadata: Record<string, unknown>
  trial: {
    nct_id: string
    title: string
    phase: string
    conditions: string[]
    status: string
    city: string
  } | null
}

export interface MatchResponse {
  profile: Record<string, unknown>
  model_available: boolean
  query: string
  retrieval_available: boolean
  matching_available: boolean
  results: MatchedTrial[]
  questions: MatchQuestion[]
  detail: string | null
}

export interface PatientInput {
  age?: number | null
  primary_condition?: string
  sex_for_eligibility?: string | null
  location?: { state?: string; city?: string }
  medical_note?: string
}

/**
 * Run a match. Pass `answers` (fact_key -> value) to refine a previous result.
 */
export async function matchTrials(
  patient: PatientInput,
  answers: Record<string, string | number> = {},
): Promise<MatchResponse> {
  const res = await fetch(`${BASE}/engine/match/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ patient, answers }),
  })
  if (!res.ok) {
    throw new Error(`match failed: ${res.status} ${res.statusText}`)
  }
  return (await res.json()) as MatchResponse
}
