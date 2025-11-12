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

from agents_shared import types, LlmAgent, Gemini, Runner, InMemorySessionService
from agents_shared import retry_config, Dict, Any, ToolContext, run_session

# Define scope levels for state keys (following best practices)
USER_NAME_SCOPE_LEVELS = ("temp", "user", "app")


# This demonstrates how tools can write to session state using tool_context.
# The 'user:' prefix indicates this is user-specific data.
def save_userinfo(
    tool_context: ToolContext, user_name: str, country: str
) -> Dict[str, Any]:
    """
    Tool to record and save user name and country in session state.

    Args:
        user_name: The username to store in session state
        country: The name of the user's country
    """
    # Write to session state using the 'user:' prefix for user data
    tool_context.state["user:name"] = user_name
    tool_context.state["user:country"] = country

    return {"status": "success"}


# This demonstrates how tools can read from session state.
def retrieve_userinfo(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Tool to retrieve user name and country from session state.
    """
    # Read from session state
    user_name = tool_context.state.get("user:name", "Username not found")
    country = tool_context.state.get("user:country", "Country not found")

    return {"status": "success", "user_name": user_name, "country": country}


print("✅ Tools created.")

# Configuration
APP_NAME = "default"
USER_ID = "default"
MODEL_NAME = "gemini-2.5-flash-lite"

# Create an agent with session state tools
root_agent = LlmAgent(
    model=Gemini(model=MODEL_NAME, retry_options=retry_config),
    name="text_chat_bot",
    description="""A text chatbot.
    Tools for managing user context:
    * To record username and country when provided use `save_userinfo` tool. 
    * To fetch username and country when required use `retrieve_userinfo` tool.
    """,
    tools=[save_userinfo, retrieve_userinfo],  # Provide the tools to the agent
)

# Set up session service and runner
session_service = InMemorySessionService()
runner = Runner(agent=root_agent, session_service=session_service, app_name="default")

print("✅ Agent with session state tools initialized!")


async def main():
    # Test conversation demonstrating session state
    await run_session(
        runner,
        session_service=session_service,
        user_queries=
        [
            "Hi there, how are you doing today? What is my name?",  # Agent shouldn't know the name yet
            "My name is Sam. I'm from Poland.",  # Provide name - agent should save it
            "What is my name? Which country am I from?",  # Agent should recall from session state
        ],
        session_name="state-demo-session",
    )

    # Retrieve the session and inspect its state
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id="state-demo-session"
    )

    print("Session State Contents:")
    print(session.state)
    print("\n🔍 Notice the 'user:name' and 'user:country' keys storing our data!")

    # Start a completely new session - the agent won't know our name
    await run_session(
        runner,
        ["Hi there, how are you doing today? What is my name?"],
        "new-isolated-session",
    ) # Expected: The agent won't know the name because this is a different session

    # Clean up any existing database to start fresh (if Notebook is restarted)
    import os

    if os.path.exists("my_agent_data.db"):
        os.remove("my_agent_data.db")
    print("✅ Cleaned up old database files")


if __name__ == "__main__":
    asyncio.run(main())