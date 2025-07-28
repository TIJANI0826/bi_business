from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.embedder.openai import OpenAIEmbedder
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.agent import Agent,RunResponse
from agno.tools.sql import SQLTools
import frappe
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO
from datetime import datetime, timedelta
from langchain.chains import create_sql_query_chain
from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import sqlglot
from langchain.chains import create_sql_query_chain
from langchain_core.runnables import RunnablePassthrough
from langchain_community.utilities import SQLDatabase
from agno.models.deepseek import DeepSeek
import openai
import re
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key=os.environ["OPENAI_API_KEY"]
DEEPSEEK_API_KEY=os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

host = frappe.conf.db_host
user = frappe.conf.db_name
password = frappe.conf.db_password
db_name = frappe.conf.db_name
db_url = f"mysql+pymysql://{user}:{password}@{host}/{db_name}"
sql_toolkit = SQLTools(db_url=db_url)

#query_agent = Agent(
#    name="Query Agent",
#    role="Convert natural language requests into SQL queries for ERPNext",
#    model=OpenAIChat(id="gpt-4o"),
#    tools=[sql_toolkit],
#    instructions="Generate secure, efficient SQL queries that match the user's request.",
#    show_tool_calls=True,
#    markdown=True,
#)

#analysis_agent = Agent(
#    name="Analysis Agent",
#    role="Analyze and interpret ERPNext query results",
#    model=OpenAIChat(id="gpt-4o"),
#    instructions="Provide insights and summaries based on query results, highlighting trends and anomalies.",
#    show_tool_calls=True,
#    markdown=True,
#)

#visualization_agent = Agent(
#    name="Visualization Agent",
#    role="Generate visual representations of query results",
#    model=OpenAIChat(id="gpt-4o"),
#    instructions="Create clear, relevant charts and graphs based on query data.",
#    show_tool_calls=True,
#    markdown=True,
#)

@frappe.whitelist()
def run_agent(question):
    # Connect to ERPNext MariaDB database
    #agent = Agent(model=DeepSeek(id="deepseek-chat",api_key=DEEPSEEK_API_KEY), markdown=True)
    #agent.print_response("Share a 2 sentence horror story")
    db_uri = f"mysql+pymysql://{user}:{password}@{host}/{db_name}"
    agent = Agent(model=DeepSeek(id="deepseek-chat",api_key=DEEPSEEK_API_KEY),tools=[SQLTools(db_url=db_uri,run_sql_query=True)],
               show_tool_calls=False,
               update_knowledge=True,
               markdown=False,
              use_json_mode=True)
    response = agent.run(question)
    return response.content
print(run_agent("how many customers do we have"))