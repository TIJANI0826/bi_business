from agno.agent import Agent
from agno.models.deepseek import DeepSeek
from agno.tools.sql import SQLTools
import frappe
import os
import openai
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO
from dotenv import load_dotenv
import requests
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
#from agno.vectordb.lancedb import LanceDb
from agno.vectordb.search import SearchType
from dotenv import load_dotenv
import typer
from rich.prompt import Prompt
from typing import Optional
#from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from agno.storage.sqlite import SqliteStorage
from agno.knowledge.json import JSONKnowledgeBase
from agno.vectordb.qdrant import Qdrant
from agno.agent import AgentKnowledge
from datetime import datetime

# Load environment variables
load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Database credentials
host = frappe.conf.db_host
user = frappe.conf.db_name
password = frappe.conf.db_password
db_name = frappe.conf.db_name
db_uri = f"mysql+pymysql://{user}:{password}@{host}/{db_name}"

# Lazy Initialization Variables
_storage = None
def get_storage():
    global _storage
    if _storage is None:
        start_time = datetime.now()
        _storage = SqliteStorage(
            table_name="agent_sessions",
            db_file="tmp/data.db",
        )
        print(f"Storage Initialized in {datetime.now() - start_time}")
    return _storage

# Define Visualization Agent
def generate_visualization(chart_type: str | None,
                           labels: list[str | int] | None,
                           datasets: list[dict[str, str | list | int]] | None):
    chart_config = {
        "type": chart_type,
        "data": {
            "labels": labels,
            "datasets": datasets
        }
    }

    response = requests.post("https://quickchart.io/chart/create",
                             json={"chart": chart_config})
    if response.status_code == 200:
        return response.json().get("url", "")
    else:
        return "Error generating chart"


# Define SQL Agent
sql_agent = Agent(
    name="SQL Agent",
    role="ERPNEXT SQL Expert. Fetches data from the database",
    instructions =["Remember in ERPNEXT and Frappe doctype start with tab e.g Sales Invoice will be tabSale Invoice"],
    model=DeepSeek(id="deepseek-chat", api_key=DEEPSEEK_API_KEY),
    tools=[SQLTools(db_url=db_uri, run_sql_query=True)],
)

visualization_agent = Agent(
    name="Visualization Agent",
    role="Generates visualizations based on dataset recieved",
    model=DeepSeek(id="deepseek-chat", api_key=DEEPSEEK_API_KEY),
    tools=[generate_visualization],
)

# Define Analysis Agent
analysis_agent = Agent(
    name="Analysis Agent",
    role=
    "Analyzes SQL query results, select an appropriate chart type and produce a necessary dataset",
    model=DeepSeek(id="deepseek-chat", api_key=DEEPSEEK_API_KEY),
)
# Define BI Agent Team
bi_agent_team = Agent(
    team=[sql_agent, analysis_agent, visualization_agent],
    model=DeepSeek(id="deepseek-chat", api_key=DEEPSEEK_API_KEY),
    instructions=["Fetch data, generate visuals, and provide analysis"],
    read_chat_history=True,  # This setting gives the model a tool to get chat history
    markdown=True,  # This setting tellss the model to format messages in markdown
    # add_chat_history_to_messages=True,
    # show_tool_calls=True,
    add_history_to_messages=True,  # Adds chat history to messages
    add_datetime_to_instructions=True,
    read_tool_call_history=True,
    #update_knowledge=True,
    num_history_responses=5,
    storage=get_storage()
)


@frappe.whitelist()
def run_agent(question):
    response = bi_agent_team.run(question)

    # Extract data if SQL query was executed
    #if response.content and "SELECT" in response.content:
    #    data = pd.read_sql(response.content, db_uri)
    #    visualization = generate_visualization(data)

    #    if visualization:
    #        return f"{response.content}\n\n{visualization}"

    return response.content

def check_run_agent_runtime(question):
    starttime = datetime.now()
    response = bi_agent_team.run(question)
    print(response.content)
    endtime = datetime.now()
    time_taken = endtime - starttime
    print(f"Runtime of the agent is {time_taken}")
    return time_taken
