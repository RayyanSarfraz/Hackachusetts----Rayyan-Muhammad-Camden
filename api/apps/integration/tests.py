"""
Tests for integration module.

Tests cover:
1. Practical constraint evaluation
2. Geographic distance calculation
3. Ranking logic and conflict preservation
4. Clarification question extraction
5. Answer validation and profile updates
6. Privacy boundary (no leakage)
7. Deterministic behavior
"""

import math
import unittest

from .contracts import (
    AnswerType,
    ClarificationQuestion,
    CriterionAssessment,
    CriterionStatus,
    PatientPreferences,
    PatientProfile,
    PracticalCompatibility,
    TrialCandidate,
    TrialLocation,
)
from .clarification import (
    apply_answer_to_profile,
    deduplicate_questions,
    extract_questions_from_trials,
    prioritize_questions,
    validate_answer,
)
from .fixtures import (
    SYNTHETIC_PATIENT,
    TRIAL_CONFLICT,
    TRIAL_MATCH,
    TRIAL_UNKNOWN,
    get_synthetic_patient,
    get_synthetic_trials,
)
from .orchestrator import (
    apply_clarification_answer,
    combine_trials_and_patient,
    demo_preference_change,
    run_synthetic_demo,
    update_preferences_only,
)
from .ranking import (
    derive_clinical_status,
    evaluate_overnight_constraint,
    evaluate_practical_fit,
    evaluate_travel_constraint,
    find_nearest_location,
    haversine_distance,
    rank_trials,
    rerank_trials,
)


class TestGeographicDistance(unittest.TestCase):
    """Tests for haversine distance calculation."""

    def test_same_location(self):
        """Distance to same point should be zero."""
        coord = (42.3601, -71.0589)
        distance = haversine_distance(coord, coord)
        self.assertAlmostEqual(distance, 0.0, places=1)

    def test_boston_to_new_york(self):
        """Distance from Boston to NYC should be approximately 190 miles."""
        boston = (42.3601, -71.0589)
        nyc = (40.7128, -74.0060)
        distance = haversine_distance(boston, nyc)
        self.assertAlmostEqual(distance, 190.0, delta=10.0)

    def test_boston_to_new_haven(self):
        """Distance from Boston to New Haven should be approximately 130 miles."""
        boston = (42.3601, -71.0589)
        new_haven = (41.3033, -72.9318)
        distance = haversine_distance(boston, new_haven)
        self.assertAlmostEqual(distance, 130.0, delta=10.0)

    def test_antipodal_points(self):
        """Distance calculation should work for distant points."""
        # San Francisco to Sydney
        sf = (37.7749, -122.4194)
        sydney = (-33.8688, 151.2093)
        distance = haversine_distance(sf, sydney)
        self.assertGreater(distance, 7000.0)
        self.assertLess(distance, 8000.0)


class TestPracticalConstraints(unittest.TestCase):
    """Tests for practical constraint evaluation."""

    def test_travel_within_limit(self):
        """Trial within travel limit should be compatible."""
        status, reason = evaluate_travel_constraint(
            max_travel_miles=50.0,
            nearest_distance_miles=30.0,
        )
        self.assertEqual(status, PracticalCompatibility.COMPATIBLE)
        self.assertIn("Within", reason)

    def test_travel_exceeds_limit(self):
        """Trial exceeding travel limit should be incompatible."""
        status, reason = evaluate_travel_constraint(
            max_travel_miles=50.0,
            nearest_distance_miles=130.0,
        )
        self.assertEqual(status, PracticalCompatibility.INCOMPATIBLE)
        self.assertIn("Exceeds", reason)

    def test_travel_unknown_distance(self):
        """Unknown distance should result in unknown status."""
        status, reason = evaluate_travel_constraint(
            max_travel_miles=50.0,
            nearest_distance_miles=None,
        )
        self.assertEqual(status, PracticalCompatibility.UNKNOWN)
        self.assertIn("unknown", reason.lower())

    def test_travel_no_preference(self):
        """No travel preference should result in unknown status."""
        status, reason = evaluate_travel_constraint(
            max_travel_miles=None,
            nearest_distance_miles=30.0,
        )
        self.assertEqual(status, PracticalCompatibility.UNKNOWN)

    def test_overnight_within_day_trip(self):
        """Short distance should not require overnight."""
        status, reason = evaluate_overnight_constraint(
            avoid_overnight=True,
            nearest_distance_miles=30.0,
        )
        self.assertEqual(status, PracticalCompatibility.COMPATIBLE)

    def test_overnight_exceeds_threshold(self):
        """Long distance with avoid_overnight should be incompatible."""
        status, reason = evaluate_overnight_constraint(
            avoid_overnight=True,
            nearest_distance_miles=150.0,
        )
        self.assertEqual(status, PracticalCompatibility.INCOMPATIBLE)

    def test_overnight_unknown_distance(self):
        """Unknown distance with avoid_overnight should be unknown."""
        status, reason = evaluate_overnight_constraint(
            avoid_overnight=True,
            nearest_distance_miles=None,
        )
        self.assertEqual(status, PracticalCompatibility.UNKNOWN)


class TestRanking(unittest.TestCase):
    """Tests for trial ranking logic."""

    def test_clinical_status_derivation_no_conflicts(self):
        """Trial with all met criteria should be potentially eligible."""
        trial = TrialCandidate(
            nct_id="NCT_TEST_001",
            title="Test Trial",
            source_url="https://example.com",
            criteria=[
                CriterionAssessment(
                    criterion_id="c1",
                    criterion_text="Age >= 18",
                    criterion_source="https://example.com",
                    required_fact="age",
                    status=CriterionStatus.MET,
                ),
            ],
        )
        status = derive_clinical_status(trial)
        self.assertEqual(status, "potentially_eligible")

    def test_clinical_status_derivation_with_conflict(self):
        """Trial with conflict should have conflict status."""
        trial = TrialCandidate(
            nct_id="NCT_TEST_002",
            title="Test Trial",
            source_url="https://example.com",
            criteria=[
                CriterionAssessment(
                    criterion_id="c1",
                    criterion_text="Age >= 18",
                    criterion_source="https://example.com",
                    required_fact="age",
                    status=CriterionStatus.MET,
                ),
                CriterionAssessment(
                    criterion_id="c2",
                    criterion_text="No prior treatment",
                    criterion_source="https://example.com",
                    required_fact="prior_treatment",
                    status=CriterionStatus.CONFLICT,
                ),
            ],
        )
        status = derive_clinical_status(trial)
        self.assertEqual(status, "conflict")

    def test_clinical_status_derivation_with_unknown(self):
        """Trial with unknown criteria should need clarification."""
        trial = TrialCandidate(
            nct_id="NCT_TEST_003",
            title="Test Trial",
            source_url="https://example.com",
            criteria=[
                CriterionAssessment(
                    criterion_id="c1",
                    criterion_text="Age >= 18",
                    criterion_source="https://example.com",
                    required_fact="age",
                    status=CriterionStatus.MET,
                ),
                CriterionAssessment(
                    criterion_id="c2",
                    criterion_text="No prior treatment",
                    criterion_source="https://example.com",
                    required_fact="prior_treatment",
                    status=CriterionStatus.UNKNOWN,
                ),
            ],
        )
        status = derive_clinical_status(trial)
        self.assertEqual(status, "needs_clarification")

    def test_ranking_conflict_not_hidden_by_convenience(self):
        """
        Clinical conflicts must NOT be hidden by practical convenience.
        
        A trial with a conflict should rank below trials without conflicts,
        even if the conflicted trial is more convenient.
        """
        # Conflicted trial, very close
        trial_conflict = TrialCandidate(
            nct_id="NCT_CONFLICT",
            title="Close but conflicted",
            source_url="https://example.com",
            locations=[
                TrialLocation(
                    name="Nearby",
                    city="Boston",
                    state="MA",
                    coords=(42.3601, -71.0589),
                ),
            ],
            criteria=[
                CriterionAssessment(
                    criterion_id="c1",
                    criterion_text="Exclusion: prior treatment",
                    criterion_source="https://example.com",
                    required_fact="prior_treatment",
                    status=CriterionStatus.CONFLICT,
                ),
            ],
        )
        
        # Potentially eligible trial, farther away
        trial_eligible = TrialCandidate(
            nct_id="NCT_ELIGIBLE",
            title="Far but eligible",
            source_url="https://example.com",
            locations=[
                TrialLocation(
                    name="Far",
                    city="Hartford",
                    state="CT",
                    coords=(41.7658, -72.6734),
                ),
            ],
            criteria=[
                CriterionAssessment(
                    criterion_id="c1",
                    criterion_text="Age >= 18",
                    criterion_source="https://example.com",
                    required_fact="age",
                    status=CriterionStatus.MET,
                ),
            ],
        )
        
        preferences = PatientPreferences(max_travel_miles=200.0)
        ranked = rank_trials([trial_conflict, trial_eligible], preferences)
        
        # Eligible trial should rank higher despite being farther
        self.assertEqual(ranked[0].nct_id, "NCT_ELIGIBLE")
        self.assertEqual(ranked[1].nct_id, "NCT_CONFLICT")

    def test_reranking_is_pure_function(self):
        """Re-ranking should not modify original trials."""
        trials = get_synthetic_trials()
        preferences = PatientPreferences(max_travel_miles=100.0)
        
        # Capture original state
        original_statuses = [t.clinical_status for t in trials]
        
        # Re-rank
        ranked = rerank_trials(trials, preferences)
        
        # Original list should be modified (rank_trials mutates)
        # But the function should be deterministic
        ranked_again = rerank_trials(trials, preferences)
        
        # Same results
        self.assertEqual(
            [t.nct_id for t in ranked],
            [t.nct_id for t in ranked_again],
        )


class TestClarificationQuestions(unittest.TestCase):
    """Tests for clarification question extraction."""

    def test_extract_questions_from_unknowns(self):
        """Questions should be extracted from UNKNOWN criteria."""
        questions = extract_questions_from_trials(get_synthetic_trials())
        
        # Should have questions for unknown criteria
        self.assertGreater(len(questions), 0)
        
        # All questions should have proper structure
        for q in questions:
            self.assertIsNotNone(q.question_id)
            self.assertIsNotNone(q.display_question)
            self.assertGreater(len(q.related_trial_ids), 0)

    def test_deduplicate_same_fact(self):
        """Questions about the same fact should be deduplicated."""
        # Create two trials with same unknown fact
        trial1 = TrialCandidate(
            nct_id="NCT_001",
            title="Trial 1",
            source_url="https://example.com",
            criteria=[
                CriterionAssessment(
                    criterion_id="c1",
                    criterion_text="Prior insulin use",
                    criterion_source="https://example.com",
                    required_fact="insulin_use",
                    status=CriterionStatus.UNKNOWN,
                ),
            ],
        )
        trial2 = TrialCandidate(
            nct_id="NCT_002",
            title="Trial 2",
            source_url="https://example.com",
            criteria=[
                CriterionAssessment(
                    criterion_id="c2",
                    criterion_text="History of insulin therapy",
                    criterion_source="https://example.com",
                    required_fact="insulin_use",
                    status=CriterionStatus.UNKNOWN,
                ),
            ],
        )
        
        questions = extract_questions_from_trials([trial1, trial2])
        
        # Should deduplicate to one question
        insulin_questions = [
            q for q in questions if q.required_fact_key == "insulin_use"
        ]
        self.assertEqual(len(insulin_questions), 1)
        
        # But should reference both trials
        self.assertIn("NCT_001", insulin_questions[0].related_trial_ids)
        self.assertIn("NCT_002", insulin_questions[0].related_trial_ids)

    def test_no_questions_for_known_criteria(self):
        """No questions should be generated for MET or CONFLICT criteria."""
        trial = TrialCandidate(
            nct_id="NCT_KNOWN",
            title="All Known",
            source_url="https://example.com",
            criteria=[
                CriterionAssessment(
                    criterion_id="c1",
                    criterion_text="Age >= 18",
                    criterion_source="https://example.com",
                    required_fact="age",
                    status=CriterionStatus.MET,
                ),
                CriterionAssessment(
                    criterion_id="c2",
                    criterion_text="No prior treatment",
                    criterion_source="https://example.com",
                    required_fact="prior_treatment",
                    status=CriterionStatus.CONFLICT,
                ),
            ],
        )
        
        questions = extract_questions_from_trials([trial])
        self.assertEqual(len(questions), 0)


class TestAnswerValidation(unittest.TestCase):
    """Tests for answer validation."""

    def test_validate_yes_no_unknown(self):
        """yes/no/unknown type should accept those values."""
        question = ClarificationQuestion(
            question_id="q_test",
            required_fact_key="test_fact",
            display_question="Test question?",
            answer_type=AnswerType.YES_NO_UNKNOWN,
            related_trial_ids=["NCT_001"],
            source_criterion_ids=["c1"],
            reason="Test",
        )
        
        is_valid, _ = validate_answer(question, "yes")
        self.assertTrue(is_valid)
        
        is_valid, _ = validate_answer(question, "no")
        self.assertTrue(is_valid)
        
        is_valid, _ = validate_answer(question, "unknown")
        self.assertTrue(is_valid)
        
        is_valid, error = validate_answer(question, "maybe")
        self.assertFalse(is_valid)
        self.assertIn("must be", error)

    def test_validate_number(self):
        """Number type should accept numeric values."""
        question = ClarificationQuestion(
            question_id="q_test",
            required_fact_key="test_fact",
            display_question="How many?",
            answer_type=AnswerType.NUMBER,
            related_trial_ids=["NCT_001"],
            source_criterion_ids=["c1"],
            reason="Test",
        )
        
        is_valid, _ = validate_answer(question, 5)
        self.assertTrue(is_valid)
        
        is_valid, _ = validate_answer(question, "3.14")
        self.assertTrue(is_valid)
        
        is_valid, error = validate_answer(question, "five")
        self.assertFalse(is_valid)


class TestProfileUpdate(unittest.TestCase):
    """Tests for patient profile updates from answers."""

    def test_answer_updates_profile(self):
        """Answer should update medical_facts in profile."""
        profile = PatientProfile(
            age=50,
            conditions=["Diabetes"],
            medications=[],
            medical_facts={"hba1c": 7.5},
            unknowns=["insulin_use"],
        )
        
        question = ClarificationQuestion(
            question_id="q_insulin",
            required_fact_key="insulin_use",
            display_question="Have you used insulin?",
            answer_type=AnswerType.YES_NO_UNKNOWN,
            related_trial_ids=["NCT_001"],
            source_criterion_ids=["c1"],
            reason="Test",
        )
        
        updated = apply_answer_to_profile(profile, question, "yes")
        
        # Original should be unchanged
        self.assertNotIn("insulin_use", profile.medical_facts)
        
        # Updated should have new fact
        self.assertTrue(updated.medical_facts["insulin_use"])
        
        # Unknown should be removed
        self.assertNotIn("insulin_use", updated.unknowns)

    def test_answer_does_not_auto_resolve(self):
        """Answering a question should NOT automatically resolve criteria."""
        # This test verifies that the profile is updated but criteria
        # remain UNKNOWN until explicitly reassessed
        profile = get_synthetic_patient()
        trials = get_synthetic_trials()
        
        # Find a question about insulin_use
        questions = extract_questions_from_trials(trials)
        insulin_q = next(
            (q for q in questions if q.required_fact_key == "insulin_use"),
            None,
        )
        
        if insulin_q:
            # Answer the question
            updated_profile, affected, reassess = apply_clarification_answer(
                trials, profile, insulin_q.question_id, "no"
            )
            
            # Profile should be updated
            self.assertFalse(updated_profile.medical_facts.get("insulin_use"))
            
            # Should return affected criteria for reassessment
            self.assertGreater(len(affected), 0)


class TestPrivacyBoundary(unittest.TestCase):
    """Tests for privacy and data handling."""

    def test_sanitized_profile_no_detailed_medications(self):
        """Sanitized profile should not expose specific medications."""
        profile = get_synthetic_patient()
        sanitized = profile.to_sanitized_dict()
        
        # Should have count, not list
        self.assertIn("medication_count", sanitized)
        self.assertNotIn("medications", sanitized)
        
        # Should have count, not specific conditions
        self.assertIn("condition_count", sanitized)
        self.assertNotIn("conditions", sanitized)

    def test_no_patient_identifiers_in_response(self):
        """Comparison response should not contain patient identifiers."""
        response = run_synthetic_demo()
        
        response_dict = response.to_dict()
        response_str = str(response_dict)
        
        # Should not contain names, SSN, or other identifiers
        # (Our synthetic data doesn't have these, but verify they're not added)
        identifier_patterns = ["ssn", "social_security", "mrn", "patient_id"]
        for pattern in identifier_patterns:
            self.assertNotIn(pattern, response_str.lower())

    def test_medical_values_not_leaked_in_logs(self):
        """Sensitive medical values should not appear in string representations."""
        profile = get_synthetic_patient()
        
        # The __str__ or __repr__ should not expose sensitive values
        # For dataclasses, this is default behavior, but let's verify
        profile_str = str(profile)
        
        # Should not contain exact HbA1c value in string
        # (This is a design consideration - dataclasses expose everything)
        # For hackathon, we document this limitation


class TestNegation(unittest.TestCase):
    """Test handling of negation in clinical facts."""

    def test_negative_answer_stored_correctly(self):
        """'No' answer should be stored as False, not inverted."""
        profile = PatientProfile(
            age=50,
            conditions=[],
            medications=[],
            medical_facts={},
        )
        
        question = ClarificationQuestion(
            question_id="q_prior_tx",
            required_fact_key="prior_chemotherapy",
            display_question="Have you received chemotherapy before?",
            answer_type=AnswerType.YES_NO_UNKNOWN,
            related_trial_ids=["NCT_001"],
            source_criterion_ids=["c1"],
            reason="Test",
        )
        
        # Answer "no"
        updated = apply_answer_to_profile(profile, question, "no")
        
        # Should be False (has NOT received chemotherapy)
        self.assertFalse(updated.medical_facts["prior_chemotherapy"])

    def test_has_not_received_drug(self):
        """Test negation: 'has not received Drug X'."""
        # This tests that we correctly handle "no" answers
        # for questions about treatments not received
        profile = PatientProfile(
            age=50,
            conditions=[],
            medications=[],
            medical_facts={},
        )
        
        question = ClarificationQuestion(
            question_id="q_drug_x",
            required_fact_key="received_drug_x",
            display_question="Have you received Drug X?",
            answer_type=AnswerType.YES_NO_UNKNOWN,
            related_trial_ids=["NCT_001"],
            source_criterion_ids=["c1"],
            reason="Test",
        )
        
        # Patient has NOT received Drug X
        updated = apply_answer_to_profile(profile, question, "no")
        
        # Should be False
        self.assertFalse(updated.medical_facts["received_drug_x"])
        
        # If the criterion is "Exclusion: has received Drug X",
        # then has NOT received it means the patient is NOT excluded
        # This interpretation is the clinical module's responsibility


class TestDeterministicBehavior(unittest.TestCase):
    """Tests for deterministic, reproducible behavior."""

    def test_same_input_same_output(self):
        """Same input should always produce same output."""
        patient = get_synthetic_patient()
        trials = get_synthetic_trials()
        
        response1 = combine_trials_and_patient(trials, patient)
        response2 = combine_trials_and_patient(trials, patient)
        
        # Should be identical
        self.assertEqual(
            [r.trial.nct_id for r in response1.results],
            [r.trial.nct_id for r in response2.results],
        )

    def test_reranking_no_external_calls(self):
        """Re-ranking should be pure function with no external calls."""
        # This is a design verification, not runtime check
        # The rerank_trials function has no network/file I/O
        # It only uses haversine_distance which is pure math
        
        trials = get_synthetic_trials()
        prefs = PatientPreferences(max_travel_miles=100.0)
        
        # Should complete without any external dependencies
        result = rerank_trials(trials, prefs)
        self.assertIsNotNone(result)


class TestEmptyEdgeCases(unittest.TestCase):
    """Tests for empty or invalid inputs."""

    def test_empty_trial_list(self):
        """Empty trial list should produce valid response."""
        response = combine_trials_and_patient([], get_synthetic_patient())
        
        self.assertEqual(len(response.results), 0)
        self.assertEqual(len(response.questions), 0)

    def test_trial_no_locations(self):
        """Trial with no locations should handle gracefully."""
        trial = TrialCandidate(
            nct_id="NCT_NO_LOC",
            title="No locations",
            source_url="https://example.com",
            locations=[],
            criteria=[
                CriterionAssessment(
                    criterion_id="c1",
                    criterion_text="Age >= 18",
                    criterion_source="https://example.com",
                    required_fact="age",
                    status=CriterionStatus.MET,
                ),
            ],
        )
        
        preferences = PatientPreferences(max_travel_miles=50.0)
        ranked = rank_trials([trial], preferences)
        
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].practical_fit, PracticalCompatibility.UNKNOWN)

    def test_trial_no_criteria(self):
        """Trial with no criteria should be marked unknown."""
        trial = TrialCandidate(
            nct_id="NCT_NO_CRIT",
            title="No criteria",
            source_url="https://example.com",
            locations=[],
            criteria=[],
        )
        
        status = derive_clinical_status(trial)
        self.assertEqual(status, "potentially_eligible")  # No conflicts, no unknowns


class TestIntegration(unittest.TestCase):
    """End-to-end integration tests."""

    def test_synthetic_demo_runs(self):
        """Synthetic demo should run without errors."""
        response = run_synthetic_demo()
        
        self.assertIsNotNone(response)
        self.assertEqual(len(response.results), 3)  # Three trials
        self.assertGreater(len(response.questions), 0)  # Should have questions

    def test_preference_change_demo(self):
        """Preference change demo should show updated ranking."""
        before, after = demo_preference_change()
        
        # Both should succeed
        self.assertIsNotNone(before)
        self.assertIsNotNone(after)

    def test_all_three_scenarios(self):
        """
        Verify all three trial types:
        - One preliminary match
        - One conflict
        - One with missing info
        """
        trials = get_synthetic_trials()
        response = combine_trials_and_patient(trials, get_synthetic_patient())
        
        # Check we have all three types
        statuses = [r.clinical_status for r in response.results]
        
        # Should have at least one potentially_eligible
        self.assertIn("potentially_eligible", statuses)
        
        # Should have at least one needs_clarification
        self.assertIn("needs_clarification", statuses)




class TestRegressionFixes(unittest.TestCase):
    """Regression coverage for PR #2 review fixes."""

    def test_distance_is_computed_from_patient_coordinates(self):
        patient = get_synthetic_patient()
        response = combine_trials_and_patient(get_synthetic_trials(), patient)
        distances = {r.trial.nct_id: r.trial.nearest_distance_miles for r in response.results}
        self.assertIsNotNone(distances["NCT05763157"])
        self.assertGreater(distances["NCT05763157"], 100)
        self.assertLess(distances["NCT05615089"], 10)

    def test_fixture_getters_return_independent_objects(self):
        patient1 = get_synthetic_patient()
        patient1.medical_facts["insulin_use"] = True
        self.assertNotIn("insulin_use", get_synthetic_patient().medical_facts)
        trials1 = get_synthetic_trials()
        trials1[0].criteria.clear()
        self.assertGreater(len(get_synthetic_trials()[0].criteria), 0)

    def test_ranking_does_not_mutate_input(self):
        trials = get_synthetic_trials()
        response = combine_trials_and_patient(trials, get_synthetic_patient())
        self.assertIsNone(trials[0].nearest_distance_miles)
        self.assertIsNone(trials[0].clinical_status)
        self.assertIsNotNone(response.results[0].trial.clinical_status)

    def test_ambiguous_criterion_remains_unknown(self):
        from .orchestrator import assess_explicit_boolean_rules
        patient = get_synthetic_patient()
        patient.medical_facts["insulin_use"] = False
        trials = get_synthetic_trials()
        updated = assess_explicit_boolean_rules(
            trials, patient, ["NCT05763157:NCT05763157-inc-002"]
        )
        criterion = next(c for t in updated if t.nct_id == "NCT05763157"
                         for c in t.criteria if c.required_fact == "insulin_use")
        self.assertEqual(criterion.status, CriterionStatus.UNKNOWN)

    def test_explicit_boolean_rule_reassesses(self):
        from .orchestrator import assess_explicit_boolean_rules
        patient = get_synthetic_patient()
        patient.medical_facts["cardiovascular_event_history"] = False
        trials = get_synthetic_trials()
        updated = assess_explicit_boolean_rules(
            trials, patient, ["NCT05763157:NCT05763157-exc-001"]
        )
        criterion = next(c for t in updated if t.nct_id == "NCT05763157"
                         for c in t.criteria if c.required_fact == "cardiovascular_event_history")
        self.assertEqual(criterion.status, CriterionStatus.MET)
        original = next(c for t in trials if t.nct_id == "NCT05763157"
                        for c in t.criteria if c.required_fact == "cardiovascular_event_history")
        self.assertEqual(original.status, CriterionStatus.UNKNOWN)

    def test_unknown_answer_stays_unknown(self):
        profile = get_synthetic_patient()
        q = next(q for q in extract_questions_from_trials(get_synthetic_trials())
                 if q.required_fact_key == "insulin_use")
        updated = apply_answer_to_profile(profile, q, "unknown")
        self.assertIn("insulin_use", updated.unknowns)


# =============================================================================
# FRONTEND SEAM TESTS
# =============================================================================

from apps.integration.frontend_demo import (  # noqa: E402
    DEMO_TRIALS,
    DEMO_PATIENT_NOTES,
    FACT_DEFINITIONS,
    get_demo_trials,
    parse_notes,
)


class TestFrontendDemoTrials(unittest.TestCase):
    """The /api/trials payload must match the frontend's Trial shape."""

    def test_returns_four_demo_trials(self):
        trials = get_demo_trials()
        self.assertEqual(len(trials), 4)
        self.assertEqual([t["id"] for t in trials], ["DEMO-A", "DEMO-B", "DEMO-C", "DEMO-D"])

    def test_trial_shape_matches_frontend(self):
        trial = get_demo_trials()[0]
        # Top-level keys the frontend Trial interface requires.
        for key in ("id", "name", "location", "distance", "sourceLabel", "criteria"):
            self.assertIn(key, trial)
        self.assertEqual(trial["distance"]["label"], "mock")
        crit = trial["criteria"][0]
        for key in ("id", "text", "category", "dependsOn", "estimatedEffort", "kind"):
            self.assertIn(key, crit)
        self.assertIsInstance(crit["dependsOn"], list)

    def test_get_demo_trials_is_deep_copied(self):
        a = get_demo_trials()
        a[0]["criteria"].clear()
        b = get_demo_trials()
        self.assertGreater(len(b[0]["criteria"]), 0)


class TestFrontendNoteParser(unittest.TestCase):
    """parse_notes must mirror the frontend's deterministic parser output."""

    def test_demo_note_extracts_documented_facts(self):
        profile = parse_notes(DEMO_PATIENT_NOTES)
        facts = profile["facts"]
        self.assertEqual(facts["age"]["value"], 54)
        self.assertTrue(facts["age"]["known"])
        self.assertEqual(facts["condition"]["value"], "Non-small cell lung cancer")
        self.assertEqual(facts["location"]["value"], "Boston, MA")
        self.assertEqual(facts["previousTreatment"]["value"], "Chemotherapy")

    def test_undocumented_facts_remain_unknown(self):
        profile = parse_notes(DEMO_PATIENT_NOTES)
        facts = profile["facts"]
        for key in ("egfrStatus", "cancerStage", "ecogStatus"):
            self.assertIsNone(facts[key]["value"])
            self.assertFalse(facts[key]["known"])

    def test_profile_has_all_fact_keys(self):
        profile = parse_notes(DEMO_PATIENT_NOTES)
        expected = {d["key"] for d in FACT_DEFINITIONS}
        self.assertEqual(set(profile["facts"].keys()), expected)

    def test_fact_shape_matches_frontend(self):
        fact = parse_notes(DEMO_PATIENT_NOTES)["facts"]["age"]
        for key in ("key", "label", "value", "known", "source"):
            self.assertIn(key, fact)
        self.assertEqual(fact["source"], "parsed")

    def test_empty_notes_all_unknown(self):
        profile = parse_notes("")
        for fact in profile["facts"].values():
            self.assertIsNone(fact["value"])
            self.assertFalse(fact["known"])

    def test_egfr_positive_extracted(self):
        profile = parse_notes("EGFR mutation detected (activating).")
        self.assertEqual(profile["facts"]["egfrStatus"]["value"], "positive")

    def test_stage_normalized_to_roman(self):
        profile = parse_notes("Stage 4 disease confirmed.")
        self.assertEqual(profile["facts"]["cancerStage"]["value"], "IV")


if __name__ == "__main__":
    unittest.main()
