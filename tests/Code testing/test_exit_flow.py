import unittest
from unittest.mock import patch

from app.modules.agent_router import Action, AdvisorContext, MainAgentDecision, run_turn
from app.modules.exit_advisor import ExitAdvisorFeedback


class _SequencedStructuredLLM:
    def __init__(self, responses):
        self._responses = iter(responses)

    def invoke(self, _messages):
        return next(self._responses)


class _FakeLLM:
    def __init__(self, responses):
        self._responses = iter(responses)

    def with_structured_output(self, _schema):
        return _SequencedStructuredLLM(self._responses)


class TestExitFlow(unittest.TestCase):
    def test_clear_exit_routes_to_final_end(self):
        context = AdvisorContext(
            message="I am not interested anymore, thanks.",
            role="Python Developer",
            history=[],
            first_name="Sam",
        )

        feedback = ExitAdvisorFeedback(
            exit_match=True,
            rationale="Candidate explicitly stated they are no longer interested.",
        )
        decision = MainAgentDecision(
            action="end",
            reply="Understood. Thanks for your time, Sam.",
            confident=True,
        )

        with patch("app.modules.agent_router._pick_advisor", return_value=Action.END), \
             patch("app.modules.exit_advisor.get_exit_feedback", return_value=feedback), \
             patch("app.modules.agent_router.build_chat_llm", return_value=_FakeLLM([decision])):
            result = run_turn(context)

        self.assertEqual(result.action, "end")
        self.assertTrue(result.confident)
        self.assertEqual(result.reply, "Understood. Thanks for your time, Sam.")
        self.assertIsNone(result.slots)

    def test_clear_continue_routes_to_final_continue(self):
        context = AdvisorContext(
            message="I still have a few questions about the role.",
            role="Python Developer",
            history=[],
            first_name="Alex",
        )

        feedback = ExitAdvisorFeedback(
            exit_match=False,
            rationale="Candidate is still engaged and asking questions.",
        )
        decision = MainAgentDecision(
            action="continue",
            reply="Of course. What would you like to know?",
            confident=True,
        )

        with patch("app.modules.agent_router._pick_advisor", return_value=Action.END), \
             patch("app.modules.exit_advisor.get_exit_feedback", return_value=feedback), \
             patch("app.modules.agent_router.build_chat_llm", return_value=_FakeLLM([decision])):
            result = run_turn(context)

        self.assertEqual(result.action, "continue")
        self.assertTrue(result.confident)
        self.assertEqual(result.reply, "Of course. What would you like to know?")
        self.assertIsNone(result.slots)

    def test_ambiguous_exit_phrasing_loops_back_before_final_end(self):
        context = AdvisorContext(
            message="I don't know, maybe...",
            role="Python Developer",
            history=["Candidate: I am not sure this is for me."],
            first_name="Taylor",
        )

        first_feedback = ExitAdvisorFeedback(
            exit_match=False,
            rationale="Message is ambiguous, could be hesitation or disengagement.",
        )
        second_feedback = ExitAdvisorFeedback(
            exit_match=True,
            rationale="History shows prior disengagement, so exit is likely.",
        )

        decisions = [
            MainAgentDecision(
                action="continue",
                reply="",
                confident=False,
                clarification_needed="Unclear whether candidate wants to end or just pause — please check conversation history for intent signals.",
            ),
            MainAgentDecision(
                action="end",
                reply="Understood. Thanks for your time, Taylor.",
                confident=True,
            ),
        ]

        captured_notes = []

        def _fake_exit_feedback(message, role=None, history=None, main_agent_note=None):
            captured_notes.append(main_agent_note)
            if main_agent_note is None:
                return first_feedback
            return second_feedback

        with patch("app.modules.agent_router._pick_advisor", return_value=Action.END), \
             patch("app.modules.exit_advisor.get_exit_feedback", side_effect=_fake_exit_feedback), \
             patch("app.modules.agent_router.build_chat_llm", return_value=_FakeLLM(decisions)):
            result = run_turn(context)

        self.assertEqual(result.action, "end")
        self.assertTrue(result.confident)
        self.assertEqual(
            captured_notes,
            [
                None,
                "Unclear whether candidate wants to end or just pause — please check conversation history for intent signals.",
            ],
        )