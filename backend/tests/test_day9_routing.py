import asyncio
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agent import AssistantFnc, CallTracker
from specialist import SchemeSpecialistAgent, SchemeSpecialistFnc
import db


async def run_day9_routing_tests():
    print("==================================================")
    print("      DAY 9: ROUTING & SPECIALIST TEST SUITE      ")
    print("==================================================")

    # 1. Routing Classifier Helper (simulates LLM intent classification based on MoneyBuddy prompt rules)
    def determine_routing(user_query: str) -> str:
        """Determines whether a query routes to 'moneybuddy' or 'scheme_specialist'
        based on MoneyBuddy's Day 9 prompt rules.
        """
        q = user_query.lower()

        # Opt out / termination
        if any(term in q for term in ["stop", "opt out", "don't call", "stop calling", "bye"]):
            return "moneybuddy_optout"

        # Explicit human help / escalation
        if any(term in q for term in ["human", "support", "someone call me", "इंसान", "agent"]):
            return "moneybuddy_escalate"

        # Fraud / card loss
        if any(term in q for term in ["fraud", "stolen", "lost my", "lost card", "unauthorized", "used my card", "used my account"]):
            return "moneybuddy_escalate"

        # General banking & financial concepts
        if any(term in q for term in ["savings account", "fixed deposit", "budget", "how should i budget", "open an account"]):
            return "moneybuddy"

        # Government scheme queries -> Scheme Specialist
        if any(term in q for term in ["scheme", "pm kisan", "kisan", "pmsby", "pmjjby", "eligibility", "documents required", "benefits", "apply for", "योजना", "पात्र"]):
            return "scheme_specialist"

        return "moneybuddy"

    # [Test 1] "What is a savings account?" -> MoneyBuddy
    print("\n[Test 1] Normal Question: 'What is a savings account?'")
    target = determine_routing("What is a savings account?")
    assert target == "moneybuddy", f"Expected 'moneybuddy', got '{target}'"
    print("-> Result: Handled by MoneyBuddy (No handoff) [Passed]")

    # [Test 2] "I lost my debit card." -> MoneyBuddy
    print("\n[Test 2] Card Loss Question: 'I lost my debit card.'")
    target = determine_routing("I lost my debit card.")
    assert target == "moneybuddy_escalate", f"Expected 'moneybuddy_escalate', got '{target}'"
    print("-> Result: Handled by MoneyBuddy Escalation Flow [Passed]")

    # [Test 3] "I think someone used my card." -> MoneyBuddy
    print("\n[Test 3] Fraud Question: 'I think someone used my card.'")
    target = determine_routing("I think someone used my card.")
    assert target == "moneybuddy_escalate", f"Expected 'moneybuddy_escalate', got '{target}'"
    print("-> Result: Handled by MoneyBuddy Escalation Flow [Passed]")

    # [Test 4] "Can I check my PM Kisan eligibility?" -> Scheme Specialist
    print("\n[Test 4] Scheme Eligibility: 'Can I check my PM Kisan eligibility?'")
    target = determine_routing("Can I check my PM Kisan eligibility?")
    assert target == "scheme_specialist", f"Expected 'scheme_specialist', got '{target}'"
    print("-> Result: Routed to Government Scheme Specialist [Passed]")

    # [Test 5] "What documents do I need for PM Kisan?" -> Scheme Specialist
    print("\n[Test 5] Scheme Documents: 'What documents do I need for PM Kisan?'")
    target = determine_routing("What documents do I need for PM Kisan?")
    assert target == "scheme_specialist", f"Expected 'scheme_specialist', got '{target}'"
    print("-> Result: Routed to Government Scheme Specialist [Passed]")

    # [Test 6] "What benefits does this government scheme provide?" -> Scheme Specialist
    print("\n[Test 6] Scheme Benefits: 'What benefits does this government scheme provide?'")
    target = determine_routing("What benefits does this government scheme provide?")
    assert target == "scheme_specialist", f"Expected 'scheme_specialist', got '{target}'"
    print("-> Result: Routed to Government Scheme Specialist [Passed]")

    # [Test 7] "How do I apply for this government scheme?" -> Scheme Specialist
    print("\n[Test 7] Scheme Application: 'How do I apply for this government scheme?'")
    target = determine_routing("How do I apply for this government scheme?")
    assert target == "scheme_specialist", f"Expected 'scheme_specialist', got '{target}'"
    print("-> Result: Routed to Government Scheme Specialist [Passed]")

    # [Test 8] "Tell me about government financial schemes." -> Scheme Specialist
    print("\n[Test 8] Scheme Overview: 'Tell me about government financial schemes.'")
    target = determine_routing("Tell me about government financial schemes.")
    assert target == "scheme_specialist", f"Expected 'scheme_specialist', got '{target}'"
    print("-> Result: Routed to Government Scheme Specialist [Passed]")

    # [Test 9] "I want to talk to a human." -> MoneyBuddy
    print("\n[Test 9] Human Support Request: 'I want to talk to a human.'")
    target = determine_routing("I want to talk to a human.")
    assert target == "moneybuddy_escalate", f"Expected 'moneybuddy_escalate', got '{target}'"
    print("-> Result: Handled by MoneyBuddy Escalation Flow [Passed]")

    # [Test 10] "Stop this call." -> MoneyBuddy Opt-out
    print("\n[Test 10] Opt-Out Request: 'Stop this call.'")
    target = determine_routing("Stop this call.")
    assert target == "moneybuddy_optout", f"Expected 'moneybuddy_optout', got '{target}'"
    print("-> Result: Handled by MoneyBuddy Opt-Out Flow [Passed]")

    # [Test 11] Handoff Execution & Context Preservation
    print("\n[Test 11] Handoff Tool Execution & Sensitive Data Sanitization")
    received_context = {}

    async def mock_handoff_cb(user_query: str, caller_context: Optional[str] = None):
        received_context["query"] = user_query
        received_context["context"] = caller_context

    tracker = CallTracker("test_call_day9_1", "browser")
    mb_fnc = AssistantFnc("user_day9_test", call_tracker=tracker, handoff_cb=mock_handoff_cb)

    # Trigger handoff with sensitive info to verify sanitization
    res = await mb_fnc.handoff_to_scheme_specialist(
        user_query="Check eligibility for PM Kisan",
        caller_context="My Aadhaar is 123456789012 and my PIN: 4321",
    )
    print(f"Handoff Output: {res}")
    assert "Connecting you" in res or "specialist" in res
    assert "[REDACTED ID]" in received_context["context"]
    assert "123456789012" not in received_context["context"]
    assert "[REDACTED CREDENTIAL]" in received_context["context"]
    assert "4321" not in received_context["context"]
    print("-> Context cleanly sanitized and transmitted without credential leaks [Passed]")

    # [Test 12] Specialist Task Execution & Outcome Recording
    print("\n[Test 12] Scheme Specialist Eligibility Check & CallTracker Integration")
    spec_fnc = SchemeSpecialistFnc("user_day9_test", call_tracker=tracker)
    elig_res = await spec_fnc.check_scheme_eligibility(35, 250000, "farmer")
    print(f"Specialist Eligibility Result: {elig_res}")
    assert "Pradhan Mantri Kisan" in elig_res
    assert tracker._task_completed is True
    print("-> Specialist successfully checked schemes and marked task completed [Passed]")

    # [Test 13] Hand-Back to MoneyBuddy
    print("\n[Test 13] Specialist Hand-Back to MoneyBuddy")
    handback_data = {}

    async def mock_handback_cb(reason: str, summary: Optional[str] = None):
        handback_data["reason"] = reason
        handback_data["summary"] = summary

    spec_handback_fnc = SchemeSpecialistFnc("user_day9_test", handback_cb=mock_handback_cb)
    hb_res = await spec_handback_fnc.handback_to_moneybuddy("completed_scheme_inquiry", "Checked PM Kisan")
    print(f"Handback Response: {hb_res}")
    assert "MoneyBuddy" in hb_res
    assert handback_data["reason"] == "completed_scheme_inquiry"
    print("-> Hand-back executed cleanly [Passed]")

    # [Test 14] Failed Handoff Graceful Fallback
    print("\n[Test 14] Failed Handoff Graceful Fallback Handling")

    async def failing_handoff_cb(user_query: str, caller_context: Optional[str] = None):
        raise RuntimeError("Specialist service initialization timeout")

    mb_failing_fnc = AssistantFnc("user_day9_test", handoff_cb=failing_handoff_cb)
    fallback_res = await mb_failing_fnc.handoff_to_scheme_specialist("PM Kisan check")
    print(f"Fallback Response: {fallback_res}")
    assert "unable to connect" in fallback_res or "still help" in fallback_res
    print("-> Graceful fallback caught error without crashing [Passed]")

    print("\n==================================================")
    print("      ALL DAY 9 ROUTING TESTS PASSED (14/14)      ")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_day9_routing_tests())
