"""
Connection test — verifies Supabase credentials and basic connectivity.
Run with:  python test_connection.py
"""
import sys
import os

# Make habit_app importable from the project root
sys.path.insert(0, os.path.dirname(__file__))

from habit_app.utils.constants import SUPABASE_URL, SUPABASE_ANON_KEY
from habit_app.services.supabase_service import SupabaseService

def test_connection():
    print(f"[1] Connecting to: {SUPABASE_URL}")

    try:
        client = SupabaseService.get_client()
        print("[2] Supabase client created OK")
    except Exception as e:
        print(f"[FAIL] Could not create client: {e}")
        return

    # Test 1: auth.get_user() with no session (should return None, not crash)
    try:
        user_response = client.auth.get_user()
        print(f"[3] auth.get_user() responded OK (user={user_response})")
    except Exception as e:
        # A missing/no-session error is expected here — network is fine
        print(f"[3] auth.get_user() raised (expected if no session): {e}")

    # Test 2: try a simple REST query against a table that should exist
    # We use a table name that Supabase will reject if RLS is blocking, but
    # it will still return a proper HTTP response (not a network failure).
    try:
        response = client.table("habits").select("id").limit(1).execute()
        print(f"[4] REST query to 'habits' table OK — data={response.data}")
    except Exception as e:
        msg = str(e)
        if "relation" in msg.lower() or "does not exist" in msg.lower():
            print(f"[4] Table 'habits' not yet created (expected) — network is working: {e}")
        elif "jwt" in msg.lower() or "auth" in msg.lower() or "permission" in msg.lower() or "policy" in msg.lower():
            print(f"[4] Auth/RLS error (expected without login) — network is working: {e}")
        else:
            print(f"[4] Unexpected error querying 'habits': {e}")

    print("\n=== Connection test complete ===")

if __name__ == "__main__":
    test_connection()
