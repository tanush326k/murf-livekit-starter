import json
import logging
import os
import re
from typing import Optional

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    UserInputTranscribedEvent,
    cli,
    llm,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, murf, noise_cancellation, openai, silero

import db
from prompt import SYSTEM_PROMPT

logger = logging.getLogger("agent")
load_dotenv(".env.local")


def clean_speech_text(text: str) -> str:
    if not text:
        return text
    # Remove asterisks, underscores, backticks, tildes, parentheses
    text = re.sub(r'[*_`~()]', '', text)
    # Replace bullet points at start of line with a comma and space for a pause
    text = re.sub(r'(?m)^[-+*]\s+', ', ', text)
    # Replace list numbers at start of line like "1." with "1, "
    text = re.sub(r'(?m)^(\d+)\.\s+', r'\1, ', text)
    # Remove hashtags
    text = re.sub(r'#+\s*', '', text)
    # Replace colons after words with commas for natural phrasing
    text = re.sub(r'(\w+):\s*', r'\1, ', text)
    # Strip LLM tool call leakage (e.g. from Llama-3)
    text = re.sub(r'\(function=[a-zA-Z_]+>[^)]*\)?', '', text)
    text = re.sub(r'\{[^{}]*\}', '', text) # Strip raw JSON objects just in case
    return text


class CleanOpenAILLM(openai.LLM):
    def chat(self, *args, **kwargs):
        stream = super().chat(*args, **kwargs)
        
        class CleanStream(stream.__class__):
            async def __anext__(self):
                chunk = await super().__anext__()
                if chunk.delta and chunk.delta.content:
                    chunk.delta.content = clean_speech_text(chunk.delta.content)
                return chunk
                
        stream.__class__ = CleanStream
        return stream



class AssistantFnc:
    def __init__(self, participant_identity: str = "unknown_user"):
        self.participant_identity = participant_identity

    @llm.function_tool(
        description=(
            "Look up a returning caller by name or ID so the agent can greet them by name "
            "and continue from their last saved context. Never return sensitive information."
        )
    )
    async def lookup_caller(self, identifier: Optional[str] = None) -> str:
        id_to_lookup = identifier or self.participant_identity
        caller = db.get_caller(id_to_lookup)
        if caller:
            name = caller.get("name", "Unknown")
            facts = caller.get("facts", {})
            facts_str = ", ".join(f"{k}: {v}" for k, v in facts.items()) if facts else "none"
            return f"Returning caller found. Name: {name}. Past facts known: {facts_str}."
        return "Caller not found. This is a new user."

    @llm.function_tool(
        description=(
            "Save only non-sensitive facts about the caller after asking for explicit permission. "
            "Never save account numbers, IDs, OTPs, UPI identifiers, PINs, or credential data."
        )
    )
    async def save_caller_info(
        self,
        name: str,
        language_preference: str,
        facts: str,
    ) -> str:
        try:
            facts_dict = json.loads(facts)
        except json.JSONDecodeError:
            facts_dict = {"notes": facts}

        id_to_save = self.participant_identity
        if not id_to_save or not name:
            return "Missing name. Nothing was saved."

        cleaned = db.sanitize_facts(facts_dict)
        if not cleaned:
            return "No safe facts to save. The data was sensitive or empty, so nothing was stored."

        db.save_caller(id_to_save, name, language_preference, cleaned)
        return "Saved with consent. Only non-sensitive context was stored."

    @llm.function_tool(
        description=(
            "Check user's eligibility for government schemes based on their age, annual income, and occupation. "
            "Returns a natural language list of eligible schemes, the document checklist, and when the data was last updated. "
            "Call this tool immediately when the user asks what schemes they qualify for. Do NOT call this tool for general questions."
        )
    )
    async def check_scheme_eligibility(self, age: int, annual_income: float, occupation: str) -> str:
        try:
            data_path = os.path.join(os.path.dirname(__file__), "schemes_data.json")
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            updated_at = data.get("updated_at", "an unknown date")
            schemes = data.get("schemes", [])
            
            eligible = []
            for s in schemes:
                # simplified mock logic: income must be <= max_income
                if annual_income <= s.get("max_income", float('inf')):
                    eligible.append(s)
            
            if not eligible:
                return f"Based on our database (updated {updated_at}), I couldn't find any specific schemes for those details."
            
            response = f"Based on our database (updated {updated_at}), you are eligible for {len(eligible)} scheme(s): "
            for idx, e in enumerate(eligible, 1):
                docs = ", ".join(e.get("documents_required", []))
                response += f"{idx}. {e['name']}. You will need these documents: {docs}. "
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to load schemes data: {e}")
            return "The scheme database is currently down. Please apologize to the user and suggest they try again later."


class Assistant(Agent):
    def __init__(self, participant_identity: str) -> None:
        super().__init__(instructions=SYSTEM_PROMPT + "\n[SYSTEM EVENT] A user has just joined the room. You MUST immediately call `lookup_caller` to see if they are returning. Greet them by name if found.")
        self.participant_identity = participant_identity

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Join the room and connect to the user first so remote participants are visible
    await ctx.connect()

    # Get the user's identity robustly with a brief retry/poll loop
    import asyncio
    participant_identity = "unknown_user"
    for _ in range(10): # try for 1 second max
        if ctx.room.remote_participants:
            participant_identity = next(iter(ctx.room.remote_participants.values())).identity
            break
        await asyncio.sleep(0.1)

    assistant_tools = AssistantFnc(participant_identity)

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=CleanOpenAILLM(
            model="llama-3.1-8b-instant",
            base_url="https://api.groq.com/openai/v1",
            api_key=os.environ.get("GROQ_API_KEY")
        ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
           tts=murf.TTS(
                voice="Anisha",
                style="Conversation",
                speed=15,
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # The turn-detector ONNX model is not reliable on Windows and crashes worker startup;
        # leaving it out keeps the agent bootable while still using VAD for session flow.
        vad=ctx.proc.userdata["vad"],
        tools=llm.find_function_tools(assistant_tools),
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(participant_identity=participant_identity),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )
    
    # Force the agent to generate a reply based on the new context
    session.generate_reply()

    # Save chat history continuously when the conversation updates
    @session.on("conversation_item_added")
    def on_conversation_item_added(event):
        # Serialize the chat history to JSON-friendly format
        serialized_history = []
        for msg in session.chat_ctx.messages:
            if isinstance(msg.content, str):
                serialized_history.append({
                    "role": msg.role,
                    "content": msg.content,
                    "name": msg.name
                })
        # Save to DB asynchronously (or we can block, it's fast enough in SQLite)
        db.save_chat_history(participant_identity, serialized_history)


if __name__ == "__main__":
    cli.run_app(server)
