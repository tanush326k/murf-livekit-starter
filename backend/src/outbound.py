import asyncio
import os
import sys
import time
from dotenv import load_dotenv
from livekit import api

load_dotenv(".env.local")

async def main():
    # Read variables from environment
    livekit_url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    sip_trunk_id = os.getenv("LIVEKIT_SIP_TRUNK_ID")
    destination_number = os.getenv("DESTINATION_PHONE_NUMBER")
    
    # We use a specific room name for the outbound call.
    # When the agent runs, it should connect to this room if not using dispatch,
    # or if using dispatch, LiveKit will start the agent in this room.
    room_name = f"outbound-call-{int(time.time())}"

    if not all([livekit_url, api_key, api_secret, sip_trunk_id, destination_number]):
        print("Missing required environment variables. Please check .env.local.")
        print("Ensure LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_SIP_TRUNK_ID, and DESTINATION_PHONE_NUMBER are set.")
        sys.exit(1)

    # Initialize LiveKit API
    lk_api = api.LiveKitAPI(livekit_url, api_key, api_secret)

    try:
        # Extract SIP user if it's a full URI (e.g., sip:user@domain.com -> user)
        call_to = destination_number
        if call_to.startswith("sip:"):
            call_to = call_to[4:]
        if "@" in call_to:
            call_to = call_to.split("@")[0]

        # Create a SIP outbound call
        print(f"Initiating SIP call to {call_to} using trunk {sip_trunk_id}...")
        
        req = api.CreateSIPParticipantRequest(
            sip_trunk_id=sip_trunk_id,
            sip_call_to=call_to,
            room_name=room_name,
            participant_identity="sip-caller",
            participant_name="User",
            wait_until_answered=True
        )
        
        await lk_api.sip.create_sip_participant(req)
        
        # Dispatch the agent to the room explicitly
        print(f"Dispatching agent to room {room_name}...")
        dispatch_req = api.CreateAgentDispatchRequest(
            agent_name="my-agent",
            room=room_name
        )
        await lk_api.agent_dispatch.create_dispatch(dispatch_req)
        
        print(f"Call initiated successfully.")
        print(f"The agent should join the room '{room_name}' to interact with the user.")
        
    except Exception as e:
        print(f"Error initiating SIP call: {e}")
    finally:
        await lk_api.aclose()

if __name__ == "__main__":
    asyncio.run(main())
