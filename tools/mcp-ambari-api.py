from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
import os
import aiohttp
import json
from base64 import b64encode

# =============================================================================
# Server Initialization
# =============================================================================
# TODO: Change "your-server-name" to the actual server name
mcp = FastMCP("ambari-api")

# =============================================================================
# Constants
# =============================================================================
# TODO: Add necessary constants here
# Example:
# API_BASE_URL = "https://api.example.com"
# USER_AGENT = "your-app/1.0"
# DEFAULT_TIMEOUT = 30.0

# Ambari API connection information environment variable settings
# These values are retrieved from environment variables or use default values.
AMBARI_HOST = os.environ.get("AMBARI_HOST", "localhost")
AMBARI_PORT = os.environ.get("AMBARI_PORT", "8080")
AMBARI_USER = os.environ.get("AMBARI_USER", "admin")
AMBARI_PASS = os.environ.get("AMBARI_PASS", "admin")
AMBARI_CLUSTER_NAME = os.environ.get("AMBARI_CLUSTER_NAME", "c1")

# AMBARI API base URL configuration
AMBARI_API_BASE_URL = f"http://{AMBARI_HOST}:{AMBARI_PORT}/api/v1"

# =============================================================================
# Helper Functions
# =============================================================================

async def make_ambari_request(endpoint: str, method: str = "GET") -> Optional[Dict]:
    """
    Sends HTTP requests to Ambari API.
    
    Args:
        endpoint: API endpoint (e.g., "/clusters/c1/services")
        method: HTTP method (default: "GET")
        
    Returns:
        API response data (JSON format) or None (on error)
    """
    try:
        auth_string = f"{AMBARI_USER}:{AMBARI_PASS}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = b64encode(auth_bytes).decode('ascii')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json'
        }
        
        url = f"{AMBARI_API_BASE_URL}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Ambari API error: HTTP {response.status}")
                    return None
                    
    except Exception as e:
        print(f"Ambari API request failed: {str(e)}")
        return None

@mcp.tool()
async def get_cluster_services() -> str:
    """
    Retrieves the list of services in an Ambari cluster.
    
    [Tool Role]: Dedicated tool for real-time retrieval of all running services and basic information in an Ambari cluster
    
    [Core Functions]: 
    - Retrieve cluster service list via Ambari REST API
    - Provide service names and cluster information
    - Include detailed link information for each service
    
    [Required Usage Scenarios]:
    - When users mention "service list", "cluster services", "Ambari services"
    - When cluster status check is needed
    - When service management requires current status overview
    - When real-time cluster information is absolutely necessary
    
    [Absolutely Prohibited Scenarios]:
    - General Hadoop knowledge questions
    - Service installation or configuration changes
    - Log viewing or performance monitoring
    - Requests belonging to other cluster management tools
    
    Returns:
        Cluster service list information (success: service list, failure: error message)
    """
    cluster_name = AMBARI_CLUSTER_NAME
    try:
        endpoint = f"/clusters/{cluster_name}/services"
        response_data = await make_ambari_request(endpoint)
        
        if response_data is None:
            return f"Error: Unable to retrieve service list for cluster '{cluster_name}'."
        
        if "items" not in response_data:
            return f"No results: No services found in cluster '{cluster_name}'."
        
        services = response_data["items"]
        if not services:
            return f"No results: No services installed in cluster '{cluster_name}'."
        
        # Format results
        result_lines = [f"Service list for cluster '{cluster_name}' ({len(services)} services):"]
        result_lines.append("=" * 50)
        
        for i, service in enumerate(services, 1):
            service_info = service.get("ServiceInfo", {})
            service_name = service_info.get("service_name", "Unknown")
            service_href = service.get("href", "")
            
            result_lines.append(f"{i}. Service Name: {service_name}")
            result_lines.append(f"   Cluster: {service_info.get('cluster_name', cluster_name)}")
            result_lines.append(f"   API Link: {service_href}")
            result_lines.append("")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"Error: Exception occurred while retrieving service list - {str(e)}"

@mcp.tool()
async def get_cluster_info() -> str:
    """
    Retrieves basic information for an Ambari cluster.
    
    [Tool Role]: Dedicated tool for real-time retrieval of overall status and basic information for an Ambari cluster
    
    Returns:
        Cluster basic information (name, version, status, etc.)
    """
    cluster_name = AMBARI_CLUSTER_NAME
    try:
        endpoint = f"/clusters/{cluster_name}"
        response_data = await make_ambari_request(endpoint)
        
        if response_data is None:
            return f"Error: Unable to retrieve information for cluster '{cluster_name}'."
        
        cluster_info = response_data.get("Clusters", {})
        
        result_lines = [f"Information for cluster '{cluster_name}':"]
        result_lines.append("=" * 30)
        result_lines.append(f"Cluster Name: {cluster_info.get('cluster_name', cluster_name)}")
        result_lines.append(f"Version: {cluster_info.get('version', 'Unknown')}")
        
        if "provisioning_state" in cluster_info:
            result_lines.append(f"Provisioning State: {cluster_info['provisioning_state']}")
        
        if "security_type" in cluster_info:
            result_lines.append(f"Security Type: {cluster_info['security_type']}")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"Error: Exception occurred while retrieving cluster information - {str(e)}"

# =============================================================================
# Server Execution
# =============================================================================

if __name__ == "__main__":
    """
    Starts the server.
    
    Usage:
    1. For development, use stdio transport: mcp.run(transport='stdio')
    2. For production, use other transport methods as needed
    """
    mcp.run(transport='stdio')
