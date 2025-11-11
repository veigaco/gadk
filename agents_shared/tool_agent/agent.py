import sys
sys.path.insert(0, '..')

from agents_shared import Agent, google_search

print("✅ ADK components imported successfully.")

root_agent = Agent(
    name="helpful_assistant",
    model="gemini-2.5-flash-lite",
    description="A simple agent that can answer general questions.",
    instruction="You are a helpful assistant. Use Google Search for current info or if unsure.",
    tools=[google_search],
)
