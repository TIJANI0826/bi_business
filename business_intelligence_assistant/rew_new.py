import frappe
import openai
import json
import matplotlib.pyplot as plt
import io
import base64
from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import sqlglot
from langchain.chains import create_sql_query_chain
from langchain_core.runnables import RunnablePassthrough
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain


def generate_sql_query(user_input):
    """Converts user input to SQL query using OpenAI API."""
    openai.api_key = frappe.conf.get("openai_api_key")
    prompt = f"Convert the following request into an SQL query for ERPNext: {user_input}"
    
    llm = ChatDeepSeek(
            model_name="deepseek-chat",
            temperature=0,
            api_key=frappe.conf.get("deepseek_api_key")
        )
    
    sql_chain = LLMChain(llm=llm, prompt=prompt)
        
    # Generate SQL
    sql_output = sql_chain.invoke({"user_input": user_input})
   
    print(sql_output)
    return sql_output

def execute_sql_query(sql_query):
    """Executes SQL query and returns results."""
    try:
        result = frappe.db.sql(sql_query, as_dict=True)
        return result
    except Exception as e:
        return {"error": str(e)}

def analyze_results(results):
    """Analyzes query results and returns insights."""
    if not results:
        return "No data found."
    
    summary = f"Retrieved {len(results)} records. Sample: {json.dumps(results[:2], indent=2)}"
    return summary

def generate_visualization(results, x_field, y_field):
    """Generates visualization from results and returns base64 image string."""
    if not results or x_field not in results[0] or y_field not in results[0]:
        return "Invalid fields for visualization."
    
    x_values = [row[x_field] for row in results]
    y_values = [row[y_field] for row in results]
    
    plt.figure(figsize=(8,5))
    plt.bar(x_values, y_values)
    plt.xlabel(x_field)
    plt.ylabel(y_field)
    plt.title(f"{y_field} vs {x_field}")
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    
    return image_base64

def ai_bi_query_handler(user_input):
    """Main function to handle AI-driven BI queries in ERPNext."""
    sql_query = generate_sql_query(user_input)
    results = execute_sql_query(sql_query)
    
    if "error" in results:
        return results
    
    analysis = analyze_results(results)
    visualization = generate_visualization(results, x_field="date", y_field="amount")
    
    return {
        "query": sql_query,
        "analysis": analysis,
        "visualization": visualization
    }
