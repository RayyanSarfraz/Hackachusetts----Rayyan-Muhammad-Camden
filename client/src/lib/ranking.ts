import type {
  PatientProfile,
  RankedTrial,
  TravelPreference,
  Trial,
} from '../types/domain'
import { assessTrial } from './assessor'

/**
 * Transparent, deterministic trial ranking.
 *
 * Clinical compatibility and travel accessibility are kept separate:
 *  - clinicalScore is computed purely from eligibility evidence.
 *  - travel preference only affects ordering/accessibility, never the clinical
 *    criterion statuses, and never silently removes clinically relevant trials.
 *
 * The score is NOT a validated medical probability. It is a simple, explainable
 * tally: supported criteria add, potential conflicts subtract, unknown counts
 * as zero (never as supported).
 */

const SUPPORTED_WEIGHT = 2
const CONFLICT_PENALTY = 3

export interface RankingOptions {
  travel: TravelPreference
}

export function rankTrials(
  trials: Trial[],
  profile: PatientProfile,
  options: RankingOptions,
): RankedTrial[] {
  const entries = trials.map((trial) => {
    const summary = assessTrial(trial, profile)
    const clinicalScore =
      summary.supported * SUPPORTED_WEIGHT -
      summary.potentialConflict * CONFLICT_PENALTY
    const withinTravelPreference =
      options.travel.maxMiles === null
        ? true
        : trial.distance.miles <= options.travel.maxMiles
    return { trial, summary, clinicalScore, withinTravelPreference }
  })

  // Sort: trials within the travel preference come first (accessibility),
  // then by clinical score desc, then fewer conflicts, then nearer distance,
  // then trial id for stability. Clinically relevant trials outside the
  // preference are kept (not removed) and simply rank lower.
  entries.sort((a, b) => {
    if (a.withinTravelPreference !== b.withinTravelPreference) {
      return a.withinTravelPreference ? -1 : 1
    }
    if (b.clinicalScore !== a.clinicalScore) return b.clinicalScore - a.clinicalScore
    if (a.summary.potentialConflict !== b.summary.potentialConflict)
      return a.summary.potentialConflict - b.summary.potentialConflict
    if (a.trial.distance.miles !== b.trial.distance.miles)
      return a.trial.distance.miles - b.trial.distance.miles
    return a.trial.id.localeCompare(b.trial.id)
  })

  return entries.map((entry, index) => ({
    ...entry,
    rank: index + 1,
    rankExplanation: buildRankExplanation(entry, options.travel),
  }))
}

function buildRankExplanation(
  entry: Omit<RankedTrial, 'rank' | 'rankExplanation'>,
  travel: TravelPreference,
): string {
  const { summary, withinTravelPreference, trial } = entry
  const parts: string[] = []
  parts.push(
    `${summary.supported} supported, ${summary.potentialConflict} potential conflict, ${summary.unknown} unknown criteria.`,
  )
  if (!withinTravelPreference && travel.maxMiles !== null) {
    parts.push(
      `Outside the "${travel.label}" preference (${trial.distance.miles} mi, ${trial.distance.label} distance), so it ranks lower but is still shown.`,
    )
  } else {
    parts.push(`Within the "${travel.label}" preference (${trial.distance.miles} mi, ${trial.distance.label} distance).`)
  }
  return parts.join(' ')
}
