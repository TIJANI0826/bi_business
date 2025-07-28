from agno.agent import Agent
from agno.tools.sql import SQLTools
from dotenv import load_dotenv
import os
import frappe
import openai
from agno.models.deepseek import DeepSeek

openai.proxy = {
            "http": "http://127.0.0.1:7890",
            "https": "http://127.0.0.1:7890"
        }

load_dotenv()
openai.api_key=os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY=os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

host = frappe.conf.db_host
user = frappe.conf.db_name
password = frappe.conf.db_password
db_name = frappe.conf.db_name
db_url = f"mysql+pymysql://{user}:{password}@{host}/{db_name}"

agent = Agent(
    tools=[SQLTools(db_url=db_url)],
    show_tool_calls=True,
    markdown=True,
)
agent = Agent(model=DeepSeek(id="deepseek-chat",api_key=DEEPSEEK_API_KEY),tools=[SQLTools(db_url=db_url,run_sql_query=True)],
               show_tool_calls=False,
               update_knowledge=True,
               markdown=False,
              use_json_mode=True)

agent.print_response("Show me all tables in the database and their schemas")