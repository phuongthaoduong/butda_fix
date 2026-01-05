#!/usr/bin/env python3
"""
Simple HTTP server for web_search tool.
Provides a REST endpoint that the research agent can use for web search.
"""

import os
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from agenthub.builtin.tools.web_search import WebSearchTool

app = FastAPI(title="Web Search Tool Server")


class SearchRequest(BaseModel):
    query: str
    exclude_urls: List[str] = []
    max_results: int = 10


@app.get("/")
async def root():
    return {
        "service": "web_search_tool",
        "version": "1.0",
        "endpoints": {
            "/tools/web_search": "POST - Execute web search",
            "/tools/{tool_name}": "POST - Generic tool execution (MCP client format)",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/tools/web_search")
async def web_search(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute web search using the WebSearchTool.

    Accepts both direct format and MCP client format with "arguments" wrapper.
    Direct: {"query": "...", "exclude_urls": [], "max_results": N}
    MCP format: {"arguments": {"query": "...", "exclude_urls": [], "max_results": N}}
    """
    try:
        # Handle both direct and wrapped formats
        if "arguments" in payload:
            arguments = payload["arguments"]
            query = arguments.get("query", "")
            exclude_urls = arguments.get("exclude_urls", [])
            max_results = arguments.get("max_results", 10)
        else:
            query = payload.get("query", "")
            exclude_urls = payload.get("exclude_urls", [])
            max_results = payload.get("max_results", 10)

        tool = WebSearchTool()
        results = tool.search(query, exclude_urls, max_results=max_results)

        # Convert results to a consistent format
        formatted_results = []

        # Handle dict with results key (WebSearchTool returns this format)
        if isinstance(results, dict) and 'results' in results:
            results_list = results['results']
        # Handle list results
        elif isinstance(results, list):
            results_list = results
        # Handle object with results attribute
        elif hasattr(results, 'results'):
            results_list = results.results
        else:
            results_list = []

        for item in results_list:
            # For dicts, use direct key access
            if isinstance(item, dict):
                title = item.get('title', 'Unknown')
                url = item.get('url', '')
                snippet = item.get('snippet') or item.get('description') or item.get('content', '')
                snippet = snippet[:500] if len(snippet) > 500 else snippet
                if url:
                    formatted_results.append({
                        "title": str(title),
                        "url": str(url),
                        "snippet": str(snippet)[:500]
                    })
            else:
                # For objects, use attribute access
                title = getattr(item, 'title', 'Unknown')
                url = getattr(item, 'url', '')
                snippet = getattr(item, 'snippet', '') or getattr(item, 'description', '') or getattr(item, 'content', '')
                snippet = str(snippet)[:500] if len(str(snippet)) > 500 else str(snippet)
                if url:
                    formatted_results.append({
                        "title": str(title),
                        "url": str(url),
                        "snippet": str(snippet)[:500]
                    })

        return {
            "type": "web_search_result",
            "query": query,
            "exclude_urls": exclude_urls,
            "results": formatted_results,
            "total_results": len(formatted_results),
            "source": "web_search_tool"
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Additional endpoint to match AgentHubMCPClient HTTP fallback format
@app.post("/tools/{tool_name}")
async def execute_tool(tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generic tool execution endpoint that matches AgentHubMCPClient HTTP fallback format.
    The client sends: {"arguments": {"query": "...", "exclude_urls": [...], "max_results": N}}
    """
    try:
        if tool_name == "web_search":
            # Call the web_search endpoint with the payload
            return await web_search(payload)
        else:
            raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")

    print(f"Starting Web Search Tool Server on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
