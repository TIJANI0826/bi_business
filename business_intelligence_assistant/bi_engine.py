import frappe
import json
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
import re
import openai

openai.proxy = {
            "http": "http://127.0.0.1:7890",
            "https": "http://127.0.0.1:7890"
        }
host = frappe.conf.db_host
user = frappe.conf.db_name
password = frappe.conf.db_password
db_name = frappe.conf.db_name
print(host,user,password,db_name)

# Connect to ERPNext MariaDB database
db_uri = f"mysql+pymysql://{user}:{password}@{host}/{db_name}"
db = SQLDatabase.from_uri(db_uri)


class BIQueryEngine:
    """Engine for processing natural language queries with AI and database integration"""
    
    def __init__(self):
        """Initialize the BI Query Engine"""
        self.llm = ChatDeepSeek(
            model_name="deepseek-chat",
            temperature=0,
            api_key=frappe.conf.get("deepseek_api_key")
        )
        self.metadata = self._load_metadata()
        
    def _load_metadata(self):
        """Load database metadata from DB Metadata DocType"""
        metadata = {
            "tables": {},
            "relationships": []
        }
        
        # Get all tables and views
        tables = frappe.get_all(
            "DB Metadata", 
            filters={"entity_type": ["in", ["Table", "View"]]},
            fields=["name", "entity_name", "entity_type", "data_source", "description"]
        )
        
        for table in tables:
            # Get fields for each table
            fields = frappe.get_all(
                "DB Metadata Field",
                filters={"parent": table.name},
                fields=["field_name", "field_type", "description", "is_key", "is_filterable", "related_entity"]
            )
            
            metadata["tables"][table.entity_name] = {
                "type": table.entity_type,
                "source": table.data_source,
                "description": table.description,
                "fields": {field.field_name: {
                    "type": field.field_type,
                    "description": field.description,
                    "is_key": field.is_key,
                    "is_filterable": field.is_filterable,
                    "related_entity": field.related_entity
                } for field in fields}
            }
        
        # Get relationships
        relationships = frappe.get_all(
            "DB Metadata",
            filters={"entity_type": "Relationship"},
            fields=["entity_name", "from_entity", "to_entity", "relationship_type", "join_field"]
        )
        
        for rel in relationships:
            metadata["relationships"].append({
                "name": rel.entity_name,
                "from_entity": rel.from_entity,
                "to_entity": rel.to_entity,
                "type": rel.relationship_type,
                "join_field": rel.join_field
            })
            
        return metadata
    
    def _resolve_date_range(self, date_range, custom_from_date=None, custom_to_date=None):
        """Convert a date range selection to actual date values"""
        today = datetime.now().date()
        
        if date_range == "Custom" and custom_from_date and custom_to_date:
            return custom_from_date, custom_to_date
            
        if date_range == "Last 30 Days":
            return (today - timedelta(days=30)), today
            
        if date_range == "This Month":
            return today.replace(day=1), today
            
        if date_range == "Last Quarter":
            quarter_start_month = ((today.month - 1) // 3) * 3 - 2
            if quarter_start_month <= 0:
                quarter_start_month += 12
                start_year = today.year - 1
            else:
                start_year = today.year
            start_date = datetime(start_year, quarter_start_month, 1).date()
            end_date = datetime(today.year, ((today.month - 1) // 3) * 3 + 1, 1).date() - timedelta(days=1)
            return start_date, end_date
            
        if date_range == "This Quarter":
            quarter_start_month = ((today.month - 1) // 3) * 3 + 1
            start_date = datetime(today.year, quarter_start_month, 1).date()
            end_date = today
            return start_date, end_date
            
        if date_range == "Last Year":
            return datetime(today.year - 1, 1, 1).date(), datetime(today.year - 1, 12, 31).date()
            
        if date_range == "This Year":
            return datetime(today.year, 1, 1).date(), today
            
        if date_range == "All Time":
            return None, None
            
        # Default to last 30 days
        return (today - timedelta(days=30)), today
    
    def _get_connection_string(self, data_source):
        """Get connection string for the specified data source"""
        if data_source == "ERPNext":
            return "frappe_db"
        elif data_source == "Splynx":
            return frappe.conf.get("splynx_db_conn")
        else:
            raise ValueError(f"Unsupported data source: {data_source}")
    def save_sql_to_file(self,sql_query, filename="query.sql"):
        """Saves the given SQL query to a text file."""
        try:
            with open(filename, "w", encoding="utf-8") as file:
                file.write(sql_query)
            print(f"SQL query saved to {filename}")
        except Exception as e:
            print(f"Error saving SQL to file: {e}")
    def extract_sql(self,text):
        """Extracts only the SQL query from the given text."""
        sql_pattern = re.compile(r"```sql(.*?)```", re.DOTALL)
        match = sql_pattern.search(text)
        return match.group(1).strip() if match else "No SQL query found."

    def generate_sql(self, query_doc):
        """Generate SQL from natural language query"""
        # Extract information from the query doc
        query_text = query_doc.query_text
        data_source = query_doc.data_source
        from_date, to_date = self._resolve_date_range(
            query_doc.date_range,
            query_doc.custom_from_date,
            query_doc.custom_to_date
        )
        
        # Filter metadata for the selected data source
        if data_source != "Cross System":
            filtered_tables = {
                name: details for name, details in self.metadata["tables"].items()
                if details["source"] == data_source
            }
        else:
            filtered_tables = self.metadata["tables"]
        
        # Create context information about the database schema
        schema_info = ""
        for table_name, table_info in filtered_tables.items():
            schema_info += f"Table: {table_name} ({table_info['description']})\n"
            for field_name, field_info in table_info["fields"].items():
                schema_info += f"  - {field_name} ({field_info['type']}): {field_info['description']}\n"
        
        # Add relationship information
        schema_info += "\nRelationships:\n"
        for rel in self.metadata["relationships"]:
            if rel["from_entity"] in filtered_tables and rel["to_entity"] in filtered_tables:
                schema_info += f"  - {rel['name']}: {rel['from_entity']} {rel['type']} {rel['to_entity']} using {rel['join_field']}\n"
        
        # Create prompt template for SQL generation
        sql_prompt = PromptTemplate.from_template(
            """You are an expert SQL query generator that converts natural language questions about business data into SQL queries.
            
            Database Schema:
            {schema}
            
            Additional Context:
            {date_context}
            
            User Question: {question}
            
            Create a SQL query that answers the user's question, using correct SQL syntax. Keep the query secure, avoiding any potential SQL injection vulnerabilities. Always include aliases for tables to make the query more readable.
            
            SQL Query:"""
        )
        
        # Add date context if applicable
        date_context = ""
        if from_date and to_date:
            date_context = f"The query should be limited to data between {from_date} and {to_date} where applicable."
        
        # Create chain for SQL generation

        #query_chain = create_sql_query_chain(self.llm, db, prompt=sql_prompt)
        sql_chain = LLMChain(llm=self.llm, prompt=sql_prompt)
        
        # Generate SQL
        sql_output = sql_chain.invoke({
            "schema": schema_info,
            "date_context": date_context,
            "question": query_text
        })
        
        # Extract SQL from the output
        sql_query = sql_output.get("text", "").strip()
        #sql_query =self.extract_sql(sql_query)

        self.save_sql_to_file(sql_query)
        # Validate and sanitize SQL
        try:
            parsed = sqlglot.parse(sql_query)
            # Check for dangerous operations
            if any(op in sql_query.lower() for op in ["insert", "update", "delete", "drop", "alter", "grant"]):
                raise ValueError("SQL query contains potentially harmful operations")
        except Exception as e:
            frappe.log_error(f"SQL validation error: {str(e)}")
            return None
        
        return sql_query
    
    def execute_query(self, query_doc):
        """Execute the SQL query and return results"""
        # Generate SQL if not already generated
        if not query_doc.generated_sql:
            sql_query = self.generate_sql(query_doc)
            if not sql_query:
                return {"status": "Error", "message": "Failed to generate SQL query"}
            
            # Update the query doc with generated SQL
            frappe.db.set_value("BI Query", query_doc.name, "generated_sql", sql_query)
        else:
            sql_query = query_doc.generated_sql
        
        # Execute the query based on data source
        try:
            if query_doc.data_source == "ERPNext":
                # Use frappe's db module for ERPNext
                result = frappe.db.sql(sql_query, as_dict=True)
                df = pd.DataFrame(result)
            else:
                # For external databases, use connections from configuration
                # This is a placeholder - you'd need to implement proper database connections
                # based on your specific requirements
                conn_string = self._get_connection_string(query_doc.data_source)
                # Using pandas to read from SQL
                import pymysql
                conn = pymysql.connect(
                    host=frappe.conf.get(f"{conn_string}_host"),
                    user=frappe.conf.get(f"{conn_string}_user"),
                    password=frappe.conf.get(f"{conn_string}_password"),
                    database=frappe.conf.get(f"{conn_string}_db")
                )
                df = pd.read_sql(sql_query, conn)
                conn.close()
            
            # Create result document
            result_doc = frappe.new_doc("BI Query Result")
            result_doc.query_reference = query_doc.name
            result_doc.execution_time = datetime.now()
            result_doc.status = "Success"
            result_doc.raw_data = json.dumps(df.to_dict(orient="records"))
            
            # Generate visualization
            if not df.empty:
                visualization_html = self._generate_visualization(df, query_doc)
                result_doc.visualization_html = visualization_html
                
                # Generate AI summary
                summary = self._generate_summary(df, query_doc.query_text)
                result_doc.ai_summary = summary
            
            result_doc.insert()
            
            # Update the query document
            frappe.db.set_value("BI Query", query_doc.name, {
                "result_reference": result_doc.name,
                "status": "Executed",
                "last_run": datetime.now()
            })
            
            return {
                "status": "Success",
                "result_id": result_doc.name,
                "visualization": visualization_html if not df.empty else ""
            }
            
        except Exception as e:
            frappe.log_error(f"Query execution error: {str(e)}")
            
            # Create error result
            result_doc = frappe.new_doc("BI Query Result")
            result_doc.query_reference = query_doc.name
            result_doc.execution_time = datetime.now()
            result_doc.status = "Error"
            result_doc.error_message = str(e)
            result_doc.insert()
            
            # Update the query document
            frappe.db.set_value("BI Query", query_doc.name, {
                "result_reference": result_doc.name,
                "status": "Failed",
                "last_run": datetime.now()
            })
            
            return {"status": "Error", "message": str(e)}
    
    def _generate_visualization(self, df, query_doc):
        """Generate appropriate visualization for the data"""
        # Determine visualization type
        viz_type = query_doc.visualization_type
        if viz_type == "Auto":
            # Auto-detect based on data shape
            if df.shape[0] > 10 and df.select_dtypes(include=['datetime64', 'datetime64[ns]']).columns.any():
                # Time series data
                viz_type = "Line Chart"
            elif df.shape[0] <= 10:
                # Categorical data with few categories
                viz_type = "Bar Chart"
            elif df.shape[1] <= 3 and df.shape[0] > 0:
                # Simple data with few columns
                viz_type = "Pie Chart"
            else:
                # Default to table for complex data
                viz_type = "Table"
    
        if viz_type == "Bar Chart":
            # For bar chart, use the first string column as x and first numeric as y
            str_cols = df.select_dtypes(include=['object']).columns
            num_cols = df.select_dtypes(include=['number']).columns

            if len(str_cols) > 0 and len(num_cols) > 0:
                x_col = str_cols[0]
                y_col = num_cols[0]
                sns.barplot(x=x_col, y=y_col, data=df)
                plt.title(f"{y_col} by {x_col}")
                plt.xticks(rotation=45)
                plt.tight_layout()
            else:
                return f"<div class='alert alert-warning'>Cannot create bar chart: need both string and numeric columns</div>{self._df_to_html_table(df)}"   
                
        elif viz_type == "Line Chart":
            # For line chart, use the first date/datetime column as x and first numeric as y
            date_cols = df.select_dtypes(include=['datetime64', 'datetime64[ns]']).columns
            if len(date_cols) == 0:
                # Try to convert string columns to datetime
                for col in df.select_dtypes(include=['object']).columns:
                    try:
                        df[col] = pd.to_datetime(df[col])
                        date_cols = [col]
                        break
                    except:
                        pass
            
            num_cols = df.select_dtypes(include=['number']).columns
            
            if len(date_cols) > 0 and len(num_cols) > 0:
                x_col = date_cols[0]
                y_col = num_cols[0]
                plt.plot(df[x_col], df[y_col], marker='o')
                plt.title(f"{y_col} Trend Over Time")
                plt.xticks(rotation=45)
                plt.tight_layout()
            else:
                return f"<div class='alert alert-warning'>Cannot create line chart: need both date and numeric columns</div>{self._df_to_html_table(df)}"
                
        elif viz_type == "Pie Chart":
            # For pie chart, use the first string column for labels and first numeric for values
            str_cols = df.select_dtypes(include=['object']).columns
            num_cols = df.select_dtypes(include=['number']).columns

            if len(str_cols) > 0 and len(num_cols) > 0:
                labels = df[str_cols[0]].tolist()
                values = df[num_cols[0]].tolist()
                plt.pie(values, labels=labels, autopct='%1.1f%%')
                plt.title(f"Distribution of {num_cols[0]} by {str_cols[0]}")
                plt.axis('equal')
            else:
                return f"<div class='alert alert-warning'>Cannot create pie chart: need both string and numeric columns</div>{self._df_to_html_table(df)}"
        
        else:  # Table view
            return self._df_to_html_table(df)
        
        # Convert plot to base64 for HTML embedding
        buffer = BytesIO()
        # Create visualization based on type
        plt.figure(figsize=(10, 6))
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        encoded = base64.b64encode(image_png).decode('utf-8')
        html = f'<div class="chart-container"><img src="data:image/png;base64,{encoded}" class="img-fluid"/></div>'
        
        # Add download options
        html += f"""
        <div class="mt-3">
            <button class="btn btn-sm btn-primary download-csv" data-query="{query_doc.name}">
                <i class="fa fa-download"></i> Download CSV
            </button>
            <button class="btn btn-sm btn-info download-excel" data-query="{query_doc.name}">
                <i class="fa fa-file-excel"></i> Download Excel
            </button>
        </div>
        """
        
        # Add table view below the chart
        html += f'<div class="mt-4">{self._df_to_html_table(df)}</div>'
        
        return html
    
    def _df_to_html_table(self, df, max_rows=100):
        """Convert DataFrame to HTML table with styling"""
        # Limit rows for display
        if df.shape[0] > max_rows:
            display_df = df.head(max_rows)
            footer_message = f"<div class='text-muted'>Showing {max_rows} of {df.shape[0]} rows</div>"
        else:
            display_df = df
            footer_message = ""
        
        # Generate styled HTML table
        table_html = display_df.to_html(classes="table table-striped table-bordered", index=False)
        
        return f"""
        <div class="table-responsive">
            {table_html}
            {footer_message}
        </div>
        """
    
    def _generate_summary(self, df, query_text):
        """Generate an AI summary of the data insights"""
        # Skip summary for empty dataframes
        if df.empty:
            return "No data available for analysis."
        
        # Prepare data description
        data_description = f"DataFrame with {df.shape[0]} rows and {df.shape[1]} columns.\n"
        data_description += "Columns: " + ", ".join(df.columns.tolist()) + "\n"
        
        # Add basic statistics for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            data_description += "Numeric column statistics:\n"
            stats = df[numeric_cols].describe().to_string()
            data_description += stats + "\n"
        
        # For categorical columns, show value counts
        cat_cols = df.select_dtypes(include=['object']).columns
        if len(cat_cols) > 0 and len(cat_cols) <= 3:  # Limit to avoid too much data
            data_description += "Categorical column distributions:\n"
            for col in cat_cols:
                if df[col].nunique() <= 10:  # Only show if not too many unique values
                    data_description += f"{col} value counts:\n"
                    data_description += df[col].value_counts().to_string() + "\n"
        
        # Create prompt for insights generation
        insight_prompt = PromptTemplate.from_template(
            """You are a data analyst expert who provides concise, insightful summaries of business data.
            
            The user asked the following question:
            {question}
            
            Here is the data that answers their question:
            {data_description}
            
            Please provide a concise 2-3 paragraph summary of the key insights from this data. Focus on business implications, trends, and actionable insights. Use bullet points where appropriate for clarity. Do not repeat the technical details of the data structure.
            """
        )
        
        # Create LLM chain for insights
        insight_chain = LLMChain(llm=self.llm, prompt=insight_prompt)
        
        # Generate insights
        try:
            insight_output = insight_chain.invoke({
                "question": query_text,
                "data_description": data_description
            })
            
            return insight_output.get("text", "")
        except Exception as e:
            frappe.log_error(f"Error generating insights: {str(e)}")
            return "Unable to generate insights for this data."