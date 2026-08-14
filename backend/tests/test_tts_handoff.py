import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

class MockTTS:
    def __init__(self, voice: str):
        self.voice = voice

    def update_options(self, voice=None, **kwargs):
        if voice:
            self.voice = voice


class MockSession:
    def __init__(self):
        self.tts = MockTTS(voice="Anisha")
        self.current_agent = None

    def update_agent(self, agent):
        self.current_agent = agent
        
    def generate_reply(self, instructions, allow_interruptions):
        pass


async def test_voice_handoff():
    print("--- Running TTS Voice Handoff Test ---")
    
    # Simulate the environment inside my_agent
    session = MockSession()
    assert session.tts.voice == "Anisha", "Default voice should be Anisha"
    
    # 1. MoneyBuddy is the active agent initially
    from agent import Assistant
    from specialist import SchemeSpecialistAgent
    
    assistant_agent = Assistant("test_user")
    session.update_agent(assistant_agent)
    
    # 2. Handoff to specialist
    # This is normally done in handle_handoff_to_specialist
    # Let's recreate the logic used in handle_handoff_to_specialist
    async def handle_handback_to_moneybuddy(reason: str, summary=None):
        if hasattr(session, "tts") and hasattr(session.tts, "update_options"):
            session.tts.update_options(voice="Anisha")
        session.update_agent(assistant_agent)
        session.generate_reply(instructions="...", allow_interruptions=True)

    async def handle_handoff_to_specialist(user_query: str, caller_context=None):
        specialist_agent = SchemeSpecialistAgent(
            participant_identity="test_user",
            handback_cb=handle_handback_to_moneybuddy,
        )
        if hasattr(session, "tts") and hasattr(session.tts, "update_options"):
            session.tts.update_options(voice="Nikhil")
        session.update_agent(specialist_agent)
        session.generate_reply(instructions="...", allow_interruptions=True)
    
    await handle_handoff_to_specialist("PM Kisan eligibility")
    
    # Verify voice changed to Nikhil
    assert session.tts.voice == "Nikhil", f"Expected voice Nikhil after handoff, got {session.tts.voice}"
    assert isinstance(session.current_agent, SchemeSpecialistAgent), "Active agent should be Specialist"
    print("MoneyBuddy -> Specialist (Nikhil): [Passed]")
    
    # 3. Handback to MoneyBuddy
    await session.current_agent.specialist_tools.handback_to_moneybuddy("done", "summary")
    
    # Verify voice changed back to Anisha
    assert session.tts.voice == "Anisha", f"Expected voice Anisha after handback, got {session.tts.voice}"
    assert isinstance(session.current_agent, Assistant), "Active agent should be MoneyBuddy"
    print("Specialist -> MoneyBuddy (Anisha): [Passed]")
    
    print("--- TTS Voice Handoff Test Complete ---")


if __name__ == "__main__":
    asyncio.run(test_voice_handoff())
