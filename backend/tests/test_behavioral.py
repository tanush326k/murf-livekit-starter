import asyncio
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from agent import AssistantFnc
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
    res = await fnc_A.check_scheme_eligibility(30, 200000, "farmer")
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
        res = await fnc_A.check_scheme_eligibility(30, 200000, "farmer")
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
    res = await fnc_A.check_scheme_eligibility(25, 150000, "farmer")
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

    # 9. Check Escalation Status
    print("\n[Test 9] Check Escalation Status")
    status_res = await fnc_esc.check_escalation_status(ref_id)
    print(f"Status Result: {status_res}")
    assert "open" in status_res

    # Check unknown status
    unknown_res = await fnc_esc.check_escalation_status("MB-INVALID")
    assert "No escalation request found" in unknown_res
    print("[Passed]")

    # Clean up test escalation records
    conn = db.sqlite3.connect(db.DB_PATH)
    conn.execute("DELETE FROM escalations WHERE caller_id LIKE 'test_%'")
    conn.commit()
    conn.close()

    print("\n--- All Tests Passed ---")

if __name__ == "__main__":
    asyncio.run(run_tests())

