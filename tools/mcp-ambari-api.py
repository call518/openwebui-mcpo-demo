#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "fastmcp>=0.1.0",
#   "aiohttp>=3.8.0",
# ]
# ///

from typing import Dict, Optional
from mcp.server.fastmcp import FastMCP
import os
import aiohttp
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

#-----------------------------------------------------------------------------------

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

@mcp.tool()
async def get_cluster_services() -> str:
    """
    Retrieves the list of services with status in an Ambari cluster.
    
    [Tool Role]: Dedicated tool for real-time retrieval of all running services and basic status information in an Ambari cluster
    
    [Core Functions]: 
    - Retrieve cluster service list with status via Ambari REST API
    - Provide service names, current state, and cluster information
    - Include detailed link information for each service
    - Display visual indicators for service status
    
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
        Cluster service list with status information (success: service list with status, failure: error message)
    """
    cluster_name = AMBARI_CLUSTER_NAME
    try:
        endpoint = f"/clusters/{cluster_name}/services?fields=ServiceInfo/service_name,ServiceInfo/state,ServiceInfo/cluster_name"
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
            state = service_info.get("state", "Unknown")
            service_href = service.get("href", "")
            
            # Add status icon
            status_icon = "🟢" if state == "STARTED" else "🔴" if state in ["INSTALLED", "STOPPED"] else "🟡"
            
            result_lines.append(f"{i}. {status_icon} Service Name: {service_name} [{state}]")
            result_lines.append(f"   Cluster: {service_info.get('cluster_name', cluster_name)}")
            result_lines.append(f"   API Link: {service_href}")
            result_lines.append("")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"Error: Exception occurred while retrieving service list - {str(e)}"

@mcp.tool()
async def get_service_status(service_name: str) -> str:
    """
    Retrieves the status information for a specific service in an Ambari cluster.
    
    [Tool Role]: Dedicated tool for real-time retrieval of specific service status and state information
    
    [Core Functions]:
    - Retrieve specific service status via Ambari REST API
    - Provide detailed service state information (STARTED, STOPPED, INSTALLING, etc.)
    - Include service configuration and component information
    
    [Required Usage Scenarios]:
    - When users ask about specific service status (e.g., "HDFS status", "YARN state")
    - When troubleshooting service issues
    - When monitoring specific service health
    
    Args:
        service_name: Name of the service to check (e.g., "HDFS", "YARN", "HBASE")
    
    Returns:
        Service status information (success: detailed status, failure: error message)
    """
    cluster_name = AMBARI_CLUSTER_NAME
    try:
        endpoint = f"/clusters/{cluster_name}/services/{service_name}?fields=ServiceInfo/state,ServiceInfo/service_name,ServiceInfo/cluster_name"
        response_data = await make_ambari_request(endpoint)
        
        if response_data is None:
            return f"Error: Unable to retrieve status for service '{service_name}' in cluster '{cluster_name}'."
        
        service_info = response_data.get("ServiceInfo", {})
        
        result_lines = [f"Service Status for '{service_name}':"]
        result_lines.append("=" * 40)
        result_lines.append(f"Service Name: {service_info.get('service_name', service_name)}")
        result_lines.append(f"Cluster: {service_info.get('cluster_name', cluster_name)}")
        result_lines.append(f"Current State: {service_info.get('state', 'Unknown')}")
        
        # Add state description
        state = service_info.get('state', 'Unknown')
        state_descriptions = {
            'STARTED': 'Service is running and operational',
            'INSTALLED': 'Service is installed but not running',
            'STARTING': 'Service is in the process of starting',
            'STOPPING': 'Service is in the process of stopping',
            'INSTALLING': 'Service is being installed',
            'INSTALL_FAILED': 'Service installation failed',
            'MAINTENANCE': 'Service is in maintenance mode',
            'UNKNOWN': 'Service state cannot be determined'
        }
        
        if state in state_descriptions:
            result_lines.append(f"Description: {state_descriptions[state]}")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"Error: Exception occurred while retrieving service status - {str(e)}"

@mcp.tool()
async def get_service_details(cluster_name: str, service_name: str) -> str:
    """
    Retrieves detailed status and configuration information for a specific service in a specified Ambari cluster.
    
    [Tool Role]: Flexible tool for retrieving comprehensive service information with custom cluster specification
    
    [Core Functions]:
    - Retrieve specific service details via Ambari REST API with custom cluster name
    - Provide detailed service state, configuration, and component information
    - Include service metrics and health status
    
    [Required Usage Scenarios]:
    - When users specify both cluster name and service name
    - When working with multiple clusters
    - When detailed service analysis is required for specific cluster
    
    Args:
        cluster_name: Name of the cluster (e.g., "TEST-AMBARI", "PROD-CLUSTER")
        service_name: Name of the service to check (e.g., "HDFS", "YARN", "HBASE")
    
    Returns:
        Detailed service information (success: comprehensive service details, failure: error message)
    """
    try:
        # First check if cluster exists
        cluster_endpoint = f"/clusters/{cluster_name}"
        cluster_response = await make_ambari_request(cluster_endpoint)
        
        if cluster_response is None:
            return f"Error: Cluster '{cluster_name}' not found or inaccessible. Please check cluster name and Ambari server connection."
        
        # Get detailed service information
        service_endpoint = f"/clusters/{cluster_name}/services/{service_name}?fields=ServiceInfo,components/ServiceComponentInfo"
        service_response = await make_ambari_request(service_endpoint)
        
        if service_response is None:
            return f"Error: Service '{service_name}' not found in cluster '{cluster_name}'. Please check service name."
        
        service_info = service_response.get("ServiceInfo", {})
        components = service_response.get("components", [])
        
        result_lines = [f"Detailed Service Information:"]
        result_lines.append("=" * 50)
        result_lines.append(f"🏷️  Service Name: {service_info.get('service_name', service_name)}")
        result_lines.append(f"🏢 Cluster: {service_info.get('cluster_name', cluster_name)}")
        result_lines.append(f"📊 Current State: {service_info.get('state', 'Unknown')}")
        
        # Add state description
        state = service_info.get('state', 'Unknown')
        state_descriptions = {
            'STARTED': '✅ Service is running and operational',
            'INSTALLED': '⏸️  Service is installed but not running', 
            'STARTING': '🔄 Service is in the process of starting',
            'STOPPING': '⏹️  Service is in the process of stopping',
            'INSTALLING': '📦 Service is being installed',
            'INSTALL_FAILED': '❌ Service installation failed',
            'MAINTENANCE': '🔧 Service is in maintenance mode',
            'UNKNOWN': '❓ Service state cannot be determined'
        }
        
        if state in state_descriptions:
            result_lines.append(f"📝 Description: {state_descriptions[state]}")
        
        # Add component information
        if components:
            result_lines.append(f"\n🔧 Components ({len(components)} total):")
            for i, component in enumerate(components, 1):
                comp_info = component.get("ServiceComponentInfo", {})
                comp_name = comp_info.get("component_name", "Unknown")
                result_lines.append(f"   {i}. {comp_name}")
        else:
            result_lines.append(f"\n🔧 Components: No components found")
        
        # Add additional service info if available
        if "desired_configs" in service_info:
            result_lines.append(f"\n⚙️  Configuration: Available")
        
        result_lines.append(f"\n🔗 API Endpoint: {service_response.get('href', 'Not available')}")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"Error: Exception occurred while retrieving service details - {str(e)}"

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
