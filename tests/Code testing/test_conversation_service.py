#setting up first unit test - conversation service (Stud)

import unittest

from app.modules.conversation_service import process_candidate_turn


class TestConversationService(unittest.TestCase):
    def test_schedule_turn_returns_slots(self):
        result = process_candidate_turn("what's your schedule")
        slots = result.slots

        self.assertEqual(result.action, "schedule")
        self.assertTrue(result.show_slots)
        self.assertIsNotNone(slots)
        assert slots is not None
        self.assertGreater(len(slots), 0)

    def test_end_turn_returns_no_slots(self):
        result = process_candidate_turn("bye, I am not interested anymore")

        self.assertEqual(result.action, "end")
        self.assertFalse(result.show_slots)
        self.assertIsNone(result.slots)

    def test_continue_turn_returns_no_slots(self):
        result = process_candidate_turn("can you tell me more about the role?")

        self.assertEqual(result.action, "continue")
        self.assertFalse(result.show_slots)
        self.assertIsNone(result.slots)


if __name__ == "__main__":
    unittest.main()