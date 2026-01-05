import os
import inspect
from agenthub.builtin.tools.web_search import WebSearchTool
from agenthub.core.tools import run_resources, tool

@tool(name="web_search", description="Search the web for a query with AI-powered query rewriting")
def web_search(query, exclude_urls):
    num_results = 10
    tool = WebSearchTool()
    return tool.search(query, exclude_urls, max_results=num_results)

_port = int(os.getenv("PORT", "8000"))
_host = os.getenv("HOST", "0.0.0.0")

_sig = inspect.signature(run_resources)
_kwargs = {}
if "port" in _sig.parameters:
    _kwargs["port"] = _port
if "host" in _sig.parameters:
    _kwargs["host"] = _host

run_resources(**_kwargs)
