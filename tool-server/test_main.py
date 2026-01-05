import os
import inspect
from agenthub.builtin.tools.web_search import WebSearchTool
from agenthub.core.tools import run_resources, tool

@tool(name="web_search", description="Search the web for a query with AI-powered query rewriting")
def web_search(query, exclude_urls):
    num_results = 10
    tool = WebSearchTool()
    return tool.search(query, exclude_urls, max_results=num_results)

# Try streamable-http transport
_port = int(os.getenv("PORT", "8000"))
_host = os.getenv("HOST", "0.0.0.0")

# Get the actual run_resources function signature
sig = inspect.signature(run_resources)
kwargs = {}
if "port" in sig.parameters:
    kwargs["port"] = _port
if "host" in sig.parameters:
    kwargs["host"] = _host

print(f"Starting MCP server with kwargs: {kwargs}")
print(f"Using transport: streamable-http")
run_resources(transport="streamable-http", **kwargs)
