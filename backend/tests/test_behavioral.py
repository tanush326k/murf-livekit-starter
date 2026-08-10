import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from agent import AssistantFnc
import db

async def run_tests():
    print("--- Running Behavioral Tests ---")
    
    # Clean DB for fresh start
    conn = db.sqlite3.connect(db.DB_PATH)
    conn.execute("DELETE FROM callers WHERE user_id IN ('test_caller_A', 'test_caller_B')")
    conn.commit()
    conn.close()

    fnc_A = AssistantFnc("test_caller_A")
    fnc_B = AssistantFnc("test_caller_B")

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

    print("\n--- All Tests Passed ---")

if __name__ == "__main__":
    asyncio.run(run_tests())
