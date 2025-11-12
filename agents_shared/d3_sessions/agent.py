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

from agents_shared import ToolContext, types, LlmAgent, Gemini, FunctionTool, Agent
from agents_shared import App, ResumabilityConfig, Runner, InMemorySessionService
from agents_shared import retry_config, uuid, print_agent_response, check_for_approval, create_approval_response, run_session


APP_NAME = "default"  # Application
USER_ID = "default"  # User
SESSION = "default"  # Session

MODEL_NAME = "gemini-2.5-flash-lite"


# Step 1: Create the LLM Agent
root_agent = Agent(
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    name="text_chat_bot",
    description="A text chatbot",  # Description of the agent's purpose
)

# Step 2: Set up Session Management
# InMemorySessionService stores conversations in RAM (temporary)
session_service = InMemorySessionService()

# Step 3: Create the Runner
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

print("✅ Stateful agent initialized!")
print(f"   - Application: {APP_NAME}")
print(f"   - User: {USER_ID}")
print(f"   - Using: {session_service.__class__.__name__}")

# Run a conversation with two queries in the same session
# Notice: Both queries are part of the SAME session, so context is maintained


async def main():
    """Main function to run the session."""
    await run_session(
        runner_instance=runner,
        session_service=session_service,
        user_id=USER_ID,
        model_name=MODEL_NAME,
        user_queries=
        [
            "Hi, I am Sam! What is the capital of United States?", 
            "Hello! What is my name?"
        ], 
        session_name="stateful-agentic-session")

if __name__ == "__main__":
    asyncio.run(main())