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
from agents_shared import Runner, App, InMemorySessionService, InMemoryMemoryService
from agents_shared import retry_config, run_session, load_memory
from agents_shared import (MODEL_NAME, APP_NAME, USER_ID)


memory_service = (
    InMemoryMemoryService()
)  # ADK's built-in Memory Service for development and testing


# Define constants used throughout the notebook
APP_NAME = "MemoryDemoApp"
USER_ID = "demo_user"


async def main():

    # Create agent
    user_agent = LlmAgent(
        model=Gemini(model=MODEL_NAME, retry_options=retry_config),
        name="MemoryDemoAgent",
        instruction="Answer user questions in simple words.",
    )

    print("✅ Agent created")

    # Create Session Service
    session_service = InMemorySessionService()  # Handles conversations

    # Create runner with BOTH services
    runner = Runner(
        agent=user_agent,
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,  # Memory service is now available!
    )

    print("✅ Agent and Runner created with memory support!")

    # User tells agent about their favorite color
    await run_session(
        runner,
        session_service=session_service,
        user_id=USER_ID,
        user_queries=["My favorite color is blue-green. Can you write a Haiku about it?"],
        session_name="conversation-01",  # Session ID
    )

    session = await session_service.get_session(
        app_name=APP_NAME, 
        user_id=USER_ID, 
        session_id="conversation-01"
    )

    # Let's see what's in the session
    print("📝 Session contains:")
    for event in session.events:
        text = (
            event.content.parts[0].text[:60]
            if event.content and event.content.parts
            else "(empty)"
        )
        print(f"  {event.content.role}: {text}...")

    # This is the key method!
    await memory_service.add_session_to_memory(session)

    print("✅ Session added to memory!")

    # Create agent
    user_agent = LlmAgent(
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        name="MemoryDemoAgent",
        instruction="Answer user questions in simple words. Use load_memory tool if you need to recall past conversations.",
        tools=[
            load_memory
        ],  # Agent now has access to Memory and can search it whenever it decides to!
    )

    print("✅ Agent with load_memory tool created.")

    # Create a new runner with the updated agent
    runner = Runner(
        agent=user_agent,
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,
    )

    await run_session(
        runner, 
        session_service=session_service,
        user_id=USER_ID,
        user_queries=["What is my favorite color?"], 
        session_name="color-test")

    await run_session(runner, 
        session_service=session_service,
        user_id=USER_ID,
        user_queries=["My birthday is on March 15th."], 
        session_name="birthday-session-01")

    # Manually save the session to memory
    birthday_session = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id="birthday-session-01"
    )

    await memory_service.add_session_to_memory(birthday_session)

    print("✅ Birthday session saved to memory!")

    # Test retrieval in a NEW session
    await run_session(
        runner, 
        session_service=session_service,
        user_id=USER_ID,
        user_queries=["When is my birthday?"], 
        session_name="birthday-session-02"  # Different session ID
    )

    # Search for color preferences
    search_response = await memory_service.search_memory(
        app_name=APP_NAME, user_id=USER_ID, query="What is the user's favorite color?"
    )

    print("🔍 Search Results:")
    print(f"  Found {len(search_response.memories)} relevant memories")
    print()

    for memory in search_response.memories:
        if memory.content and memory.content.parts:
            text = memory.content.parts[0].text[:80]
            print(f"  [{memory.author}]: {text}...")


if __name__ == "__main__":
    asyncio.run(main())