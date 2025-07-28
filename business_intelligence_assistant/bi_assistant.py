import frappe
import json
import pandas as pd
from frappe.utils import cstr
from frappe import _
from .bi_engine import BIQueryEngine

@frappe.whitelist()
def execute_query(query_name=None):
    """Execute a BI Query and return results"""
    if not query_name:
        frappe.throw(_("Query name is required"))
    
    # Check permissions
    if not frappe.has_permission("BI Query", "read", query_name):
        frappe.throw(_("No permission to execute query"), frappe.PermissionError)
    
    # Get the query document
    query_doc = frappe.get_doc("BI Query", query_name)
    
    # Initialize the BI engine
    engine = BIQueryEngine()
    
    # Execute the query
    result = engine.execute_query(query_doc)
    
    return result

@frappe.whitelist()
def create_and_execute_query(query_text, data_source="ERPNext", date_range="Last 30 Days", visualization_type="Auto"):
    """Create a new query and execute it in one step"""
    if not query_text:
        frappe.throw(_("Query text is required"))
    
    # Check permissions
    if not frappe.has_permission("BI Query", "create"):
        frappe.throw(_("No permission to create query"), frappe.PermissionError)
    
    # Create a new query document
    query_doc = frappe.new_doc("BI Query")
    query_doc.query_name = f"Query {frappe.utils.now_datetime().strftime('%Y%m%d%H%M%S')}"
    query_doc.query_text = query_text
    query_doc.user = frappe.session.user
    query_doc.data_source = data_source
    query_doc.date_range = date_range
    query_doc.visualization_type = visualization_type
    query_doc.status = "Draft"
    query_doc.insert()
    
    # Execute the query
    engine = BIQueryEngine()
    result = engine.execute_query(query_doc)
    
    # Add the query ID to the result
    result["query_id"] = query_doc.name
    
    return result

@frappe.whitelist()
def get_query_result(result_id=None):
    """Get a BI Query Result by ID"""
    if not result_id:
        frappe.throw(_("Result ID is required"))
    
    # Check permissions
    if not frappe.has_permission("BI Query Result", "read", result_id):
        frappe.throw(_("No permission to access result"), frappe.PermissionError)
    
    # Get the result document
    result_doc = frappe.get_doc("BI Query Result", result_id)
    
    return {
        "query_id": result_doc.query_reference,
        "status": result_doc.status,
        "execution_time": result_doc.execution_time,
        "visualization_html": result_doc.visualization_html,
        "ai_summary": result_doc.ai_summary,
        "error_message": result_doc.error_message if result_doc.status == "Error" else None
    }

@frappe.whitelist()
def download_query_data(result_id, format="csv"):
    """Download query result data in specified format"""
    if not result_id:
        frappe.throw(_("Result ID is required"))
    
    # Check permissions
    if not frappe.has_permission("BI Query Result", "read", result_id):
        frappe.throw(_("No permission to access result"), frappe.PermissionError)
    
    # Get the result document
    result_doc = frappe.get_doc("BI Query Result", result_id)
    
    if result_doc.status != "Success":
        frappe.throw(_("Cannot download data from an unsuccessful query"))
    
    # Parse the JSON data
    data = json.loads(result_doc.raw_data)
    df = pd.DataFrame(data)
    
    # Get the query name for the file name
    query_doc = frappe.get_doc("BI Query", result_doc.query_reference)
    file_name = query_doc.query_name.replace(" ", "_")
    
    if format.lower() == "csv":
        # Generate CSV
        csv_data = df.to_csv(index=False)
        frappe.response['filecontent'] = csv_data
        frappe.response['type'] = 'csv'
        frappe.response['filename'] = f"{file_name}.csv"
    
    elif format.lower() == "excel":
        # Generate Excel
        from io import BytesIO
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Data', index=False)
        
        # Add metadata sheet
        metadata = pd.DataFrame([
            {"Attribute": "Query", "Value": query_doc.query_text},
            {"Attribute": "Created By", "Value": query_doc.user},
            {"Attribute": "Data Source", "Value": query_doc.data_source},
            {"Attribute": "Date Range", "Value": query_doc.date_range},
            {"Attribute": "Execution Time", "Value": cstr(result_doc.execution_time)}
        ])
        metadata.to_excel(writer, sheet_name='Metadata', index=False)
        
        writer.save()
        frappe.response['filecontent'] = output.getvalue()
        frappe.response['type'] = 'binary'
        frappe.response['filename'] = f"{file_name}.xlsx"
    
    else:
        frappe.throw(_("Unsupported format. Use 'csv' or 'excel'"))

@frappe.whitelist()
def get_table_metadata():
    """Get all table metadata for frontend"""
    # Check permissions
    if not frappe.has_permission("DB Metadata", "read"):
        frappe.throw(_("No permission to access metadata"), frappe.PermissionError)
    
    # Get all tables
    tables = frappe.get_all(
        "DB Metadata", 
        filters={"entity_type": ["in", ["Table", "View"]]},
        fields=["name", "entity_name", "entity_type", "data_source", "description"]
    )
    
    result = {}
    
    for table in tables:
        # Get fields for each table
        fields = frappe.get_all(
            "DB Metadata Field",
            filters={"parent": table.name},
            fields=["field_name", "field_type", "description", "is_key", "is_filterable"]
        )
        
        result[table.entity_name] = {
            "type": table.entity_type,
            "source": table.data_source,
            "description": table.description,
            "fields": [{"name": field.field_name, "type": field.field_type, "description": field.description}
                      for field in fields]
        }
    
    return result

@frappe.whitelist()
def get_sample_queries():
    """Get sample queries for the BI Assistant"""
    return [
        {
            "title": "Monthly Sales Trend",
            "query": "Show me the monthly sales trend for the last 12 months"
        },
        {
            "title": "Top Customers",
            "query": "Who are our top 10 customers by revenue this year?"
        },
        {
            "title": "Product Performance",
            "query": "Which products have the highest profit margin?"
        },
        {
            "title": "Sales by Region",
            "query": "Show me sales by region for this quarter"
        },
        {
            "title": "Accounts Receivable",
            "query": "What is our current accounts receivable aging?"
        },
        {
            "title": "Inventory Value",
            "query": "What is our current inventory value by warehouse?"
        },
        {
            "title": "Employee Performance",
            "query": "Who are the top performing sales representatives this quarter?"
        },
        {
            "title": "Customer Acquisition",
            "query": "How many new customers have we acquired each month this year?"
        }
    ]

@frappe.whitelist()
def sync_table_metadata():
    """Synchronize DB Metadata with actual database structure"""
    # Only allow System Managers to sync metadata
    if not frappe.has_permission("System Manager", "write"):
        frappe.throw(_("Only System Managers can sync database metadata"), frappe.PermissionError)

    # Fetch tables from the database
    tables = frappe.db.sql("""
        SELECT table_name, table_type, table_comment
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        AND table_name LIKE 'tab%'
    """, as_dict=True)

    # Skip system tables that should not be included
    system_tables = {"tabSessions", "tabActivity Log", "tabInstalled Applications", "tabPatch Log", "tabDB Metadata"}

    # Track updates
    added_tables = []
    updated_tables = []

    for table in tables:
        # Skip system tables and DB Metadata itself
        if table.table_name in system_tables:
            continue

        # Convert table name to entity name (Remove 'tab' prefix)
        entity_name = table.table_name[3:] if table.table_name.startswith("tab") else table.table_name

        # Check if the table already exists in DB Metadata
        existing_metadata = frappe.get_all("DB Metadata",
            filters={"entity_name": entity_name, "data_source": "ERPNext"},
            fields=["name"])

        if existing_metadata:
            # Update existing metadata
            metadata_name = existing_metadata[0]["name"]
            existing_doc = frappe.get_doc("DB Metadata", metadata_name)
            existing_doc.entity_type = "View" if table.table_type == "VIEW" else "Table"
            existing_doc.description = table.table_comment or f"{entity_name} table"
            existing_doc.save(ignore_permissions=True)
            updated_tables.append(entity_name)
        else:
            # Create new metadata record
            new_doc = frappe.new_doc("DB Metadata")
            new_doc.entity_name = entity_name
            new_doc.entity_type = "View" if table.table_type == "VIEW" else "Table"
            new_doc.data_source = "ERPNext"
            new_doc.description = table.table_comment or f"{entity_name} table"
            new_doc.insert(ignore_permissions=True)  # Ensure it gets inserted
            added_tables.append(entity_name)

    # Return the summary of changes
    return {
        "added": added_tables,
        "updated": updated_tables,
        "total": len(added_tables) + len(updated_tables)
    }