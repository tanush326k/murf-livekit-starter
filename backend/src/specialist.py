import json
import logging
import os
from typing import Any, Callable, Optional

from livekit.agents import Agent, llm
from specialist_prompt import SCHEME_SPECIALIST_PROMPT

logger = logging.getLogger("specialist")


class SchemeSpecialistFnc:
    """Tool set for the Government Scheme Specialist agent.
    Reuses existing schemes_data.json and CallTracker for zero data duplication.
    """

    def __init__(
        self,
        participant_identity: str = "unknown_user",
        call_tracker: Optional[Any] = None,
        handback_cb: Optional[Callable[..., Any]] = None,
    ):
        self.participant_identity = participant_identity
        self.call_tracker = call_tracker
        self.handback_cb = handback_cb

    @llm.function_tool(
        description="Check caller eligibility for Indian government financial schemes based on age, annual income, and occupation. Reuses the grounded schemes database."
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
                if annual_income <= s.get("max_income", float("inf")):
                    eligible.append(s)

            if not eligible:
                if self.call_tracker:
                    self.call_tracker.mark_task_completed("eligibility_check_completed")
                return f"Based on our database (updated {updated_at}), I couldn't find any specific schemes for those details."

            response = f"Based on our database (updated {updated_at}), you are eligible for {len(eligible)} scheme(s): "
            for idx, e in enumerate(eligible, 1):
                docs = ", ".join(e.get("documents_required", []))
                response += f"{idx}. {e['name']}. You will need these documents: {docs}. "

            if self.call_tracker:
                self.call_tracker.mark_task_completed("eligibility_check_completed")

            return response

        except Exception as e:
            logger.error("Failed to load schemes data in specialist: %s", e)
            if self.call_tracker:
                self.call_tracker.mark_failed("tool_failure")
            return "The scheme database is currently down. Please apologize to the user and suggest they try again later."

    @llm.function_tool(
        description=(
            "Hand the conversation back to the main MoneyBuddy assistant. "
            "Call this when: 1) scheme assistance is complete, 2) the caller changes the topic to general banking or cards, "
            "3) the caller reports fraud or lost card, or 4) the caller requests human support or wants to opt out."
        )
    )
    async def handback_to_moneybuddy(self, reason: str, summary: Optional[str] = None) -> str:
        logger.info("Specialist handback triggered. Reason: %s, Summary: %s", reason, summary)
        if self.handback_cb:
            try:
                import asyncio
                if asyncio.iscoroutinefunction(self.handback_cb):
                    await self.handback_cb(reason=reason, summary=summary)
                else:
                    self.handback_cb(reason=reason, summary=summary)
            except Exception as e:
                logger.error("Error executing handback callback: %s", e)
        return "I will pass you back to MoneyBuddy now."


class SchemeSpecialistAgent(Agent):
    """Specialist Agent dedicated exclusively to Indian government financial schemes."""

    def __init__(
        self,
        participant_identity: str = "unknown_user",
        call_tracker: Optional[Any] = None,
        handback_cb: Optional[Callable[..., Any]] = None,
        custom_instructions: Optional[str] = None,
        tts: Optional[Any] = None,
    ) -> None:
        self.participant_identity = participant_identity
        self.specialist_tools = SchemeSpecialistFnc(
            participant_identity=participant_identity,
            call_tracker=call_tracker,
            handback_cb=handback_cb,
        )
        instructions = custom_instructions or SCHEME_SPECIALIST_PROMPT
        kwargs = {
            "instructions": instructions,
            "tools": llm.find_function_tools(self.specialist_tools),
        }
        if tts is not None:
            kwargs["tts"] = tts
        super().__init__(**kwargs)
