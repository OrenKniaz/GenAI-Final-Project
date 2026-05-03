# test full run integration flow of our agent router logic.
# goal is to have cold,fast,cheap tests. not covering the LLM itself, just logic

import unittest
from unittest.mock import patch

from app.modules.agent_router import Action, TurnContext, MainAgentDecision, run_turn
from app.modules.schedule_advisor import ScheduleAdvisorFeedback


class _FakeStructuredLLM:
    def invoke(self, _messages):
        return MainAgentDecision(
            action="schedule",
            reply=(
                "Absolutely! Here are a few available slots: "
                "Tuesday, 2024-01-02 at 09:00, Tuesday, 2024-01-02 at 11:00, "
                "or Wednesday, 2024-01-03 at 14:00."
            ),
            confident=True,
        )


class _FakeLLM:
    def with_structured_output(self, _schema):
        return _FakeStructuredLLM()


class TestAgentRouter(unittest.TestCase):
    def test_single_schedule_feedback_routes_to_final_turn_result(self):
        context = TurnContext(
            message="Can we schedule an interview?",
            role="Python Developer",
            history=[],
            first_name="Jordan",
        )

        feedback = ScheduleAdvisorFeedback(
            schedule_match=True,
            requested_time_text=None,
            requested_slot_text=None,
            requested_slot_available=None,
            slots=[
                "Tuesday, 2024-01-02 at 09:00",
                "Tuesday, 2024-01-02 at 11:00",
                "Wednesday, 2024-01-03 at 14:00",
            ],
            reference_date_text="2024-01-02",
            rationale="Candidate explicitly asked to set up an interview.",
        )

        with patch("app.modules.agent_router._pick_advisor", return_value=Action.SCHEDULE), \
             patch("app.modules.schedule_advisor.get_schedule_feedback", return_value=feedback), \
             patch("app.modules.agent_router.build_chat_llm", return_value=_FakeLLM()):
            result = run_turn(context)

        self.assertEqual(result.action, "schedule")
        self.assertTrue(result.confident)
        self.assertEqual(result.slots, feedback.slots)
        self.assertIn("available slots", result.reply)
        self.assertIn("Tuesday, 2024-01-02 at 09:00", result.reply)