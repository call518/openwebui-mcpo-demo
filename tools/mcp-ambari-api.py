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

async def make_ambari_request(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
    """
    Sends HTTP requests to Ambari API.
    
    Args:
        endpoint: API endpoint (e.g., "/clusters/c1/services")
        method: HTTP method (default: "GET")
        data: Request payload for PUT/POST requests
        
    Returns:
        API response data (JSON format) or {"error": "error_message"} on error
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
            kwargs = {'headers': headers}
            if data:
                kwargs['data'] = json.dumps(data)
                
            async with session.request(method, url, **kwargs) as response:
                if response.status in [200, 202]:  # Accept both OK and Accepted
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {"error": f"HTTP {response.status}: {error_text}"}
                    
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

#-----------------------------------------------------------------------------------


@mcp.tool()
async def get_service_configurations(service_name: str) -> str:
    """
    [TOOL ROLE]:
    - Ambari 서비스의 설정(desired_configs, configs 등) 정보를 실시간으로 조회하는 전용 도구

    [CORE FUNCTIONS]:
    - 서비스 단위의 desired_configs(적용된 설정 태그) 및 configs(설정 타입/버전 등) 정보 조회
    - 서비스별 configuration 상태, 변경 이력, 적용 태그 등 확인
    - Ambari REST API를 통해 서비스 설정 내역을 상세하게 반환

    [REQUIRED USAGE SCENARIOS]:
    - 사용자가 "서비스 설정 보여줘", "HDFS 설정 내역", "YARN configuration 상태" 등 요청 시
    - 서비스별 적용된 설정 태그(desired_configs) 및 config 타입/버전 확인이 필요할 때
    - Ambari에서 서비스의 configuration 내역을 직접적으로 보고 싶을 때

    Args:
        service_name: Name of the service (e.g., "HDFS", "YARN", "HBASE")

    Returns:
        Service configuration information (success: info, failure: error message)
    """
    cluster_name = AMBARI_CLUSTER_NAME
    try:
        # 서비스별 주요 config type 목록 정의 (확장 가능)
        service_config_types = {
            "HDFS": ["hdfs-site", "core-site"],
            "YARN": ["yarn-site", "core-site"],
            "HBASE": ["hbase-site", "core-site"],
            # 필요시 추가
        }
        config_types = service_config_types.get(service_name.upper(), [])
        if not config_types:
            return f"Error: No config types defined for service '{service_name}'."

        result_lines = [f"Service Configuration for '{service_name}':", "="*50]
        result_lines.append(f"Cluster: {cluster_name}")

        for config_type in config_types:
            # 1. 최신 tag 추출
            type_endpoint = f"/clusters/{cluster_name}/configurations?type={config_type}"
            type_data = await make_ambari_request(type_endpoint)
            items = type_data.get("items", []) if type_data else []
            if not items:
                result_lines.append(f"[{config_type}] No configuration found.")
                continue
            # 최신 tag: 가장 마지막 items의 tag 사용
            latest_item = items[-1]
            tag = latest_item.get("tag", "Unknown")
            version = latest_item.get("version", "Unknown")
            result_lines.append(f"[{config_type}] Latest tag: {tag} (version: {version})")

            # 2. 해당 tag로 실제 설정값 조회
            config_endpoint = f"/clusters/{cluster_name}/configurations?type={config_type}&tag={tag}"
            config_data = await make_ambari_request(config_endpoint)
            config_items = config_data.get("items", []) if config_data else []
            if not config_items:
                result_lines.append(f"  No properties found for tag {tag}.")
                continue
            for item in config_items:
                properties = item.get("properties", {})
                if properties:
                    result_lines.append(f"  Properties:")
                    for k, v in properties.items():
                        result_lines.append(f"    {k}: {v}")
                else:
                    result_lines.append(f"  No properties found.")
                # properties_attributes (final 등)
                prop_attrs = item.get("properties_attributes", {})
                if prop_attrs:
                    result_lines.append(f"  Properties Attributes:")
                    for attr_type, attr_map in prop_attrs.items():
                        result_lines.append(f"    [{attr_type}]")
                        for k, v in attr_map.items():
                            result_lines.append(f"      {k}: {v}")

        return "\n".join(result_lines)
    except Exception as e:
        return f"Error: Exception occurred while retrieving service configurations - {str(e)}"

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
        
        if "error" in response_data:
            return f"Error: Unable to retrieve information for cluster '{cluster_name}'. {response_data['error']}"
        
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
async def get_active_requests() -> str:
    """
    Retrieves currently active (in progress) requests/operations in an Ambari cluster.
    Shows running operations, in-progress tasks, pending requests.
    
    [Tool Role]: Dedicated tool for monitoring currently running Ambari operations
    
    [Core Functions]:
    - Retrieve active/running Ambari operations (IN_PROGRESS, PENDING status)
    - Show real-time progress of ongoing operations
    - Monitor current cluster activity
    
    [Required Usage Scenarios]:
    - When users ask for "active requests", "running operations", "current requests"
    - When users ask for "request list", "operation list", "task list"
    - When users want to see "current tasks", "running tasks", "in progress operations"
    - When users mention "running", "in progress", "current activity"
    - When users ask about Ambari requests, operations, or tasks
    - When checking if any operations are currently running
    
    Returns:
        Active requests information (success: active request list, failure: error message)
    """
    cluster_name = AMBARI_CLUSTER_NAME
    try:
        # Get requests that are in progress only (remove PENDING as it may not be supported)
        endpoint = f"/clusters/{cluster_name}/requests?fields=Requests/id,Requests/request_status,Requests/request_context,Requests/start_time,Requests/progress_percent&Requests/request_status=IN_PROGRESS"
        response_data = await make_ambari_request(endpoint)
        
        if "error" in response_data:
            # If IN_PROGRESS also fails, try without status filter and filter manually
            endpoint_fallback = f"/clusters/{cluster_name}/requests?fields=Requests/id,Requests/request_status,Requests/request_context,Requests/start_time,Requests/progress_percent&sortBy=Requests/id.desc"
            response_data = await make_ambari_request(endpoint_fallback)
            
            if "error" in response_data:
                return f"Error: Unable to retrieve active requests for cluster '{cluster_name}'. {response_data['error']}"
        
        if "items" not in response_data:
            return f"No active requests found in cluster '{cluster_name}'."
        
        # Filter for active requests manually if needed
        all_requests = response_data["items"]
        active_requests = []
        
        for request in all_requests:
            request_info = request.get("Requests", {})
            status = request_info.get("request_status", "")
            if status in ["IN_PROGRESS", "PENDING", "QUEUED", "STARTED"]:
                active_requests.append(request)
        
        if not active_requests:
            return f"No active requests - All operations completed in cluster '{cluster_name}'."
        
        result_lines = [f"Active Requests for Cluster '{cluster_name}' ({len(active_requests)} running):"]
        result_lines.append("=" * 60)
        
        for i, request in enumerate(active_requests, 1):
            request_info = request.get("Requests", {})
            request_id = request_info.get("id", "Unknown")
            status = request_info.get("request_status", "Unknown")
            context = request_info.get("request_context", "No context")
            progress = request_info.get("progress_percent", 0)
            start_time = request_info.get("start_time", "Unknown")
            
            result_lines.append(f"{i}. Request ID: {request_id}")
            result_lines.append(f"   Status: {status}")
            result_lines.append(f"   Progress: {progress}%")
            result_lines.append(f"   Context: {context}")
            result_lines.append(f"   Started: {start_time}")
            result_lines.append("")
        
        result_lines.append("Tip: Use get_request_status(request_id) for detailed progress information.")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"Error: Exception occurred while retrieving active requests - {str(e)}"

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
            
            result_lines.append(f"{i}. Service Name: {service_name} [{state}]")
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
async def get_service_components(service_name: str) -> str:
    """
    Retrieves detailed components information for a specific service in the Ambari cluster.
    
    Args:
        service_name: Name of the service (e.g., "HDFS", "YARN", "HBASE")
    
    Returns:
        Service components detailed information (success: component list with details, failure: error message)
    """
    cluster_name = AMBARI_CLUSTER_NAME
    try:
        # Get detailed component information including host components
        endpoint = f"/clusters/{cluster_name}/services/{service_name}/components?fields=ServiceComponentInfo/component_name,ServiceComponentInfo/state,ServiceComponentInfo/category,ServiceComponentInfo/started_count,ServiceComponentInfo/installed_count,ServiceComponentInfo/total_count,host_components/HostRoles/host_name,host_components/HostRoles/state"
        response_data = await make_ambari_request(endpoint)
        
        if response_data is None:
            return f"Error: Unable to retrieve components for service '{service_name}' in cluster '{cluster_name}'."
        
        if "items" not in response_data:
            return f"No components found for service '{service_name}' in cluster '{cluster_name}'."
        
        components = response_data["items"]
        if not components:
            return f"No components found for service '{service_name}' in cluster '{cluster_name}'."
        
        result_lines = [f"Detailed Components for service '{service_name}':"]
        result_lines.append("=" * 60)
        result_lines.append(f"Total Components: {len(components)}")
        result_lines.append("")
        
        for i, component in enumerate(components, 1):
            comp_info = component.get("ServiceComponentInfo", {})
            comp_name = comp_info.get("component_name", "Unknown")
            comp_state = comp_info.get("state", "Unknown")
            comp_category = comp_info.get("category", "Unknown")
            
            # Component counts
            started_count = comp_info.get("started_count", 0)
            installed_count = comp_info.get("installed_count", 0)
            total_count = comp_info.get("total_count", 0)
            
            # Host components information
            host_components = component.get("host_components", [])
            
            result_lines.append(f"{i}. Component: {comp_name}")
            result_lines.append(f"   State: {comp_state}")
            result_lines.append(f"   Category: {comp_category}")
            
            # Add component state description
            state_descriptions = {
                'STARTED': 'Component is running',
                'INSTALLED': 'Component is installed but not running',
                'STARTING': 'Component is starting',
                'STOPPING': 'Component is stopping',
                'INSTALL_FAILED': 'Component installation failed',
                'MAINTENANCE': 'Component is in maintenance mode',
                'UNKNOWN': 'Component state is unknown'
            }
            
            if comp_state in state_descriptions:
                result_lines.append(f"   Description: {state_descriptions[comp_state]}")
            
            # Add instance counts if available
            if total_count > 0:
                result_lines.append(f"   Instances: {started_count} started / {installed_count} installed / {total_count} total")
            
            # Add host information
            if host_components:
                result_lines.append(f"   Hosts ({len(host_components)} instances):")
                for j, host_comp in enumerate(host_components[:5], 1):  # Show first 5 hosts
                    host_roles = host_comp.get("HostRoles", {})
                    host_name = host_roles.get("host_name", "Unknown")
                    host_state = host_roles.get("state", "Unknown")
                    result_lines.append(f"      {j}. {host_name} [{host_state}]")
                
                if len(host_components) > 5:
                    result_lines.append(f"      ... and {len(host_components) - 5} more hosts")
            else:
                result_lines.append("   Hosts: No host assignments found")
            
            result_lines.append("")
        
        # Add summary statistics
        total_instances = sum(len(comp.get("host_components", [])) for comp in components)
        started_components = len([comp for comp in components if comp.get("ServiceComponentInfo", {}).get("state") == "STARTED"])
        
        result_lines.append("Summary:")
        result_lines.append(f"  - Components: {len(components)} total, {started_components} started")
        result_lines.append(f"  - Total component instances across all hosts: {total_instances}")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"Error: Exception occurred while retrieving components for service '{service_name}' - {str(e)}"

@mcp.tool()
async def get_service_details(service_name: str) -> str:
    """
    Retrieves detailed status and configuration information for a specific service in the Ambari cluster.
    
    Args:
        service_name: Name of the service to check (e.g., "HDFS", "YARN", "HBASE")
    
    Returns:
        Detailed service information (success: comprehensive service details, failure: error message)
    """
    cluster_name = AMBARI_CLUSTER_NAME
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
        
        # Add component information
        if components:
            result_lines.append(f"\nComponents ({len(components)} total):")
            for i, component in enumerate(components, 1):
                comp_info = component.get("ServiceComponentInfo", {})
                comp_name = comp_info.get("component_name", "Unknown")
                result_lines.append(f"   {i}. {comp_name}")
        else:
            result_lines.append(f"\nComponents: No components found")
        
        # Add additional service info if available
        if "desired_configs" in service_info:
            result_lines.append(f"\nConfiguration: Available")
        
        result_lines.append(f"\nAPI Endpoint: {service_response.get('href', 'Not available')}")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"Error: Exception occurred while retrieving service details - {str(e)}"

@mcp.tool()
async def start_all_services() -> str:
    """
    Starts all services in an Ambari cluster (equivalent to "Start All" in Ambari Web UI).
    
    [Tool Usage]: Use this function when users request to:
    - "start all services", "start everything", "cluster startup"
    - "bring up all services", "start entire cluster"
    
    [Function Purpose]: Bulk service management - starts all installed services simultaneously
    rather than starting each service individually. This is much more efficient than
    calling start_service() for each service separately.
    
    Returns:
        Start operation result (success: request info, failure: error message)
    """
    cluster_name = AMBARI_CLUSTER_NAME
    try:
        # First check cluster exists
        cluster_endpoint = f"/clusters/{cluster_name}"
        cluster_response = await make_ambari_request(cluster_endpoint)
        
        if cluster_response.get("error"):
            return f"Error: Cluster '{cluster_name}' not found or inaccessible. {cluster_response['error']}"
        
        # Try the standard bulk start approach first
        endpoint = f"/clusters/{cluster_name}/services"
        payload = {
            "RequestInfo": {
                "context": "Start All Services via MCP API",
                "operation_level": {
                    "level": "CLUSTER",
                    "cluster_name": cluster_name
                }
            },
            "Body": {
                "ServiceInfo": {
                    "state": "STARTED"
                }
            }
        }
        
        response_data = await make_ambari_request(endpoint, method="PUT", data=payload)
        
        if response_data.get("error"):
            # If bulk approach fails, try alternative approach
            alt_endpoint = f"/clusters/{cluster_name}/services?ServiceInfo/state=INSTALLED"
            alt_payload = {
                "ServiceInfo": {
                    "state": "STARTED"
                }
            }
            
            response_data = await make_ambari_request(alt_endpoint, method="PUT", data=alt_payload)
            
            if response_data.get("error"):
                return f"Error: Failed to start services in cluster '{cluster_name}'. {response_data['error']}"
        
        # Extract request information
        request_info = response_data.get("Requests", {})
        request_id = request_info.get("id", "Unknown")
        request_status = request_info.get("status", "Unknown")
        request_href = response_data.get("href", "")
        
        result_lines = [f"Start All Services Operation Initiated:"]
        result_lines.append("=" * 50)
        result_lines.append(f"Cluster: {cluster_name}")
        result_lines.append(f"Request ID: {request_id}")
        result_lines.append(f"Status: {request_status}")
        result_lines.append(f"Monitor URL: {request_href}")
        result_lines.append("")
        result_lines.append("Note: This operation may take several minutes to complete.")
        result_lines.append("    Use get_request_status(request_id) to track progress.")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"Error: Exception occurred while starting all services - {str(e)}"

@mcp.tool()
async def stop_all_services() -> str:
    """
    Stops all services in an Ambari cluster (equivalent to "Stop All" in Ambari Web UI).
    
    [Tool Usage]: Use this function when users request to:
    - "stop all services", "stop everything", "cluster shutdown"
    - "halt all services", "shutdown entire cluster"
    
    [Function Purpose]: Bulk service management - stops all running services simultaneously
    rather than stopping each service individually. This is much more efficient than 
    calling stop_service() for each service separately.
    
    Returns:
        Stop operation result (success: request info, failure: error message)
    """
    cluster_name = AMBARI_CLUSTER_NAME
    try:
        # First, check if cluster is accessible
        cluster_endpoint = f"/clusters/{cluster_name}"
        cluster_response = await make_ambari_request(cluster_endpoint)
        
        if cluster_response.get("error"):
            return f"Error: Cluster '{cluster_name}' not found or inaccessible. {cluster_response['error']}"
        
        # Get all services that are currently STARTED
        services_endpoint = f"/clusters/{cluster_name}/services?ServiceInfo/state=STARTED"
        services_response = await make_ambari_request(services_endpoint)
        
        if services_response.get("error"):
            return f"Error retrieving services: {services_response['error']}"
        
        services = services_response.get("items", [])
        if not services:
            return "No services are currently running. All services are already stopped."
        
        # Try the standard bulk stop approach first
        stop_endpoint = f"/clusters/{cluster_name}/services"
        stop_payload = {
            "RequestInfo": {
                "context": "Stop All Services via MCP API",
                "operation_level": {
                    "level": "CLUSTER",
                    "cluster_name": cluster_name
                }
            },
            "Body": {
                "ServiceInfo": {
                    "state": "INSTALLED"
                }
            }
        }
        
        stop_response = await make_ambari_request(stop_endpoint, method="PUT", data=stop_payload)
        
        if stop_response.get("error"):
            # If bulk approach fails, try alternative approach
            alt_endpoint = f"/clusters/{cluster_name}/services?ServiceInfo/state=STARTED"
            alt_payload = {
                "ServiceInfo": {
                    "state": "INSTALLED"
                }
            }
            
            stop_response = await make_ambari_request(alt_endpoint, method="PUT", data=alt_payload)
            
            if stop_response.get("error"):
                return f"Error: Failed to stop services in cluster '{cluster_name}'. {stop_response['error']}"
        
        # Parse successful response
        request_info = stop_response.get("Requests", {})
        request_id = request_info.get("id", "Unknown")
        request_status = request_info.get("status", "Unknown")
        request_href = stop_response.get("href", "")
        
        result_lines = [
            "STOP ALL SERVICES INITIATED",
            "",
            f"Cluster: {cluster_name}",
            f"Request ID: {request_id}",
            f"Status: {request_status}",
            f"Monitor URL: {request_href}",
            "",
            "Note: This operation may take several minutes to complete.",
            "    Use get_request_status(request_id) to track progress."
        ]
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"Error: Exception occurred while stopping all services - {str(e)}"

@mcp.tool()
async def start_service(service_name: str) -> str:
    """
    Starts a specific service in the Ambari cluster.
    
    Args:
        service_name: Name of the service to start (e.g., "HDFS", "YARN", "HBASE")
    
    Returns:
        Start operation result (success: request info, failure: error message)
    """
    cluster_name = AMBARI_CLUSTER_NAME
    try:
        # Check if service exists
        service_endpoint = f"/clusters/{cluster_name}/services/{service_name}"
        service_check = await make_ambari_request(service_endpoint)
        
        if service_check.get("error"):
            return f"Error: Service '{service_name}' not found in cluster '{cluster_name}'."
        
        # Start the service
        payload = {
            "RequestInfo": {
                "context": f"Start Service {service_name} via MCP API"
            },
            "Body": {
                "ServiceInfo": {
                    "state": "STARTED"
                }
            }
        }
        
        response_data = await make_ambari_request(service_endpoint, method="PUT", data=payload)
        
        if response_data.get("error"):
            return f"Error: Failed to start service '{service_name}' in cluster '{cluster_name}'."
        
        # Extract request information
        request_info = response_data.get("Requests", {})
        request_id = request_info.get("id", "Unknown")
        request_status = request_info.get("status", "Unknown")
        request_href = response_data.get("href", "")
        
        result_lines = [
            f"START SERVICE: {service_name}",
            "",
            f"Cluster: {cluster_name}",
            f"Service: {service_name}",
            f"Request ID: {request_id}",
            f"Status: {request_status}",
            f"Monitor URL: {request_href}",
            "",
            "Use get_request_status(request_id) to track progress."
        ]
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"Error: Exception occurred while starting service '{service_name}' - {str(e)}"

@mcp.tool()
async def stop_service(service_name: str) -> str:
    """
    Stops a specific service in the Ambari cluster.
    
    Args:
        service_name: Name of the service to stop (e.g., "HDFS", "YARN", "HBASE")
    
    Returns:
        Stop operation result (success: request info, failure: error message)
    """
    cluster_name = AMBARI_CLUSTER_NAME
    try:
        # Check if service exists
        service_endpoint = f"/clusters/{cluster_name}/services/{service_name}"
        service_check = await make_ambari_request(service_endpoint)
        
        if service_check.get("error"):
            return f"Error: Service '{service_name}' not found in cluster '{cluster_name}'."
        
        # Stop the service (set state to INSTALLED)
        payload = {
            "RequestInfo": {
                "context": f"Stop Service {service_name} via MCP API"
            },
            "Body": {
                "ServiceInfo": {
                    "state": "INSTALLED"
                }
            }
        }
        
        response_data = await make_ambari_request(service_endpoint, method="PUT", data=payload)
        
        if response_data.get("error"):
            return f"Error: Failed to stop service '{service_name}' in cluster '{cluster_name}'."
        
        # Extract request information
        request_info = response_data.get("Requests", {})
        request_id = request_info.get("id", "Unknown")
        request_status = request_info.get("status", "Unknown")
        request_href = response_data.get("href", "")
        
        result_lines = [
            f"STOP SERVICE: {service_name}",
            "",
            f"Cluster: {cluster_name}",
            f"Service: {service_name}",
            f"Request ID: {request_id}",
            f"Status: {request_status}",
            f"Monitor URL: {request_href}",
            "",
            "Use get_request_status(request_id) to track progress."
        ]
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"Error: Exception occurred while stopping service '{service_name}' - {str(e)}"

@mcp.tool()
async def get_request_status(request_id: str) -> str:
    """
    Retrieves the status of a specific Ambari request operation.
    
    Args:
        request_id: ID of the request to check
    
    Returns:
        Request status information (success: detailed status, failure: error message)
    """
    cluster_name = AMBARI_CLUSTER_NAME
    try:
        endpoint = f"/clusters/{cluster_name}/requests/{request_id}"
        response_data = await make_ambari_request(endpoint)
        
        if response_data.get("error"):
            return f"Error: Request '{request_id}' not found in cluster '{cluster_name}'."
        
        request_info = response_data.get("Requests", {})
        
        result_lines = [
            f"REQUEST STATUS: {request_id}",
            "",
            f"Cluster: {cluster_name}",
            f"Request ID: {request_info.get('id', request_id)}",
            f"Status: {request_info.get('request_status', 'Unknown')}",
            f"Progress: {request_info.get('progress_percent', 0)}%"
        ]
        
        if "request_context" in request_info:
            result_lines.append(f"Context: {request_info['request_context']}")
        
        if "start_time" in request_info:
            result_lines.append(f"Start Time: {request_info['start_time']}")
        
        if "end_time" in request_info:
            result_lines.append(f"End Time: {request_info['end_time']}")
        
        # Add status explanation
        status = request_info.get('request_status', 'Unknown')
        status_descriptions = {
            'PENDING': 'Request is pending execution',
            'IN_PROGRESS': 'Request is currently running',
            'COMPLETED': 'Request completed successfully',
            'FAILED': 'Request failed',
            'ABORTED': 'Request was aborted',
            'TIMEDOUT': 'Request timed out'
        }
        
        if status in status_descriptions:
            result_lines.append(f"Description: {status_descriptions[status]}")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"Error: Exception occurred while retrieving request status - {str(e)}"

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
