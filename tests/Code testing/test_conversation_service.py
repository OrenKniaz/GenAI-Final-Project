#setting up first unit test - conversation service (Stud)

import unittest

from app.modules.conversation_service import process_candidate_turn, CandidateTurnInput
from app.modules.Helpers.sql_helper import get_schedule_reference_date
import datetime as dt
from unittest.mock import patch
from app.modules.schedule_advisor import get_schedule_feedback

class _FakeStructuredLLM:
    def __init__(self, payload):
        self.payload = payload

    def invoke(self, _messages):
        return self.payload

class _FakeLLM:
    def __init__(self, payload):
        self.payload = payload

    def with_structured_output(self, _schema):
        return _FakeStructuredLLM(self.payload)


class TestConversationService(unittest.TestCase):
    def test_schedule_turn_returns_slots(self):
        result = process_candidate_turn(
            CandidateTurnInput(message="Can we schedule an interview?", role="Python Developer")
        )
        slots = result.slots

        self.assertEqual(result.action, "schedule")
        self.assertTrue(result.show_slots)
        self.assertIsNotNone(slots)
        assert slots is not None
        self.assertGreater(len(slots), 0)
        self.assertLessEqual(len(slots), 3)
        self.assertTrue(all(" at " in slot for slot in slots))
        self.assertTrue(all("datetime.date" not in slot for slot in slots))
        self.assertTrue(all("datetime.time" not in slot for slot in slots))

    def test_end_turn_returns_no_slots(self):
        result = process_candidate_turn(CandidateTurnInput(message="bye, I am not interested anymore"))

        self.assertEqual(result.action, "end")
        self.assertFalse(result.show_slots)
        self.assertIsNone(result.slots)

    def test_continue_turn_returns_no_slots(self):
        result = process_candidate_turn(CandidateTurnInput(message="can you tell me more about the role?"))

        self.assertEqual(result.action, "continue")
        self.assertFalse(result.show_slots)
        self.assertIsNone(result.slots)

    def test_schedule_turn_without_role_returns_no_slots(self):
        result = process_candidate_turn(
        CandidateTurnInput(message="Can we schedule an interview?"))

        self.assertIsNone(result.role)
        self.assertIsNone(result.normalized_role)
        self.assertFalse(result.show_slots)
        self.assertIsNone(result.slots)


    def test_existing_role_is_carried_forward_and_normalized(self):
        result = process_candidate_turn(
        CandidateTurnInput(message="Can we schedule an interview?", role="Python Developer",))

        self.assertEqual(result.role, "Python Developer")
        self.assertEqual(result.normalized_role, "Python Dev")

    def test_neutral_follow_up_stays_on_continue(self):
        result = process_candidate_turn(CandidateTurnInput(message="That sounds good, can you tell me more?",role="Python Developer",))

        self.assertEqual(result.action, "continue")
        self.assertFalse(result.show_slots)
        self.assertIsNone(result.slots)
        self.assertEqual(result.role, "Python Developer")
        self.assertEqual(result.normalized_role, "Python Dev")

    def test_interested_without_schedule_stays_on_continue(self):
        result = process_candidate_turn(
        CandidateTurnInput(message="I'm interested")
    )

        self.assertEqual(result.action, "continue")
        self.assertFalse(result.show_slots)
        self.assertIsNone(result.slots)


    def test_available_times_with_role_routes_to_schedule(self):
        result = process_candidate_turn(
            CandidateTurnInput(message="What times are available?", role="Python Developer")
        )

        self.assertEqual(result.action, "schedule")
        self.assertTrue(result.show_slots)
        self.assertIsNotNone(result.slots)
        assert result.slots is not None
        self.assertLessEqual(len(result.slots), 3)
        self.assertTrue(all(" at " in slot for slot in result.slots))
        self.assertTrue(all("datetime.date" not in slot for slot in result.slots))
        self.assertTrue(all("datetime.time" not in slot for slot in result.slots))


    def test_interested_goodbye_routes_to_end(self):
        result = process_candidate_turn(
            CandidateTurnInput(message="I'm interested, goodbye")
        )

        self.assertEqual(result.action, "end")
        self.assertFalse(result.show_slots)
        self.assertIsNone(result.slots)


    def test_polite_delay_stays_on_continue(self):
        result = process_candidate_turn(
            CandidateTurnInput(message="Maybe later, can you tell me more first?")
        )

        self.assertEqual(result.action, "continue")
        self.assertFalse(result.show_slots)
        self.assertIsNone(result.slots)


    def test_clear_exit_phrase_routes_to_end(self):
        result = process_candidate_turn(
            CandidateTurnInput(message="Please stop messaging me")
        )

        self.assertEqual(result.action, "end")
        self.assertFalse(result.show_slots)
        self.assertIsNone(result.slots)

    def test_intake_role_is_used_and_normalized(self):
        # Slice 8: role comes from intake, not from message text
        result = process_candidate_turn(
            CandidateTurnInput(message="Can we schedule an interview?", role="Python Developer")
        )
        self.assertEqual(result.role, "Python Developer")
        self.assertEqual(result.normalized_role, "Python Dev")

    def test_no_intake_role_means_no_resolved_role(self):
        # Slice 8: without an intake role, result.role is None regardless of message content
        result = process_candidate_turn(
            CandidateTurnInput(message="I am interested in the Python Developer role", role=None)
        )
        self.assertIsNone(result.role)
        self.assertIsNone(result.normalized_role)

    def test_schedule_reference_date_exists_for_python_dev(self):
        reference_date = get_schedule_reference_date("Python Dev")

        self.assertIsNotNone(reference_date)
        assert reference_date is not None
        self.assertEqual(reference_date.year, 2024)

    def test_requested_available_time_confirms_slot(self):
        result = process_candidate_turn(
            CandidateTurnInput(
                message="Can we do Tuesday at 9am?",
                role="Python Developer",
            )
        )

        self.assertEqual(result.action, "schedule")
        self.assertTrue(result.show_slots)
        self.assertIsNotNone(result.slots)
    def test_requested_unavailable_time_returns_alternatives(self):
        result = process_candidate_turn(
            CandidateTurnInput(
                message="Can we do Friday at 11am?",
                role="Python Developer",
            )
        )

        self.assertEqual(result.action, "schedule")
        self.assertTrue(result.show_slots)
        self.assertIsNotNone(result.slots)
        assert result.slots is not None
        self.assertLessEqual(len(result.slots), 3)

    def test_phase6_exact_requested_slot_confirms_available(self):
        payload = {
            "schedule_match": True,
            "requested_time_text": "Tuesday at 09:00",
            "requested_slot_text": "2024-01-02 09:00",
            "rationale": "Candidate asked for a concrete time."
        }
        exact = (1, dt.date(2024, 1, 2), dt.time(9, 0), "Python Dev")

        with patch("app.modules.schedule_advisor.build_chat_llm", return_value=_FakeLLM(payload)), \
            patch("app.modules.schedule_advisor.get_schedule_reference_date", return_value=dt.date(2024, 1, 2)), \
            patch("app.modules.schedule_advisor.get_exact_available_slot", return_value=exact), \
            patch("app.modules.schedule_advisor.get_available_slots", return_value=[]):
            fb = get_schedule_feedback("Can we do Tuesday at 9am?", role="Python Developer")

        self.assertTrue(fb.schedule_match)
        self.assertTrue(fb.requested_slot_available)
        self.assertEqual(fb.requested_slot_text, "2024-01-02 09:00")
        self.assertIsNotNone(fb.slots)
        assert fb.slots is not None
        self.assertEqual(len(fb.slots), 1)
        self.assertIn("2024-01-02 at 09:00", fb.slots[0])

    def test_phase6_unavailable_requested_slot_returns_nearest_three(self):
        payload = {
            "schedule_match": True,
            "requested_time_text": "Friday at 11:00",
            "requested_slot_text": "2024-01-05 11:00",
            "rationale": "Candidate asked for a concrete time."
        }
        alternatives = [
            (2, dt.date(2024, 1, 5), dt.time(10, 0), "Python Dev"),
            (3, dt.date(2024, 1, 5), dt.time(12, 0), "Python Dev"),
            (4, dt.date(2024, 1, 6), dt.time(9, 0), "Python Dev"),
        ]

        with patch("app.modules.schedule_advisor.build_chat_llm", return_value=_FakeLLM(payload)), \
            patch("app.modules.schedule_advisor.get_schedule_reference_date", return_value=dt.date(2024, 1, 2)), \
            patch("app.modules.schedule_advisor.get_exact_available_slot", return_value=None), \
            patch("app.modules.schedule_advisor.get_available_slots", return_value=alternatives):
            fb = get_schedule_feedback("Can we do Friday at 11am?", role="Python Developer")

        self.assertTrue(fb.schedule_match)
        self.assertFalse(fb.requested_slot_available)
        self.assertIsNotNone(fb.slots)
        assert fb.slots is not None
        self.assertLessEqual(len(fb.slots), 3)

    def test_phase6_bad_slot_format_falls_back_cleanly(self):
        payload = {
            "schedule_match": True,
            "requested_time_text": "next Tuesday morning",
            "requested_slot_text": "next Tuesday morning",
            "rationale": "Scheduling intent detected."
        }
        fallback = [
            (10, dt.date(2024, 1, 2), dt.time(9, 0), "Python Dev"),
            (11, dt.date(2024, 1, 2), dt.time(11, 0), "Python Dev"),
        ]

        with patch("app.modules.schedule_advisor.build_chat_llm", return_value=_FakeLLM(payload)), \
            patch("app.modules.schedule_advisor.get_schedule_reference_date", return_value=dt.date(2024, 1, 2)), \
            patch("app.modules.schedule_advisor.get_available_slots", return_value=fallback):
            fb = get_schedule_feedback("next Tuesday morning works", role="Python Developer")

        self.assertTrue(fb.schedule_match)
        self.assertFalse(fb.requested_slot_available)
        self.assertIsNotNone(fb.slots)
        assert fb.slots is not None
        self.assertGreater(len(fb.slots), 0)
        
if __name__ == "__main__":
    unittest.main()