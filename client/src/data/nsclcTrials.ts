import raw from './nsclcTrials.json'
import type { Trial } from '../types/domain'

/**
 * Real recruiting NSCLC trials from the Hackachusetts dataset, with criteria
 * from ClinicalTrials.gov. Regenerate the JSON with
 * client/scripts/build_nsclc_trials.py.
 */
export const NSCLC_TRIALS = raw as Trial[]
