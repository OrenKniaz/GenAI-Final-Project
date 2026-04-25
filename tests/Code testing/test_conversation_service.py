#setting up first unit test - conversation service (Stud)

import unittest

from app.modules.conversation_service import process_candidate_turn, CandidateTurnInput


class TestConversationService(unittest.TestCase):
    def test_schedule_turn_returns_slots(self):
        result = process_candidate_turn(CandidateTurnInput(message="what's your schedule"))
        slots = result.slots

        self.assertEqual(result.action, "schedule")
        self.assertTrue(result.show_slots)
        self.assertIsNotNone(slots)
        assert slots is not None
        self.assertGreater(len(slots), 0)

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

    def test_exit_takes_precedence_over_schedule(self):
        result = process_candidate_turn(
        CandidateTurnInput(message="bye, can we schedule an interview?"))

        self.assertEqual(result.action, "end")
        self.assertFalse(result.show_slots)
        self.assertIsNone(result.slots)

    def test_role_is_detected_from_message(self):
        result = process_candidate_turn(
        CandidateTurnInput(message="I am interested in the Python Developer role"))

        self.assertEqual(result.role, "Python Developer")

    def test_python_developer_role_is_normalized(self):
        result = process_candidate_turn(
        CandidateTurnInput(message="I am interested in the Python Developer role"))

        self.assertEqual(result.role, "Python Developer")
        self.assertEqual(result.normalized_role, "Python Dev")

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


if __name__ == "__main__":
    unittest.main()