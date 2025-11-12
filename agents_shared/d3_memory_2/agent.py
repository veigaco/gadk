import sys
import os
import asyncio
from dotenv import load_dotenv

# Add parent directory to path so we can import agents_shared
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, grandparent_dir)

# Load environment variables from .env file in agents_shared folder
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

from agents_shared import LlmAgent, Gemini
from agents_shared import Runner, App, InMemorySessionService, InMemoryMemoryService, load_memory
from agents_shared import retry_config, run_session, preload_memory
from agents_shared import (MODEL_NAME, APP_NAME, USER_ID)

memory_service = (
    InMemoryMemoryService()
)

# Define constants used throughout the notebook
APP_NAME = "MemoryDemoApp"
USER_ID = "demo_user"

async def auto_save_to_memory(callback_context):
    """Automatically save session to memory after each agent turn."""
    await callback_context._invocation_context.memory_service.add_session_to_memory(
        callback_context._invocation_context.session
    )

print("✅ Callback created.")


# Agent with automatic memory saving
auto_memory_agent = LlmAgent(
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    name="AutoMemoryAgent",
    instruction="Answer user questions.",
    tools=[preload_memory],
    after_agent_callback=auto_save_to_memory,  # Saves after each turn!
)

print("✅ Agent created with automatic memory saving!")

# Create Session Service
session_service = InMemorySessionService()  # Handles conversations


# Create a runner for the auto-save agent
# This connects our automated agent to the session and memory services
auto_runner = Runner(
    agent=auto_memory_agent,  # Use the agent with callback + preload_memory
    app_name=APP_NAME,
    session_service=session_service,  # Same services from Section 3
    memory_service=memory_service,
)

print("✅ Runner created.")


async def main(): 
    # Test 1: Tell the agent about a gift (first conversation)
    # The callback will automatically save this to memory when the turn completes
    await run_session(
        auto_runner,
        session_service=session_service,
        user_id=USER_ID,
        user_queries=["I gifted a new toy to my nephew on his 1st birthday!"],
        session_name="auto-save-test",
    )

    # Test 2: Ask about the gift in a NEW session (second conversation)
    # The agent should retrieve the memory using preload_memory and answer correctly
    await run_session(
        auto_runner,
        session_service=session_service,
        user_id=USER_ID,
        user_queries=["What did I gift my nephew?"],
        session_name="auto-save-test-2",  # Different session ID - proves memory works across sessions!
    )


if __name__ == "__main__":
    asyncio.run(main())