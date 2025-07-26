from mcp.server.fastmcp import FastMCP


# Create an MCP server
mcp = FastMCP("mcp-add")


# Add an additional tool
@mcp.tool()
def weather(a: int, b: int) -> int:
    """
    This tool performs addition of two integers. 
    It is designed to take two numbers as input and return their sum, 
    enabling simple arithmetic operations within workflows.
    """
    return a + b


# Add a dynamic greeing resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


if __name__ == "__main__":
    # mcp.run(transport="stdio")
    mcp.run(transport="sse")