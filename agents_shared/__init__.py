# Common imports for all agent folders
# Day 1 imports
from google.adk.agents.llm_agent import Agent
from google.adk.agents import SequentialAgent, ParallelAgent, LoopAgent
from google.adk.runners import Runner, InMemoryRunner
from google.adk.tools import AgentTool, FunctionTool, google_search
from google.genai import types
# Day 2 imports, incremental
# 2a
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.sessions import InMemorySessionService, DatabaseSessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.tools import ToolContext
from google.adk.tools import load_memory, preload_memory
from google.adk.code_executors import BuiltInCodeExecutor
# 2b
import uuid
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.apps.app import App, ResumabilityConfig
from google.adk.tools.function_tool import FunctionTool
from mcp import StdioServerParameters
# Day 3 imports, incremental
from typing import Any, Dict
from google.adk.apps.app import EventsCompactionConfig
from google.adk.sessions import DatabaseSessionService

print("✅ ADK components imported successfully.")

APP_NAME = "default"  # Application
USER_ID = "default"  # User
SESSION = "default"  # Session
MODEL_NAME = "gemini-2.5-flash-lite"

# Day 2 - Helper functions
def show_python_code_and_result(response):
    for i in range(len(response)):
        # Check if the response contains a valid function call result from the code executor
        if (
            (response[i].content.parts)
            and (response[i].content.parts[0])
            and (response[i].content.parts[0].function_response)
            and (response[i].content.parts[0].function_response.response)
        ):
            response_code = response[i].content.parts[0].function_response.response
            if "result" in response_code and response_code["result"] != "```":
                if "tool_code" in response_code["result"]:
                    print(
                        "Generated Python Code >> ",
                        response_code["result"].replace("tool_code", ""),
                    )
                else:
                    print("Generated Python Response >> ", response_code["result"])

retry_config = types.HttpRetryOptions(
    # Retry configuration
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

def check_for_approval(events):
    """Check if events contain an approval request.

    Returns:
        dict with approval details or None
    """
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if (
                    part.function_call
                    and part.function_call.name == "adk_request_confirmation"
                ):
                    return {
                        "approval_id": part.function_call.id,
                        "invocation_id": event.invocation_id,
                    }
    return None

def print_agent_response(events):
    """Print agent's text responses from events."""
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Agent > {part.text}")

def create_approval_response(approval_info, approved):
    """Create approval response message."""
    confirmation_response = types.FunctionResponse(
        id=approval_info["approval_id"],
        name="adk_request_confirmation",
        response={"confirmed": approved},
    )
    return types.Content(
        role="user", parts=[types.Part(function_response=confirmation_response)]
    )

# Day 3 - Helper functions
async def run_session(
    runner_instance: Runner,
    session_service: InMemorySessionService,
    user_id: str = USER_ID,
    model_name: str = MODEL_NAME,
    user_queries: list[str] | str = None,
    session_name: str = SESSION):
    """Run a session asynchronously.

    Args:
        runner_instance: The runner instance
        user_queries: The user queries
        session_name: The session name
    """
    print(f"\n ### Session: {session_name}")

    # Get app name from the Runner
    app_name = runner_instance.app_name

    # Attempt to create a new session or retrieve an existing one
    try:
        session = await session_service.create_session(
            app_name=app_name, 
            user_id=user_id, 
            session_id=session_name
        )
    except:
        session = await session_service.get_session(
            app_name=app_name, 
            user_id=user_id, 
            session_id=session_name
        )

    # Process queries if provided
    if user_queries:
        # Convert single query to list for uniform processing
        if type(user_queries) == str:
            user_queries = [user_queries]

        # Process each query in the list sequentially
        for query in user_queries:
            print(f"\nUser > {query}")

            # Convert the query string to the ADK Content format
            query = types.Content(role="user", parts=[types.Part(text=query)])

            # Stream the agent's response asynchronously
            async for event in runner_instance.run_async(
                user_id=user_id, session_id=session.id, new_message=query
            ):
                # Check if the event contains valid content
                if event.content and event.content.parts:
                    # Filter out empty or "None" responses before printing
                    if (
                        event.content.parts[0].text != "None"
                        and event.content.parts[0].text
                    ):
                        print(f"{model_name} > ", event.content.parts[0].text)
    else:
        print("No queries!")

print("✅ Helper functions defined.")