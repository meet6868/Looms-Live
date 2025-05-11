import requests
import json

def diagnose_supabase_connection(url, api_key):
    """
    Diagnose connection issues with Supabase.
    
    Args:
        url (str): Supabase URL
        api_key (str): Supabase API key
        
    Returns:
        dict: Diagnostic results
    """
    results = {
        "url_valid": False,
        "auth_valid": False,
        "tables_accessible": False,
        "error_details": None
    }
    
    try:
        # Check if URL is valid
        if not url.startswith("https://"):
            results["error_details"] = "URL must start with https://"
            return results
        
        # Try to connect to Supabase
        headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Test URL validity
        try:
            response = requests.get(f"{url}/rest/v1/", headers=headers, timeout=10)
            results["url_valid"] = response.status_code != 404
        except requests.exceptions.RequestException as e:
            results["error_details"] = f"Connection error: {str(e)}"
            return results
        
        # Test authentication
        try:
            auth_response = requests.get(f"{url}/rest/v1/", headers=headers, timeout=10)
            results["auth_valid"] = auth_response.status_code != 401
            
            if not results["auth_valid"]:
                results["error_details"] = "Authentication failed: Invalid API key"
                return results
        except requests.exceptions.RequestException as e:
            results["error_details"] = f"Authentication error: {str(e)}"
            return results
        
        # Test if companies table exists
        try:
            table_response = requests.get(f"{url}/rest/v1/companies?limit=1", headers=headers, timeout=10)
            results["tables_accessible"] = table_response.status_code == 200
            
            if not results["tables_accessible"]:
                if table_response.status_code == 404:
                    results["error_details"] = "companies table does not exist"
                else:
                    results["error_details"] = f"Table access error: HTTP {table_response.status_code}"
        except requests.exceptions.RequestException as e:
            results["error_details"] = f"Table access error: {str(e)}"
        
    except Exception as e:
        results["error_details"] = f"Unexpected error: {str(e)}"
    
    return results

def create_supabase_table(url, api_key, table_name, schema):
    """
    Create a table in Supabase.
    
    Args:
        url (str): Supabase URL
        api_key (str): Supabase API key
        table_name (str): Name of the table to create
        schema (dict): Table schema
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        # Use Supabase's SQL API to create the table
        sql_query = f"CREATE TABLE IF NOT EXISTS {table_name} ("
        
        # Add columns
        columns = []
        for column_name, column_def in schema.items():
            columns.append(f"{column_name} {column_def}")
        
        sql_query += ", ".join(columns)
        sql_query += ");"
        
        response = requests.post(
            f"{url}/rest/v1/rpc/execute_sql",
            headers=headers,
            json={"query": sql_query},
            timeout=10
        )
        
        return response.status_code in (200, 201, 204)
    except Exception:
        return False