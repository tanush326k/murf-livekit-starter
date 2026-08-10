import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from livekit.agents import llm
from agent import AssistantFnc, CleanOpenAILLM, SYSTEM_PROMPT

async def run_e2e_test():
    print("--- Running LLM E2E Tests ---")

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Skipping E2E test: GROQ_API_KEY not found.")
        return

    # 1. Test Scheme Eligibility Tool Invocation
    print("\n[Test 1] Scheme Tool Invocation")
    tools = AssistantFnc("test_caller_C")
    func_tools = llm.find_function_tools(tools)
    
    model = CleanOpenAILLM(
        model="llama-3.1-8b-instant",
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key
    )

    chat_ctx = llm.ChatContext()
    # Adding messages might vary by SDK version, try the robust approach
    if hasattr(chat_ctx, "messages") and not callable(chat_ctx.messages):
        chat_ctx.messages.append(llm.ChatMessage(text=SYSTEM_PROMPT, role="system"))
        chat_ctx.messages.append(llm.ChatMessage(text="I am a 30 year old farmer with 200000 income. What government schemes am I eligible for?", role="user"))
    elif hasattr(chat_ctx, "append"):
        chat_ctx.append(text=SYSTEM_PROMPT, role="system")
        chat_ctx.append(text="I am a 30 year old farmer with 200000 income. What government schemes am I eligible for?", role="user")

    stream = model.chat(chat_ctx=chat_ctx, fnc_ctx=func_tools)
    response = ""
    async for chunk in stream:
        if chunk.delta.content:
            response += chunk.delta.content

    print(f"Agent Response:\n{response}\n")
    print(f"Tool calls made during this stream: {stream.called_functions}")
    
    if len(stream.called_functions) > 0:
        print("✅ LLM independently decided to invoke a tool.")
        func_call = stream.called_functions[0]
        assert func_call.call_info.function.name == "check_scheme_eligibility"
        print("✅ LLM invoked check_scheme_eligibility.")
    else:
        print("❌ LLM failed to invoke tool. Response was:", response)


if __name__ == "__main__":
    asyncio.run(run_e2e_test())
