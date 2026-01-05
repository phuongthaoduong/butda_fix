from __future__ import annotations

import json
import logging
import multiprocessing
import queue
import re
import time
import asyncio
from typing import Any, AsyncGenerator


try:
    import agenthub as ah
    AGENTHUB_AVAILABLE = True
except ImportError:
    AGENTHUB_AVAILABLE = False

logger = logging.getLogger(__name__)

if not AGENTHUB_AVAILABLE:
    logger.warning("agenthub not available. Research agent functionality will be limited.")


class LLMUnavailableError(RuntimeError):
    """Raised when AISuite/OpenAI clients are not configured."""


LLM_UNAVAILABLE_HINT = (
    "LLM provider unavailable. Set OPENAI_API_KEY or DEEPSEEK_API_KEY in server/.env, "
    "or configure AISuite to use a local provider."
)


class QueueLogHandler(logging.Handler):
    def __init__(self, q: multiprocessing.Queue) -> None:
        super().__init__(level=logging.INFO)
        self.q = q
        self._count = 0
        self._max = 20

    def emit(self, record: logging.LogRecord) -> None:
        if self._count >= self._max:
            return
        msg = getattr(record, "msg", "")
        if not isinstance(msg, str):
            return
        lowered = msg.lower()
        informative = (
            ("reading" in lowered) or
            ("fetch" in lowered) or
            ("download" in lowered) or
            ("analyz" in lowered) or
            ("summar" in lowered)
        )
        if informative:
            try:
                # Extract URL or title from the message
                article_info = self._extract_article_info(msg)
                self.q.put({
                    "step": "log",
                    "detail": msg,
                    "level": record.levelname,
                    "article": article_info
                })
                self._count += 1
            except Exception:
                pass

    def _extract_article_info(self, msg: str) -> dict[str, str] | None:
        """Extract article URL and title from log message."""
        import re

        # Look for URLs in the message
        url_pattern = r'https?://[^\s\)]+'
        urls = re.findall(url_pattern, msg)

        if urls:
            # Clean up the URL (remove trailing punctuation)
            url = urls[0].rstrip('.,;:')

            # Try to extract title from the message
            # Common patterns: "Reading article: Title - URL", "Fetching: URL"
            title_match = re.search(r'(?:reading|fetching|analyzing|summarizing)[^:]*:?\s*?(.+?)(?:\s*-\s*https?://|$)', msg, re.IGNORECASE)

            if title_match:
                title = title_match.group(1).strip(' "\'')
                # Remove trailing URL from title if it got included
                title = re.sub(r'\s*-\s*https?://[^\s]*$', '', title).strip()
                return {"url": url, "title": title}
            else:
                # If no clear title, try to extract from URL domain
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc.replace('www.', '')
                return {"url": url, "title": f"Article from {domain}"}

        return None


def _run_agent_in_process(query: str, result_queue: multiprocessing.Queue, progress_queue: multiprocessing.Queue) -> None:
    """
    Helper function to run agent research in a separate process.
    This isolates agenthub's blocking operations from FastAPI's async event loop.
    """
    try:
        # Load environment variables in the subprocess
        import os
        import sys
        from dotenv import load_dotenv

        # Find .env file from server directory
        server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        env_path = os.path.join(server_dir, ".env")

        # Load .env and set critical environment variables explicitly
        load_dotenv(env_path, override=True)

        # Explicitly set environment variables that aisuite needs
        # This ensures they're available even if dotenv has issues
        if not os.getenv("OPENAI_API_KEY"):
            # Read from .env file directly if not set
            try:
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("OPENAI_API_KEY="):
                            os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()
                        elif line.startswith("DEEPSEEK_API_KEY="):
                            os.environ["DEEPSEEK_API_KEY"] = line.split("=", 1)[1].strip()
                        elif line.startswith("OPENAI_BASE_URL="):
                            os.environ["OPENAI_BASE_URL"] = line.split("=", 1)[1].strip()
            except Exception as e:
                progress_queue.put({"step": "error", "detail": f"Failed to read .env: {str(e)}"})
                return

        # Verify API key is set
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            progress_queue.put({"step": "error", "detail": "No API key found in environment"})
            return

        log_handler = QueueLogHandler(progress_queue)
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.handlers = [log_handler]

        from agenthub.builtin.tools.web_search import WebSearchTool
        from agenthub.core.tools import tool

        progress_queue.put({"step": "init", "detail": "start"})

        @tool(name="web_search", description="Search the web for a query with AI-powered query rewriting")
        def web_search(q, exclude_urls):
            progress_queue.put({"step": "tool", "detail": "web_search"})
            t = WebSearchTool()
            res = t.search(q, exclude_urls, max_results=10)

            try:
                if isinstance(res, list) and res:
                    for item in res:
                        title = getattr(item, 'title', None) or getattr(item, 'name', None) or (item.get('title') if isinstance(item, dict) else 'Unknown')
                        url = getattr(item, 'url', None) or getattr(item, 'link', None) or (item.get('url') if isinstance(item, dict) else '')
                        if isinstance(title, str):
                            title = title.strip('"\'')
                            if ' - ' in title and any(domain in title for domain in ['.com', '.org', '.net', '.gov']):
                                title = title.split(' - ')[0]
                        if url and title != 'Unknown':
                            progress_queue.put({
                                "step": "log",
                                "detail": f"Found article: {title}",
                                "article": {"url": url, "title": title}
                            })
                else:
                    results = getattr(res, "results", None)
                    if isinstance(results, list) and results:
                        for item in results:
                            title = getattr(item, 'title', None) or getattr(item, 'name', None) or (item.get('title') if isinstance(item, dict) else 'Unknown')
                            url = getattr(item, 'url', None) or getattr(item, 'link', None) or (item.get('url') if isinstance(item, dict) else '')
                            if isinstance(title, str):
                                title = title.strip('"\'')
                                if ' - ' in title and any(domain in title for domain in ['.com', '.org', '.net', '.gov']):
                                    title = title.split(' - ')[0]
                            if url and title != 'Unknown':
                                progress_queue.put({
                                    "step": "log",
                                    "detail": f"Found article: {title}",
                                    "article": {"url": url, "title": title}
                                })

                count = len(res) if isinstance(res, list) else len(getattr(res, "results", []))
                progress_queue.put({"step": "tool", "detail": "web_search_results", "count": count})
            except Exception as e:
                progress_queue.put({"step": "log", "detail": f"Error processing results: {str(e)}"})
                try:
                    count = len(res) if isinstance(res, list) else len(getattr(res, "results", []))
                    progress_queue.put({"step": "tool", "detail": "web_search_results", "count": count})
                except Exception:
                    pass

            return res

        progress_queue.put({"step": "agent", "detail": "load"})
        # Use local web_search tool defined above, no need for external MCP server
        agent = ah.load_agent("agentplug/research-agent")
        progress_queue.put({"step": "agent", "detail": "run"})
        result = agent.instant_research(query)
        progress_queue.put({"step": "agent", "detail": "done"})

        result_queue.put({"success": True, "result": result})

    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}"
        progress_queue.put({"step": "error", "detail": error_detail, "traceback": traceback.format_exc()})
        result_queue.put({"success": False, "error": error_detail})


class AgentService:
    """
    Agent service that runs research in separate processes to prevent
    agenthub's blocking operations from interfering with FastAPI's async event loop.
    """

    def __init__(self) -> None:
        pass

    @staticmethod
    def _matches_llm_error(value: Any) -> bool:
        if isinstance(value, str):
            normalized = value.strip().lower()
            return normalized == "aisuite not available"
        return False

    def _llm_unavailable(self, payload: Any) -> bool:
        if self._matches_llm_error(payload):
            return True
        if isinstance(payload, dict):
            for key in ("result", "content", "message", "error", "detail"):
                if key in payload and self._llm_unavailable(payload[key]):
                    return True
        if isinstance(payload, list):
            return any(self._llm_unavailable(item) for item in payload)
        return False

    def _ensure_llm_available(self, payload: Any) -> None:
        if self._llm_unavailable(payload):
            raise LLMUnavailableError(LLM_UNAVAILABLE_HINT)

    def _format_result_content(self, result: dict[str, Any]) -> dict[str, Any]:
        """
        Format research result content - parse JSON if present and convert to markdown.

        Args:
            result: Raw research result from agent

        Returns:
            Processed result with formatted content
        """
        # Extract content from result
        content = result.get("content", "")

        if not content:
            return result

        logger.info(f"Processing content ({len(content)} chars), starts with: {content[:50]}")

        # Remove markdown code blocks if present (```json ... ```)
        content_after_removal = self._remove_code_blocks(content)

        if content_after_removal != content:
            logger.info(f"Code blocks removed, content now: {content_after_removal[:100]}")

        # If content is JSON, parse and format it
        try:
            # Try to parse as JSON
            # First, handle case where content starts with "json {"
            content_stripped = content_after_removal.strip()
            if content_stripped.lower().startswith("json"):
                # Remove "json" prefix
                content_stripped = content_stripped[4:].strip()

            # Try to parse as JSON
            parsed = json.loads(content_stripped)

            # Convert JSON to markdown
            formatted = self._json_to_markdown(parsed)
            result["content"] = formatted
            logger.info(f"Content formatted from JSON to markdown ({len(formatted)} chars)")
        except (json.JSONDecodeError, ValueError) as e:
            # Not JSON or parsing failed, keep as is
            logger.debug(f"Failed to parse content as JSON: {e}, keeping original")
            result["content"] = content_after_removal
            pass

        return result

    def _remove_code_blocks(self, content: str) -> str:
        """Remove markdown code block markers from content."""
        # Pattern to match code blocks: ```json ... ``` or ``` ... ```
        import re
        # Remove code blocks but keep the content inside
        pattern = r'```(?:json|JSON)?\s*\n?(.*?)\n?```'
        matches = re.findall(pattern, content, re.DOTALL)
        if matches:
            # If we found a code block, return its content
            return matches[0].strip()

        # Fallback: remove leading/trailing ``` markers
        lines = content.split('\n')
        while lines and lines[0].strip().startswith('```'):
            lines = lines[1:]
        while lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        return '\n'.join(lines).strip()

    def _json_to_markdown(self, data: Any, indent: int = 0) -> str:
        """
        Convert JSON data to markdown format.

        Args:
            data: Parsed JSON data
            indent: Current indentation level

        Returns:
            Markdown formatted string
        """
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                key_formatted = key.replace('_', ' ').title()
                if isinstance(value, dict):
                    if indent == 0:
                        # Top level - use heading
                        lines.append(f"\n## {key_formatted}")
                    else:
                        # Nested dict - use bold heading
                        lines.append(f"\n**{key_formatted}**")
                    lines.append(self._json_to_markdown(value, indent + 1))
                elif isinstance(value, list):
                    if indent == 0:
                        lines.append(f"\n## {key_formatted}")
                    else:
                        lines.append(f"\n**{key_formatted}**")
                    for item in value:
                        if isinstance(item, (dict, list)):
                            lines.append(self._json_to_markdown(item, indent + 1))
                        else:
                            lines.append(f"- {item}")
                else:
                    lines.append(f"- **{key_formatted}**: {value}")
            return "\n".join(lines)
        elif isinstance(data, list):
            lines = []
            for item in data:
                if isinstance(item, dict):
                    lines.append(self._json_to_markdown(item, indent))
                else:
                    lines.append(f"- {item}")
            return "\n".join(lines)
        else:
            return str(data)

    def search(self, query: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Perform research by spawning a separate process.
        This prevents agenthub's WebSocket server from blocking FastAPI.
        """
        normalized_query = " ".join(query.split())
        logger.info("Starting agent research in separate process", extra={"query": normalized_query})

        if not AGENTHUB_AVAILABLE:
            raise RuntimeError("agenthub is not available")

        try:
            manager = multiprocessing.Manager()
            result_queue = manager.Queue()
            progress_queue = manager.Queue()

            process = multiprocessing.Process(
                target=_run_agent_in_process,
                args=(normalized_query, result_queue, progress_queue)
            )

            process.start()
            logger.info("Agent process started", extra={"pid": process.pid, "query": normalized_query})

            research_done = False
            
            # Wait until research completes
            while not research_done:
                try:
                    while True:
                        ev = progress_queue.get_nowait()
                        step = ev.get("step")
                        detail = ev.get("detail")
                        
                        if step == "init":
                            logger.info("Initializing research agent...", extra={"query": normalized_query})
                        elif step == "agent" and detail == "load":
                            logger.info("Loading research agent...", extra={"query": normalized_query})
                        elif step == "agent" and detail == "run":
                            logger.info("Agent loaded. Starting research...", extra={"query": normalized_query})
                        elif step == "tool" and detail == "web_search":
                            logger.info("Calling web_search tool", extra={"query": normalized_query})
                        elif step == "agent" and detail == "done":
                            logger.info("Research finished", extra={"query": normalized_query})
                            research_done = True
                            break
                        elif step == "log":
                            pass
                        elif step == "error":
                            logger.error(detail, extra={"query": normalized_query})
                except queue.Empty:
                    # Check if process died unexpectedly (before sending "done")
                    if not process.is_alive() and not research_done:
                        raise RuntimeError("Agent process died unexpectedly")
                    pass
                
                time.sleep(0.2)
            
            # Get result immediately (it's already in the queue after "done")
            logger.info("Getting result from queue...", extra={"query": normalized_query})
            try:
                result_data = result_queue.get(timeout=20.0)
            except queue.Empty:
                raise RuntimeError("No result received from agent process - queue timeout")
            
            # Continue draining progress_queue to prevent deadlock
            # This prevents the process from blocking on queue.put() operations
            logger.info("Draining progress queue to prevent deadlock...", extra={"query": normalized_query})
            while process.is_alive():
                try:
                    ev = progress_queue.get_nowait()
                    # Log any remaining progress messages
                    step = ev.get("step")
                    if step == "log":
                        logger.info(ev.get("detail"))
                    elif step == "error":
                        logger.error(ev.get("detail"), extra={"query": normalized_query})
                except queue.Empty:
                    time.sleep(0.1)
            
            # Don't call process.join() - let it exit naturally
            # The result is already retrieved, so we can return immediately

            if not result_data["success"]:
                raise RuntimeError(f"Agent process failed: {result_data['error']}")

            agent_result = result_data["result"]
            self._ensure_llm_available(agent_result)

            logger.info("Agent research completed successfully", extra={"query": normalized_query})
            return agent_result

        except Exception as e:
            logger.error("Agent research failed", exc_info=True, extra={"query": normalized_query})
            raise RuntimeError(f"Research failed: {str(e)}") from e
        finally:
            if 'process' in locals() and process.is_alive():
                process.terminate()
                process.join(timeout=5)
            if 'manager' in locals():
                try:
                    manager.shutdown()
                except Exception:
                    pass

    async def search_with_thoughts(self, query: str) -> AsyncGenerator[dict[str, Any], None]:
        normalized_query = " ".join(query.split())
        logger.info("Starting agent research with thoughts", extra={"query": normalized_query})
        yield {"stage": "starting", "message": "Understanding your query..."}
        if not AGENTHUB_AVAILABLE:
            yield {"stage": "error", "message": "Research service unavailable", "error": "agenthub not available"}
            return
        try:
            result_queue = multiprocessing.Queue()
            progress_queue = multiprocessing.Queue()
            process = multiprocessing.Process(target=_run_agent_in_process, args=(normalized_query, result_queue, progress_queue))
            process.start()
            logger.info("Agent process started", extra={"pid": process.pid, "query": normalized_query})
            yield {"stage": "loading", "message": "Preparing search..."}
            research_done = False
            sources_found = 0
            first_search = True
            while not research_done:
                try:
                    while True:
                        ev = progress_queue.get_nowait()
                        step = ev.get("step")
                        detail = ev.get("detail")
                        if step == "agent" and detail == "load":
                            yield {"stage": "loading", "message": "Preparing research tools..."}
                        elif step == "agent" and detail == "run":
                            if first_search:
                                yield {"stage": "searching", "message": "Searching for relevant information..."}
                                first_search = False
                        elif step == "tool" and detail == "web_search":
                            # Don't repeat search messages too frequently
                            if sources_found < 3:
                                yield {"stage": "searching", "message": "Discovering sources..."}
                        elif step == "tool" and detail == "web_search_results":
                            cnt = ev.get("count")
                            if isinstance(cnt, int) and cnt >= 0:
                                sources_found = cnt
                                # Only show count once or if significant
                                if sources_found > 0:
                                    yield {"stage": "searching", "message": "Found relevant sources"}
                        elif step == "agent" and detail == "done":
                            yield {"stage": "thinking", "message": "Analyzing findings..."}
                            research_done = True
                            break
                        elif step == "log" and isinstance(detail, str):
                            article = ev.get("article")
                            if article and "url" in article and "title" in article:
                                title = article.get("title", "Unknown article")
                                # Truncate long titles
                                if len(title) > 50:
                                    title = title[:47] + "..."

                                # Simplified and consistent article messages
                                if "Found article" in detail:
                                    yield {
                                        "stage": "searching",
                                        "message": "Found relevant source",
                                        "details": title,
                                        "article_url": article["url"]
                                    }
                                else:
                                    # For reading, fetching, processing - use one consistent message
                                    yield {
                                        "stage": "reading",
                                        "message": "Reviewing content",
                                        "details": title,
                                        "article_url": article["url"]
                                    }
                            else:
                                # Fallback for generic logs
                                if "Reading" in detail or "reading" in detail:
                                    yield {"stage": "reading", "message": "Reading source..."}
                                elif "Fetching" in detail or "fetching" in detail:
                                    yield {"stage": "reading", "message": "Fetching source..."}
                        elif step == "error":
                            # Pass through full error detail from agent
                            yield {"stage": "error", "message": detail, "error": detail}
                            return
                except queue.Empty:
                    if not process.is_alive() and not research_done:
                        yield {"stage": "error", "message": "Research interrupted", "error": "Agent process died"}
                        return
                await asyncio.sleep(0.2)
            try:
                result_data = result_queue.get(timeout=10.0)
            except queue.Empty:
                yield {"stage": "error", "message": "Research timeout", "error": "No result received"}
                return
            while process.is_alive():
                try:
                    _ = progress_queue.get_nowait()
                except queue.Empty:
                    break
            if not result_data.get("success"):
                yield {"stage": "error", "message": "Research failed", "error": result_data.get("error", "Unknown error")}
                return

            try:
                agent_result = result_data["result"]
                self._ensure_llm_available(agent_result)
            except LLMUnavailableError as exc:
                yield {
                    "stage": "error",
                    "message": str(exc),
                    "error": "llm_unavailable"
                }
                return

            yield {"stage": "writing", "message": "Creating your summary..."}

            # Process the result content - if it's JSON, format it nicely
            # agent_result has structure: {'result': {...}, 'execution_time': ...}
            inner_result = agent_result.get("result", agent_result)
            logger.info(f"Formatting inner_result: {type(inner_result)}, keys: {list(inner_result.keys()) if isinstance(inner_result, dict) else 'N/A'}")
            processed_result = self._format_result_content(inner_result)

            # Keep the original structure
            processed_result = {
                "result": processed_result,
                "execution_time": agent_result.get("execution_time")
            }

            yield {"stage": "complete", "success": True, "data": processed_result}
        except Exception as e:
            logger.error("Agent research with thoughts failed", exc_info=True, extra={"query": normalized_query})
            yield {"stage": "error", "message": "Research failed", "error": str(e)}
        finally:
            if 'process' in locals() and process.is_alive():
                process.terminate()
                process.join(timeout=5)
