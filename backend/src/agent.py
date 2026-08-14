import json
import logging
import os
import re
import time
from datetime import datetime
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
from livekit.plugins import deepgram, google, murf, noise_cancellation, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import db
from prompt import SYSTEM_PROMPT
from specialist import SchemeSpecialistAgent, SchemeSpecialistFnc

logger = logging.getLogger("agent")
load_dotenv(".env.local")


def init_schemes_data():
    import json
    data_path = os.path.join(os.path.dirname(__file__), "schemes_data.json")
    if not os.path.exists(data_path) and not os.path.exists(data_path + ".bak"):
        data = {
          "updated_at": "yesterday",
          "schemes": [
            {
              "id": "pmkisan",
              "name": "Pradhan Mantri Kisan Samman Nidhi",
              "max_income": 300000,
              "occupation": "farmer",
              "documents_required": ["Aadhaar Card", "Bank Account Details", "Land Holding Papers"]
            },
            {
              "id": "pmsby",
              "name": "Pradhan Mantri Suraksha Bima Yojana",
              "max_income": 500000,
              "occupation": "any",
              "documents_required": ["Aadhaar Card", "Savings Bank Account"]
            },
            {
              "id": "pmjjby",
              "name": "Pradhan Mantri Jeevan Jyoti Bima Yojana",
              "max_income": 500000,
              "occupation": "any",
              "documents_required": ["Aadhaar Card", "Savings Bank Account"]
            }
          ]
        }
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

init_schemes_data()


def init_agent_db():
    import sqlite3
    conn = sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS callers (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            facts TEXT,
            last_interaction TIMESTAMP,
            chat_history TEXT
        )
        """
    )
    conn.commit()
    conn.close()

init_agent_db()


def agent_get_caller(identifier: str) -> Optional[dict]:
    import sqlite3
    import json
    conn = sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT user_id, name, language_preference, facts, last_interaction, chat_history
        FROM callers
        WHERE user_id = ? OR name = ?
        """,
        (identifier, identifier),
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "user_id": row[0],
            "name": row[1],
            "language_preference": row[2],
            "facts": json.loads(row[3]) if row[3] else {},
            "last_interaction": row[4],
            "chat_history": json.loads(row[5]) if row[5] else [],
        }
    return None


def agent_save_caller(user_id: str, name: str, language_preference: str, facts: dict):
    import sqlite3
    import json
    from datetime import datetime
    conn = sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    facts_json = json.dumps(facts, ensure_ascii=False)
    now = datetime.now().isoformat()
    cursor.execute(
        """
        INSERT INTO callers (user_id, name, language_preference, facts, last_interaction)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name = excluded.name,
            language_preference = excluded.language_preference,
            facts = excluded.facts,
            last_interaction = excluded.last_interaction
        """,
        (user_id, name, language_preference, facts_json, now),
    )
    conn.commit()
    conn.close()


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
    # Convert internal variables to natural language equivalents
    text = text.replace("eligibility_confirmed", "eligibility confirmed")
    text = text.replace("eligibility_check_completed", "eligibility check completed")
    text = text.replace("scheme_info_provided", "scheme information provided")
    text = text.replace("documents_provided", "documents provided")
    text = text.replace("human_escalation_created", "escalation created")
    text = text.replace("pmkisan", "PM Kisan")
    text = text.replace("pmsby", "PMSBY")
    text = text.replace("pmjjby", "PMJJBY")
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


class CleanGoogleLLM(google.LLM):
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


# ── Day 8: Call Analytics Tracker ────────────────────────────────────────────


class CallTracker:
    """Tracks call lifecycle, outcome, latency for analytics.

    Success is explicit: a tool succeeding does NOT automatically mean the call
    was successful. The call is only marked successful when the agent has
    delivered the tool results to the user (agent speaks after a task-completing
    tool call).
    """

    def __init__(self, call_id: str, channel: str):
        self.call_id = call_id
        self.channel = channel  # 'browser' or 'sip'
        self.start_time = datetime.now().isoformat()
        self._start_mono = time.monotonic()
        self.language = "English"
        self.outcome: Optional[str] = None          # 'successful' or 'failed'
        self.failure_type: Optional[str] = None
        self.success_reason: Optional[str] = None
        self.financial_outcome: Optional[str] = None
        self.escalation_created = False
        self.user_spoke = False
        self._task_completed = False  # True when a task-completing tool returns data
        self._latency_samples: list[float] = []
        self._last_user_stop_time: Optional[float] = None

    def on_user_stopped_speaking(self):
        self.user_spoke = True
        self._last_user_stop_time = time.monotonic()

    def on_agent_started_speaking(self):
        if self._last_user_stop_time is not None:
            delta_ms = (time.monotonic() - self._last_user_stop_time) * 1000
            self._latency_samples.append(delta_ms)
            logger.info("Voice latency: %d ms", int(delta_ms))
            self._last_user_stop_time = None

    def on_agent_stopped_speaking(self):
        # If a task-completing tool succeeded AND the agent just finished
        # speaking the result to the user → call is successful.
        if self._task_completed and self.outcome is None:
            self.outcome = "successful"
            if not self.success_reason:
                self.success_reason = self.financial_outcome or "task_completed"

    def mark_task_completed(self, financial_outcome: str):
        """Called when a task-completing tool returns valid data.
        Does NOT mark the call successful yet — that happens only when
        the agent speaks the result to the user."""
        self._task_completed = True
        # Map to readable positive financial outcome labels
        if financial_outcome in ("eligibility_check_completed", "eligibility_confirmed"):
            self.financial_outcome = "Eligibility confirmed"
        elif financial_outcome == "scheme_info_provided":
            self.financial_outcome = "Scheme information provided"
        elif financial_outcome == "documents_provided":
            self.financial_outcome = "Required documents provided"
        else:
            self.financial_outcome = financial_outcome

    def mark_failed(self, failure_type: str):
        # If task was already completed, saying goodbye is NOT a failure
        if self._task_completed:
            if self.outcome is None:
                self.outcome = "successful"
                if not self.success_reason:
                    self.success_reason = self.financial_outcome or "task_completed"
            return
        if self.outcome is None:  # Don't overwrite existing outcome
            self.outcome = "failed"
            self.failure_type = failure_type

    def mark_escalation(self):
        self.escalation_created = True
        if self.financial_outcome is None or self.financial_outcome == "human_escalation_created":
            self.financial_outcome = "Escalation successfully created"
        # Escalation itself can be a successful task if it was the user's intent
        self._task_completed = True

    def finalize_and_record(self):
        """Called when the session ends. Writes analytics to DB."""
        end_time = datetime.now().isoformat()
        duration = time.monotonic() - self._start_mono

        # Apply defaults if outcome was never explicitly set
        if self.outcome is None:
            if not self.user_spoke:
                self.outcome = "failed"
                self.failure_type = "no_response"
            else:
                self.outcome = "failed"
                self.failure_type = "incomplete_task"

        avg_latency = None
        if self._latency_samples:
            avg_latency = round(
                sum(self._latency_samples) / len(self._latency_samples), 1
            )

        try:
            db.record_call_analytics(
                call_id=self.call_id,
                start_time=self.start_time,
                end_time=end_time,
                duration_seconds=round(duration, 1),
                channel=self.channel,
                language=self.language,
                outcome=self.outcome,
                failure_type=self.failure_type,
                success_reason=self.success_reason,
                financial_outcome=self.financial_outcome,
                escalation_created=self.escalation_created,
                avg_latency_ms=avg_latency,
            )
        except Exception as e:
            logger.error("Failed to record call analytics: %s", e)


class AssistantFnc:
    def __init__(
        self,
        participant_identity: str = "unknown_user",
        session_shutdown_cb = None,
        call_tracker: Optional[CallTracker] = None,
        handoff_cb = None,
    ):
        self.participant_identity = participant_identity
        self.session_shutdown_cb = session_shutdown_cb
        self.call_tracker = call_tracker
        self.handoff_cb = handoff_cb

    @llm.function_tool(
        description=(
            "Hand off the conversation to the Government Scheme Specialist. "
            "Call this ONLY when the caller's request genuinely requires in-depth government scheme information or eligibility checking. "
            "Do NOT call this for general banking, savings accounts, lost cards, fraud, human escalation, or opt-outs. "
            "Before calling, you MUST tell the caller: 'I will connect you with our government scheme specialist.'"
        )
    )
    async def handoff_to_scheme_specialist(
        self,
        user_query: str,
        caller_context: Optional[str] = None,
    ) -> str:
        logger.info("Main agent initiating handoff to Scheme Specialist. Query: %s", user_query)
        safe_query = db.sanitize_text(user_query) if hasattr(db, "sanitize_text") else user_query
        safe_context = db.sanitize_text(caller_context) if caller_context and hasattr(db, "sanitize_text") else caller_context

        if self.handoff_cb:
            try:
                import asyncio
                if asyncio.iscoroutinefunction(self.handoff_cb):
                    await self.handoff_cb(user_query=safe_query, caller_context=safe_context)
                else:
                    self.handoff_cb(user_query=safe_query, caller_context=safe_context)
                return "Connecting you to our government scheme specialist now."
            except Exception as e:
                logger.error("Handoff to specialist failed: %s", e)
                return "I am unable to connect you to the scheme specialist right now, but I can still help with the information I have."
        return "I will connect you with our government scheme specialist now."

    @llm.function_tool(
        description="Opt the caller out of future outbound calls and terminate the call immediately. Call this when the user says they want to stop receiving calls, opt out, or stop these calls."
    )
    async def opt_out(self) -> str:
        if self.call_tracker:
            self.call_tracker.mark_failed("user_declined")
        if self.session_shutdown_cb:
            import asyncio
            asyncio.create_task(self.session_shutdown_cb())
        return "Opt-out request processed. The call is terminating now. Goodbye."

    @llm.function_tool(
        description="Terminate the call immediately. Call this when the user says NO to hearing more details, or says goodbye to end the conversation."
    )
    async def terminate_call(self) -> str:
        if self.call_tracker:
            self.call_tracker.mark_failed("user_declined")
        if self.session_shutdown_cb:
            import asyncio
            asyncio.create_task(self.session_shutdown_cb())
        return "Call termination initiated."

    @llm.function_tool(
        description="Look up a returning caller by name or ID."
    )
    async def lookup_caller(self, identifier: Optional[str] = None) -> str:
        id_to_lookup = identifier or self.participant_identity
        caller = agent_get_caller(id_to_lookup)
        if caller:
            name = caller.get("name", "Unknown")
            facts = caller.get("facts", {})
            facts_str = ", ".join(f"{k}: {v}" for k, v in facts.items()) if facts else "none"
            return f"Returning caller found. Name: {name}. Past facts known: {facts_str}."
        return "Caller not found. This is a new user."

    @llm.function_tool(
        description="Save non-sensitive facts about the caller after asking for explicit permission."
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
        agent_save_caller(id_to_save, name, language_preference, facts_dict)
        return "Saved with consent. Only non-sensitive context was stored."



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
        # Day 8: Track escalation in analytics
        if self.call_tracker:
            self.call_tracker.mark_escalation()
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

    @ctx.room.on("track_published")
    def on_track_published(publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        logger.info(f"ROOM EVENT: Participant {participant.identity} published track {publication.sid} ({publication.kind})")

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track: rtc.RemoteTrack, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        logger.info(f"ROOM EVENT: Subscribed to track {publication.sid} ({track.kind}) from participant {participant.identity}")

    # Wait up to 60 seconds for the participant to answer and join the room
    import asyncio
    participant_identity = "unknown_user"
    for _ in range(600):  # wait for 60 seconds max
        if ctx.room.remote_participants:
            participant_identity = next(iter(ctx.room.remote_participants.values())).identity
            break
        await asyncio.sleep(0.1)

    # Determine channel and initialize CallTracker
    channel = "browser"
    if ctx.room.remote_participants:
        part = next(iter(ctx.room.remote_participants.values()))
        if part.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP or part.identity.startswith("sip"):
            channel = "sip"
    call_id = ctx.room.name or f"call-{int(time.time())}"
    call_tracker = CallTracker(call_id=call_id, channel=channel)

    async def shutdown_session():
        call_tracker.finalize_and_record()
        await asyncio.sleep(4.0)
        await session.aclose()

    assistant_agent = Assistant(participant_identity=participant_identity)

    async def handle_handback_to_moneybuddy(reason: str, summary: Optional[str] = None):
        logger.info("HANDBACK: Switching session agent back to MoneyBuddy. Reason: %s", reason)
        await ctx.room.local_participant.set_attributes({"active_agent": "moneybuddy"})
        if hasattr(session, "tts") and hasattr(session.tts, "update_options"):
            session.tts.update_options(voice="Anisha")
        session.update_agent(assistant_agent)
        session.generate_reply(
            instructions="You are MoneyBuddy. You have just returned from the government scheme specialist. Politely ask the caller: 'Is there anything else I can help you with?' in English (or 'क्या मैं आपकी किसी और चीज़ में मदद कर सकती हूँ?' if caller speaks Hindi).",
            allow_interruptions=True,
        )

    async def handle_handoff_to_specialist(user_query: str, caller_context: Optional[str] = None):
        logger.info("HANDOFF: Switching session agent to Scheme Specialist. Query: %s", user_query)
        specialist_agent = SchemeSpecialistAgent(
            participant_identity=participant_identity,
            call_tracker=call_tracker,
            handback_cb=handle_handback_to_moneybuddy,
        )
        await ctx.room.local_participant.set_attributes({"active_agent": "specialist"})
        if hasattr(session, "tts") and hasattr(session.tts, "update_options"):
            session.tts.update_options(voice="Nikhil")
        session.update_agent(specialist_agent)

        caller_lang = call_tracker.language if call_tracker and call_tracker.language else "English"
        if caller_lang.lower() == "hindi":
            intro = "नमस्ते, मैं सरकारी योजना विशेषज्ञ हूँ। मैं सरकारी योजनाओं की पात्रता, लाभ, दस्तावेज़ और आवेदन की जानकारी में आपकी मदद कर सकती हूँ।"
        else:
            intro = "Hi, I'm the Government Scheme Specialist. I can help you with government scheme eligibility, benefits, documents, and application information."
        
        # Eliminate latency by directly speaking the intro
        session.chat_ctx.append(llm.ChatMessage(role="assistant", content=intro))
        session.say(intro, allow_interruptions=True)

        prompt_instruction = (
            f"You are MoneyBuddy's government scheme specialist. The caller was transferred to you with this request: '{user_query}'. "
            "You have just introduced yourself. Now, directly address their scheme question or eligibility using natural language. "
            "NEVER speak internal variable names like 'pmkisan' or 'eligibility_confirmed'."
        )
        session.generate_reply(
            instructions=prompt_instruction,
            allow_interruptions=True,
        )

    assistant_tools = AssistantFnc(
        participant_identity,
        session_shutdown_cb=shutdown_session,
        call_tracker=call_tracker,
        handoff_cb=handle_handoff_to_specialist,
    )

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=CleanGoogleLLM(
            model="gemini-3.5-flash-lite",
            api_key=os.environ.get("GOOGLE_API_KEY")
        ),
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
        tools=llm.find_function_tools(assistant_tools),
    )

    silence_count = 0
    silence_task: Optional[asyncio.Task] = None

    def cancel_silence_timer():
        nonlocal silence_task
        if silence_task and not silence_task.done():
            silence_task.cancel()
            silence_task = None

    async def _handle_silence_timeout():
        nonlocal silence_count
        try:
            await asyncio.sleep(10.0)
            silence_count += 1
            if silence_count == 1:
                logger.info("SILENCE: First timeout - re-prompting user ('Are you still there?')")
                session.generate_reply(
                    instructions="Politely ask the caller: 'Are you still there?' in English (or 'क्या आप अभी भी सुन रहे हैं?' if caller speaks Hindi).",
                    allow_interruptions=True,
                )
            elif silence_count == 2:
                logger.info("SILENCE: Second timeout - re-prompting user ('Would you like to continue?')")
                session.generate_reply(
                    instructions="Politely ask: 'Would you like to continue?' in English (or 'क्या आप बातचीत जारी रखना चाहते हैं?' if caller speaks Hindi).",
                    allow_interruptions=True,
                )
            else:
                logger.info("SILENCE: Continued silence - gracefully ending call and recording no_response.")
                call_tracker.mark_failed("no_response")
                await shutdown_session()
        except asyncio.CancelledError:
            pass

    @session.on("user_started_speaking")
    def on_user_started_speaking():
        nonlocal silence_count
        cancel_silence_timer()
        silence_count = 0
        logger.info("EVENT: User started speaking")

    @session.on("user_stopped_speaking")
    def on_user_stopped_speaking():
        logger.info("EVENT: User stopped speaking")
        call_tracker.on_user_stopped_speaking()

    @session.on("user_speech_committed")
    def on_user_speech_committed(msg: llm.ChatMessage):
        logger.info(f"EVENT: User speech committed: {msg.content}")

    @session.on("agent_started_speaking")
    def on_agent_started_speaking():
        cancel_silence_timer()
        logger.info("EVENT: Agent started speaking")
        call_tracker.on_agent_started_speaking()

    @session.on("agent_stopped_speaking")
    def on_agent_stopped_speaking():
        logger.info("EVENT: Agent stopped speaking")
        call_tracker.on_agent_stopped_speaking()
        cancel_silence_timer()
        silence_task = asyncio.create_task(_handle_silence_timeout())

    @ctx.room.on("disconnected")
    def on_room_disconnected(reason=None):
        cancel_silence_timer()
        logger.info(f"ROOM EVENT: Disconnected ({reason})")
        call_tracker.finalize_and_record()

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=assistant_agent,
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
    # Set the participant identity metadata for the frontend
    await ctx.room.local_participant.set_attributes({"active_agent": "moneybuddy"})

    # Wait a moment for media/RTP channels to establish on SIP calls
    await asyncio.sleep(2.0)
    # Force the agent to generate a reply
    logger.info("Triggering initial greeting...")
    session.generate_reply(
        instructions="Greet the caller in English by saying exactly: 'Hello, this is MoneyBuddy, I'm calling because a financial scheme you may already be eligible for has an upcoming deadline, would you like to know more, you can say yes or no, and you can tell me if you don't want to receive these calls.'",
        allow_interruptions=False
    )



if __name__ == "__main__":
    cli.run_app(server)
