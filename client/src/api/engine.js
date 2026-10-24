import apiClient from './client'

// Submit a patient object for normalization + (optional) AI extraction.
// Returns { profile_id, profile, model_available }.
export async function postIntake(patient, { signal } = {}) {
  const { data } = await apiClient.post('/engine/intake/', { patient }, { signal })
  return data
}

// Send a normalized profile into the trial-retrieval workflow.
// Returns { query, retrieval_available, matching_available, results, detail }.
export async function findTrials(profile, { signal } = {}) {
  const { data } = await apiClient.post('/engine/trials/', { profile }, { signal })
  return data
}

// Convenience: engine status (public endpoint).
export async function getEngineStatus() {
  const { data } = await apiClient.get('/engine/status/')
  return data
}
