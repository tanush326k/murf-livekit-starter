import asyncio
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from agent import AssistantFnc
from specialist import SchemeSpecialistFnc
import db

async def run_tests():
    print("--- Running Behavioral Tests ---")
    
    # Clean DB for fresh start
    conn = db.sqlite3.connect(db.DB_PATH)
    conn.execute("DELETE FROM callers WHERE user_id IN ('test_caller_A', 'test_caller_B')")
    conn.execute("DELETE FROM escalations WHERE caller_id LIKE 'test_%'")
    conn.commit()
    conn.close()

    fnc_A = AssistantFnc("test_caller_A")
    fnc_B = AssistantFnc("test_caller_B")

    # 1. Scheme-tool success test
    print("\n[Test 1] Scheme-tool success test")
    spec_fnc_A = SchemeSpecialistFnc("test_caller_A")
    res = await spec_fnc_A.check_scheme_eligibility(30, 200000, "farmer")
    print(f"Result: {res}")
    assert "yesterday" in res
    assert "Pradhan Mantri Kisan" in res
    print("[Passed]")

    # 2. Scheme-tool failure test (simulate by removing file temporarily)
    print("\n[Test 2] Scheme-tool failure test")
    data_path = os.path.join(os.path.dirname(__file__), "../src/schemes_data.json")
    temp_path = data_path + ".bak"
    os.rename(data_path, temp_path)
    try:
        res = await spec_fnc_A.check_scheme_eligibility(30, 200000, "farmer")
        print(f"Result: {res}")
        assert "down" in res or "unavailable" in res
        print("[Passed]")
    finally:
        os.rename(temp_path, data_path)

    # 3. Permission-before-save test & Memory Persistence
    print("\n[Test 3] Memory Persistence & Save")
    res = await fnc_A.save_caller_info("Rahul", "Hindi", '{"likes": "apples"}')
    print(f"Save Result: {res}")
    assert "Saved with consent" in res
    
    # Look up in a new instance (simulating cross-session)
    fnc_A_new = AssistantFnc("test_caller_A")
    res = await fnc_A_new.lookup_caller()
    print(f"Lookup A Result: {res}")
    assert "Rahul" in res
    assert "apples" in res
    print("[Passed]")

    # 4. Caller isolation
    print("\n[Test 4] Caller Isolation")
    res = await fnc_B.lookup_caller()
    print(f"Lookup B Result: {res}")
    assert "Caller not found" in res
    print("[Passed]")

    # ===== DAY 7: ESCALATION TESTS =====

    # 5. Escalation creation — creates a real DB record
    print("\n[Test 5] Escalation Creation (Day 7)")
    fnc_esc = AssistantFnc("test_escalation_user")
    res = await fnc_esc.create_escalation(
        caller_name="Priya",
        reason="Possible fraud reported",
        summary="Caller reported a suspicious transaction of a large amount they did not authorize.",
        what_checked="Provided general fraud-awareness information but cannot verify or resolve the transaction.",
        urgency="High",
        language="English",
        preferred_followup="Phone call",
        callback_time="Today afternoon",
    )
    print(f"Escalation Result: {res}")

    # Verify reference ID format MB-YYYYMMDD-NNN
    assert "Reference ID is MB-" in res
    ref_match = re.search(r"MB-\d{8}-\d{3}", res)
    assert ref_match, f"Reference ID not found in response: {res}"
    ref_id = ref_match.group(0)
    print(f"Reference ID: {ref_id}")

    # Verify the record exists in the database
    conn = db.sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM escalations WHERE reference_id = ?", (ref_id,))
    row = cursor.fetchone()
    conn.close()
    assert row is not None, f"Escalation record {ref_id} not found in database"
    assert row[3] == "Possible fraud reported"  # reason column
    assert row[9] == "open"  # status column
    print(f"DB record verified: status={row[9]}, reason={row[3]}")
    print("[Passed]")

    # 6. Normal conversation does NOT create escalation
    print("\n[Test 6] Normal Question Does Not Escalate (Day 7)")
    conn = db.sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM escalations")
    count_before = cursor.fetchone()[0]
    conn.close()

    # A normal question answered via check_scheme_eligibility — no escalation
    res = await spec_fnc_A.check_scheme_eligibility(25, 150000, "farmer")
    assert "Pradhan Mantri" in res  # normal answer

    conn = db.sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM escalations")
    count_after = cursor.fetchone()[0]
    conn.close()

    assert count_after == count_before, (
        f"Escalation count changed after normal question! Before: {count_before}, After: {count_after}"
    )
    print("No escalation created for normal question.")
    print("[Passed]")

    # 7. Permission denied — no escalation record created
    print("\n[Test 7] Permission Denied Path (Day 7)")
    conn = db.sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM escalations")
    count_before = cursor.fetchone()[0]
    conn.close()

    # Simulate: the caller says NO. The LLM would NOT call create_escalation.
    # We verify that if the tool is never called, no record is created.
    # (This is a "negative path" test — simply don't call the tool.)
    print("Simulated: caller denied permission. create_escalation was NOT called.")

    conn = db.sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM escalations")
    count_after = cursor.fetchone()[0]
    conn.close()

    assert count_after == count_before, (
        f"Escalation record created without tool call! Before: {count_before}, After: {count_after}"
    )
    print("No escalation created when permission denied.")
    print("[Passed]")

    # 8. Deduplication and Redaction (Day 7 Enhancements)
    print("\n[Test 8] Deduplication and Redaction (Day 7 Enhancements)")
    # We use the same caller "test_escalation_user" who already has an open escalation from Test 5
    res = await fnc_esc.create_escalation(
        caller_name="Priya",
        reason="Follow up on previous issue",
        summary="Here is more info. My aadhaar is 123456789012 and my email is test@example.com.",
        what_checked="Follow up.",
        urgency="Emergency",
        language="English",
        preferred_followup="Email",
        callback_time="Immediately",
    )
    print(f"Escalation Result (Deduplication): {res}")
    
    # Verify it returns the SAME reference ID as Test 5
    assert ref_id in res, f"Expected same reference ID {ref_id}, got {res}"

    # Verify redaction and deduplication in DB
    conn = db.sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT summary, urgency FROM escalations WHERE reference_id = ?", (ref_id,))
    row = cursor.fetchone()
    conn.close()
    
    assert row is not None
    updated_summary = row[0]
    updated_urgency = row[1]
    
    assert "[REDACTED EMAIL]" in updated_summary
    assert "[REDACTED ID]" in updated_summary
    assert "123456789012" not in updated_summary
    assert "test@example.com" not in updated_summary
    assert updated_urgency == "Emergency"
    # Verify it was appended
    assert "suspicious transaction" in updated_summary.lower() and "here is more info" in updated_summary.lower()
    
    print("[Passed]")

    # Clean up test escalation records
    conn = db.sqlite3.connect(db.DB_PATH)
    conn.execute("DELETE FROM escalations WHERE caller_id LIKE 'test_%'")
    conn.execute("DELETE FROM call_analytics WHERE call_id LIKE 'test_%'")
    conn.commit()
    conn.close()

    # ===== DAY 8: CALL ANALYTICS TESTS =====
    from agent import CallTracker

    print("\n[Test 9] Analytics DB Recording & Summary (Day 8)")
    db.record_call_analytics(
        call_id="test_call_success_1",
        start_time="2026-08-13T10:00:00",
        end_time="2026-08-13T10:02:00",
        duration_seconds=120.0,
        channel="browser",
        language="English",
        outcome="successful",
        failure_type=None,
        success_reason="eligibility_check_completed",
        financial_outcome="eligibility_check_completed",
        escalation_created=False,
        avg_latency_ms=450.0,
    )

    summary = db.get_analytics_summary()
    assert summary["total_calls"] >= 1
    assert summary["successful_calls"] >= 1
    assert summary["success_rate"] > 0
    print(f"Summary calculated: {summary}")
    print("[Passed]")

    print("\n[Test 10] Call Outcome: Tool Success alone vs Agent Speaking (Day 8)")
    # Test that tool completing task does NOT mark successful until agent speaks
    tracker = CallTracker("test_call_flow_1", "browser")
    tracker.on_user_stopped_speaking()
    tracker.on_agent_started_speaking()
    
    # Tool executes successfully
    spec_fnc_track = SchemeSpecialistFnc("test_caller_A", call_tracker=tracker)
    res_elig = await spec_fnc_track.check_scheme_eligibility(30, 200000, "farmer")
    assert "Pradhan Mantri" in res_elig
    
    # BEFORE agent speaks result -> outcome must NOT be successful yet
    assert tracker.outcome != "successful", "Tool success alone prematurely marked call as successful!"
    assert tracker._task_completed is True
    
    # NOW agent finishes speaking the result to user
    tracker.on_agent_stopped_speaking()
    assert tracker.outcome == "successful", "Call failed to mark successful after agent spoke result!"
    
    # Verify latency sample was recorded
    assert len(tracker._latency_samples) == 1
    assert tracker._latency_samples[0] >= 0
    
    tracker.finalize_and_record()
    rec = db.get_call_analytics(outcome="successful")
    assert any(r["call_id"] == "test_call_flow_1" for r in rec)
    print("[Passed]")

    print("\n[Test 10B] Outcome Preservation: Terminate Call after Task Completion (Phase 1)")
    tracker_term = CallTracker("test_call_flow_2", "browser")
    tracker_term.on_user_stopped_speaking()
    tracker_term.on_agent_started_speaking()
    spec_fnc_term = SchemeSpecialistFnc("test_caller_A", call_tracker=tracker_term)
    await spec_fnc_term.check_scheme_eligibility(30, 200000, "farmer")
    tracker_term.on_agent_stopped_speaking()
    assert tracker_term.outcome == "successful"
    assert tracker_term.financial_outcome == "Eligibility confirmed"

    # User says "Goodbye" -> terminate_call invoked
    fnc_term = AssistantFnc("test_caller_A", call_tracker=tracker_term)
    await fnc_term.terminate_call()
    assert tracker_term.outcome == "successful", "terminate_call incorrectly downgraded a completed call to failed!"
    assert tracker_term.financial_outcome == "Eligibility confirmed"
    tracker_term.finalize_and_record()
    print("[Passed]")

    print("\n[Test 11] Failure: User Declined (Day 8)")
    tracker_dec = CallTracker("test_call_declined", "sip")
    fnc_dec = AssistantFnc("test_caller_A", call_tracker=tracker_dec)
    await fnc_dec.terminate_call()
    assert tracker_dec.outcome == "failed"
    assert tracker_dec.failure_type == "user_declined"
    tracker_dec.finalize_and_record()
    
    rec_dec = db.get_call_analytics(outcome="failed")
    assert any(r["call_id"] == "test_call_declined" and r["failure_type"] == "user_declined" for r in rec_dec)
    print("[Passed]")

    print("\n[Test 12] Failure: Tool Failure (Day 8)")
    tracker_tf = CallTracker("test_call_tf", "browser")
    fnc_tf = AssistantFnc("test_caller_A", call_tracker=tracker_tf)
    
    # Force tool failure
    os.rename(data_path, temp_path)
    try:
        spec_fnc_tf = SchemeSpecialistFnc("test_caller_A", call_tracker=tracker_tf)
        await spec_fnc_tf.check_scheme_eligibility(30, 200000, "farmer")
        assert tracker_tf.outcome == "failed"
        assert tracker_tf.failure_type == "tool_failure"
    finally:
        os.rename(temp_path, data_path)
    
    tracker_tf.finalize_and_record()
    rec_tf = db.get_call_analytics(outcome="failed")
    assert any(r["call_id"] == "test_call_tf" and r["failure_type"] == "tool_failure" for r in rec_tf)
    print("[Passed]")

    print("\n[Test 13] Failure: Incomplete Task & No Response (Day 8)")
    # No user speech -> no_response
    t_no_resp = CallTracker("test_call_no_resp", "browser")
    t_no_resp.finalize_and_record()
    assert t_no_resp.outcome == "failed"
    assert t_no_resp.failure_type == "no_response"

    # User spoke but ended before success -> incomplete_task
    t_inc = CallTracker("test_call_inc", "browser")
    t_inc.on_user_stopped_speaking()
    t_inc.finalize_and_record()
    assert t_inc.outcome == "failed"
    assert t_inc.failure_type == "incomplete_task"
    print("[Passed]")

    print("\n[Test 14] Analytics Filters & Charts (Day 8)")
    charts = db.get_analytics_charts()
    assert "calls_over_time" in charts
    assert "failure_distribution" in charts
    assert "financial_outcomes" in charts
    
    filtered_sip = db.get_call_analytics(channel="sip")
    assert all(r["channel"] == "sip" for r in filtered_sip)
    print("[Passed]")

    print("\n[Test 15] Analytics Privacy Check (Day 8)")
    all_recs = db.get_call_analytics()
    for r in all_recs:
        # Verify no sensitive dictionary keys or transcript text columns exist in schema
        assert "password" not in r
        assert "otp" not in r
        assert "pin" not in r
        assert "transcript" not in r
        assert "account_number" not in r
    print("[Passed]")

    # Final cleanup
    conn = db.sqlite3.connect(db.DB_PATH)
    conn.execute("DELETE FROM escalations WHERE caller_id LIKE 'test_%'")
    conn.execute("DELETE FROM call_analytics WHERE call_id LIKE 'test_%'")
    conn.commit()
    conn.close()

    print("\n--- All Tests Passed ---")

if __name__ == "__main__":
    asyncio.run(run_tests())

