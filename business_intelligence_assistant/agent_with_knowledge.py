from agno.agent import Agent
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from dotenv import load_dotenv
import openai
from agno.models.deepseek import DeepSeek
import os
openai.proxy = {
            "http": "http://127.0.0.1:7890",
            "https": "http://127.0.0.1:7890"
        }
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
print(openai.api_key)
api_key = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY=os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

#db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

agent = Agent(
    model=DeepSeek(id="deepseek-chat",api_key=DEEPSEEK_API_KEY),
    # Add a tool to read chat history.
    read_chat_history=True,
    show_tool_calls=True,
    markdown=True,
    # debug_mode=True,
)
agent.print_response("How do I make chicken and galangal in coconut milk soup", stream=True)
agent.print_response("What was my last question?", stream=True)