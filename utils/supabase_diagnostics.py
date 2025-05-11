import requests
import logging

logger = logging.getLogger("LoomLive.SupabaseDiagnostics")

def diagnose_supabase_connection(url, api_key):
    """
    Diagnose Supabase connection issues
    
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
    
    if not url or not api_key:
        results["error_details"] = "URL or API key is empty"
        return results
    
    # Check if URL is properly formatted
    if not url.startswith("https://"):
        logger.warning(f"URL does not start with https://: {url}")
    
    # Remove trailing slash if present
    if url.endswith("/"):
        url = url[:-1]
    
    results["url_valid"] = True
    
    try:
        # Test basic connection
        logger.info(f"Testing connection to Supabase at: {url}")
        
        # Try to access health endpoint
        health_response = requests.get(
            f"{url}/rest/v1/",
            headers={
                "apikey": api_key,
                "Authorization": f"Bearer {api_key}"
            }
        )
        
        logger.info(f"Health check response: {health_response.status_code}")
        
        if health_response.status_code in [200, 404]:
            # 404 is acceptable for the root endpoint
            results["auth_valid"] = True
        
        # Try to list tables
        tables_response = requests.get(
            f"{url}/rest/v1/",
            headers={
                "apikey": api_key,
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json"
            },
            params={"select": "*"}
        )
        
        logger.info(f"Tables list response: {tables_response.status_code}")
        
        if tables_response.status_code == 200:
            results["tables_accessible"] = True
        
        # Check specific table (companies)
        companies_response = requests.get(
            f"{url}/rest/v1/companies",
            headers={
                "apikey": api_key,
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json"
            },
            params={"select": "*", "limit": 1}
        )
        
        logger.info(f"Companies table response: {companies_response.status_code}")
        
        if companies_response.status_code == 404:
            results["error_details"] = "The 'companies' table does not exist or is not accessible"
        elif companies_response.status_code != 200:
            results["error_details"] = f"Error accessing 'companies' table: {companies_response.status_code}"
        
        return results
    
    except requests.exceptions.ConnectionError:
        results["error_details"] = "Connection error - could not connect to the server"
        return results
    except requests.exceptions.Timeout:
        results["error_details"] = "Connection timed out"
        return results
    except requests.exceptions.RequestException as e:
        results["error_details"] = f"Request error: {str(e)}"
        return results
    except Exception as e:
        results["error_details"] = f"Unexpected error: {str(e)}"
        return results