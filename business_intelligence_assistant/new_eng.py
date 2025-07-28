import frappe
import json
import os
import openai
import ast
import re
from dotenv import load_dotenv
from typing import List
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_sql_query_chain
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel, Field
from operator import itemgetter
from langchain_deepseek import ChatDeepSeek

# Load OpenAI API Key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Get ERPNext Database Credentials
host = frappe.conf.db_host
user = frappe.conf.db_name
password = frappe.conf.db_password
db_name = frappe.conf.db_name
print(host,user,password,db_name)

# Connect to ERPNext MariaDB database
db_uri = f"mysql+pymysql://{user}:{password}@{host}/{db_name}"
db = SQLDatabase.from_uri(db_uri)
db_schema = db.get_table_info()


#llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=openai.api_key)
llm = ChatDeepSeek(
            model_name="deepseek-chat",
            temperature=0,
            api_key=frappe.conf.get("deepseek_api_key")
        )

def query_as_list(db, query):
    """Execute SQL query and return results as a list."""
    try:
        res = db.run(query)
        res = [el for sub in ast.literal_eval(res) for el in sub if el]
        res = [re.sub(r"\b\d+\b", "", string).strip() for string in res]
        return res
    except Exception as e:
        return [f"Error executing query: {str(e)}"]

def get_database_schema():
    """Retrieve all table names and structure from the database."""
    tables = db.get_usable_table_names()
    schema = "\n".join([f"{table}: {db.get_table_info([table])}" for table in tables])
    return schema
def get_table_schema():
    """Fetch and return the schema of all tables in the database."""
    tables = frappe.db.get_tables()
    schema = {}
    
    for table in tables:
        columns = frappe.db.get_table_columns_description(table)
        schema[table] = [col['Field'] for col in columns]

    return json.dumps(schema, indent=2)
def generate_sql_query(user_question):
    """Generate SQL query from user input using LangChain."""
    table_schema = get_database_schema()

    system_prompt = """You are an SQL expert generating queries for ERPNext (MariaDB).
    Given a user question, create a syntactically correct SQL query.

    Use the following database schema:
    {table_info}

    Ensure:
    1. The query is valid for MariaDB.
    2. Use table and column names as specified in the schema.
    3. Use LIMIT {top_k} for queries returning multiple rows.

    Return at most {top_k} rows.
    """


    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])

    query_chain = create_sql_query_chain(llm, db, prompt=prompt)
    query = query_chain.invoke({"question": user_question, "top_k": 5, "table_info": table_schema})
    
    
    return query