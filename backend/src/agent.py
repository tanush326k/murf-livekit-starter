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
            "Create a human-help escalation request when the caller reports: "
            "1) possible fraud or unauthorized activity, or 2) lost or stolen credit card. "
            "Urgency levels can be 'low', 'medium', 'high', or 'emergency'. "
            "CRITICAL: You MUST ask the caller for explicit permission BEFORE calling this tool. "
            "If the caller says no, do NOT call this tool. "
            "Never include passwords, OTPs, PINs, full account numbers, card numbers, CVV, Aadhaar, or PAN."
        )
    )
    async def create_escalation(
        self,
        caller_name: str,
        reason: str,
        summary: str,
        what_checked: str,
        urgency: str,
        language: str,
        preferred_followup: str,
        callback_time: str,
    ) -> str:
        reference_id = db.create_escalation(
            caller_id=self.participant_identity,
            caller_name=caller_name,
            reason=reason,
            summary=summary,
            what_checked=what_checked,
            urgency=urgency,
            language=language,
            preferred_followup=preferred_followup,
            callback_time=callback_time,
        )
        return (
            f"Escalation created successfully. Reference ID is {reference_id}. "
            f"Tell the caller their request has been escalated to a human agent, and their "
            f"reference ID for tracking purposes is {reference_id}. "
            f"Explain that a human team member will review it, but do NOT promise they will reply immediately."
        )


class Assistant(Agent):
    def __init__(self, participant_identity: str) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
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

    # Wait up to 60 seconds for the SIP caller to answer and join the room
    import asyncio
    participant_identity = "unknown_user"
    for _ in range(600): # wait for 60 seconds max
        if ctx.room.remote_participants:
            participant_identity = next(iter(ctx.room.remote_participants.values())).identity
            break
        await asyncio.sleep(0.1)

    assistant_tools = AssistantFnc(participant_identity)

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-2", language="multi"),
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
    # Force the agent to generate a reply
    logger.info("Triggering initial greeting...")
    session.generate_reply(
        instructions="Greet the caller naturally as MoneyBuddy."
    )



if __name__ == "__main__":
    cli.run_app(server)
