from agno.agent import Agent, RunResponse  # noqa
from agno.models.deepseek import DeepSeek
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv
import os
import openai

load_dotenv()
openai.api_key=os.environ["OPENAI_API_KEY"]
DEEPSEEK_API_KEY=os.environ["DEEPSEEK_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

#agent = Agent(model=DeepSeek(id="deepseek-chat",api_key=DEEPSEEK_API_KEY), markdown=True)

# Get the response in a variable
# run: RunResponse = agent.run("Share a 2 sentence horror story")
# print(run.content)

# Print the response in the terminal
#agent.print_response("Share a 2 sentence horror story")


agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    description="You are an enthusiastic news reporter with a flair for storytelling!",
    markdown=True
)
agent.print_response("Tell me about a breaking news story from New York.", stream=True)