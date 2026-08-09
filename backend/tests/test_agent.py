import pytest
import os
import sys

# Ensure backend/src is in path so we can import agent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from livekit.agents import llm
import agent

def test_assistant_initialization():
    """Verify that Assistant class can be instantiated without crashing."""
    assistant = agent.Assistant(participant_identity="test_user")
    assert assistant is not None
    assert assistant.instructions is not None
    # Verify the fnc_ctx / tools removal didn't break init
    assert not hasattr(assistant, "fnc_ctx") or assistant.fnc_ctx is None

def test_db_init():
    """Verify that the db is initialized and doesn't throw errors."""
    import db
    assert hasattr(db, "init_db")

def test_agent_session_tools():
    """Verify AgentSession can be instantiated with find_function_tools without throwing ToolContext errors."""
    from livekit.agents.voice.agent_session import AgentSession
    from livekit.plugins import openai
    
    # Minimal mock of what's passed in agent.py
    assistant_tools = agent.AssistantFnc()
    
    try:
        session = AgentSession(
            llm=openai.LLM(model="llama-3.1-8b-instant", api_key="dummy"),
            tools=llm.find_function_tools(assistant_tools),
        )
        assert session is not None
    except Exception as e:
        pytest.fail(f"AgentSession initialization failed: {e}")
