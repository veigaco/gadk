import sys
import os
import asyncio
from dotenv import load_dotenv
import sqlite3

# Add parent directory to path so we can import agents_shared
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, grandparent_dir)

# Load environment variables from .env file in agents_shared folder
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

from agents_shared import LlmAgent, Gemini
from agents_shared import Runner, DatabaseSessionService, App, EventsCompactionConfig
from agents_shared import retry_config, run_session
from agents_shared import (MODEL_NAME, APP_NAME, USER_ID)


# Step 1: Create the same agent (notice we use LlmAgent this time)
chatbot_agent = LlmAgent(
    model=Gemini(model=MODEL_NAME, retry_options=retry_config),
    name="text_chat_bot",
    description="A text chatbot with persistent memory",
)

# Step 2: Switch to DatabaseSessionService
# SQLite database will be created automatically
db_url = "sqlite:///my_agent_data.db"  # Local SQLite file
session_service = DatabaseSessionService(db_url=db_url)

# Step 3: Create a new runner with persistent storage
runner = Runner(agent=chatbot_agent, app_name=APP_NAME, session_service=session_service)

print("✅ Upgraded to persistent sessions!")
print(f"   - Database: my_agent_data.db")
print(f"   - Sessions will survive restarts!")


def check_data_in_db():
    with sqlite3.connect("my_agent_data.db") as connection:
        cursor = connection.cursor()
        result = cursor.execute(
            "select app_name, session_id, author, content from events"
        )
        print([_[0] for _ in result.description])
        for each in result.fetchall():
            print(each)


# Re-define our app with Events Compaction enabled
research_app_compacting = App(
    name="research_app_compacting",
    root_agent=chatbot_agent,
    # This is the new part!
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=3,  # Trigger compaction every 3 invocations
        overlap_size=1,  # Keep 1 previous turn for context
    ),
)

# Create a new runner for our upgraded app
research_runner_compacting = Runner(
    app=research_app_compacting, session_service=session_service
)


print("✅ Research App upgraded with Events Compaction!")



async def main():
    """Main function to run the session."""
    
    """ 
    # Part 3
    await run_session(
        runner,
        session_service=session_service,
        user_queries=
        ["Hi, I am Sam! What is the capital of the United States?", "Hello! What is my name?"],
        session_name="test-db-session-01",
    )

    await run_session(
    runner,
    session_service=session_service,
    user_queries=
    ["What is the capital of India?", "Hello! What is my name?"],
    session_name="test-db-session-01",
    )

    await run_session(
    runner, ["Hello! What is my name?"], "test-db-session-02"
    )  # Note, we are using new session name

    check_data_in_db()
    """
    
    # Part 4
    # Turn 1
    await run_session(
        research_runner_compacting,
        session_service=session_service,
        user_queries=[ "What is the latest news about AI in healthcare?"],
        session_name="compaction_demo"
    )

    # Turn 2
    await run_session(
        research_runner_compacting,
        session_service=session_service,
        user_queries=["Are there any new developments in drug discovery?"],
        session_name="compaction_demo"
    )

    # Turn 3 - Compaction should trigger after this turn!
    await run_session(
        research_runner_compacting,
        session_service=session_service,
        user_queries=["Tell me more about the second development you found."],
        session_name="compaction_demo",
    )

    # Turn 4
    await run_session(
        research_runner_compacting,
        session_service=session_service,
        user_queries=["Who are the main companies involved in that?"],
        session_name="compaction_demo",
    )


    # Get the final session state
    final_session = await session_service.get_session(
        app_name=research_runner_compacting.app_name,
        user_id=USER_ID,
        session_id="compaction_demo",
    )

    print("--- Searching for Compaction Summary Event ---")
    found_summary = False
    for event in final_session.events:
        # Compaction events have a 'compaction' attribute
        if event.actions and event.actions.compaction:
            print("\n✅ SUCCESS! Found the Compaction Event:")
            print(f"  Author: {event.author}")
            print(f"\n Compacted information: {event}")
            found_summary = True
            break

    if not found_summary:
        print(
            "\n❌ No compaction event found. Try increasing the number of turns in the demo."
        )    



if __name__ == "__main__":
    asyncio.run(main())