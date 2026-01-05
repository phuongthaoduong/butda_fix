#!/usr/bin/env python3
"""
API Stream Test - Full End-to-End Testing

This script tests the complete research API flow including:
1. Health check
2. Stream endpoint connectivity
3. SSE event parsing
4. JSON response formatting
5. Error handling

Usage:
    python tests/test_api_stream.py
    python tests/test_api_stream.py --query "What is Python?"
    python tests/test_api_stream.py --query "test" --timeout 30

Requirements:
    - Backend running on http://localhost:8001
    - Valid API keys configured in server/.env
"""

import argparse
import json
import sys
import time
from typing import Optional

import requests


# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


class APIStreamTester:
    """Tester for the research API stream endpoint."""

    def __init__(self, base_url: str = "http://localhost:8001"):
        """
        Initialize the API tester.

        Args:
            base_url: Base URL of the backend API
        """
        self.base_url = base_url
        self.stream_url = f"{base_url}/api/research/stream"
        self.health_url = f"{base_url}/api/health"

    def print_header(self, text: str) -> None:
        """Print a formatted header."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    def print_success(self, text: str) -> None:
        """Print success message."""
        print(f"{Colors.GREEN}✓{Colors.RESET} {text}")

    def print_error(self, text: str) -> None:
        """Print error message."""
        print(f"{Colors.RED}✗{Colors.RESET} {text}")

    def print_info(self, text: str) -> None:
        """Print info message."""
        print(f"{Colors.CYAN}ℹ{Colors.RESET} {text}")

    def check_health(self) -> bool:
        """
        Check if the backend API is healthy.

        Returns:
            True if backend is healthy, False otherwise
        """
        try:
            response = requests.get(self.health_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Backend is healthy - {data.get('service', 'unknown')}")
                return True
            else:
                self.print_error(f"Backend returned HTTP {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.print_error(f"Cannot connect to {self.base_url}")
            self.print_info("Start the backend with: cd server && uvicorn main:app --host 0.0.0.0 --port 8001")
            return False
        except Exception as e:
            self.print_error(f"Health check failed: {e}")
            return False

    def test_stream(
        self,
        query: str,
        timeout: int = 90,
        verbose: bool = False
    ) -> dict[str, any]:
        """
        Test the stream endpoint with a research query.

        Args:
            query: Research query to test
            timeout: Maximum time to wait for completion (seconds)
            verbose: Whether to print all events

        Returns:
            Dictionary with test results
        """
        self.print_header(f"Testing Stream Endpoint")
        self.print_info(f"Query: {query}")
        self.print_info(f"Timeout: {timeout}s")

        result = {
            "success": False,
            "query": query,
            "events_received": 0,
            "stages": [],
            "final_content": None,
            "error": None,
            "duration_ms": 0
        }

        try:
            start_time = time.time()
            response = requests.get(
                self.stream_url,
                params={"query": query},
                stream=True,
                timeout=timeout + 5
            )

            if response.status_code != 200:
                result["error"] = f"HTTP {response.status_code}"
                self.print_error(f"Stream endpoint returned HTTP {response.status_code}")
                return result

            self.print_success("Stream connection established")

            # Process SSE events
            for line in response.iter_lines():
                if time.time() - start_time > timeout:
                    result["error"] = "Timeout"
                    self.print_error(f"Timeout after {timeout}s")
                    break

                if not line:
                    continue

                decoded = line.decode('utf-8')
                result["events_received"] += 1

                if verbose:
                    print(f"  [{result['events_received']}] {decoded[:100]}")

                if decoded.startswith("event:"):
                    event_type = decoded[6:].strip()
                    result["stages"].append(event_type)
                    if verbose:
                        print(f"    → Event type: {Colors.CYAN}{event_type}{Colors.RESET}")

                elif decoded.startswith("data:"):
                    try:
                        data = json.loads(decoded[5:].strip())
                        stage = data.get("stage", "")
                        message = data.get("message", "")

                        if stage == "progress":
                            if verbose:
                                print(f"    → {Colors.GREEN}{stage}{Colors.RESET}: {message}")
                            elif message not in ["Searching for relevant information...", "Analyzing findings..."]:
                                print(f"  {Colors.BLUE}→{Colors.RESET} {message}")

                        elif stage == "complete":
                            self.print_success("Research completed!")
                            result["success"] = True

                            # Extract and format content
                            content_data = data.get("data", {})
                            inner_result = content_data.get("result", {})
                            result["final_content"] = inner_result.get("content", "") or content_data.get("content", "")

                            # Show content preview
                            if result["final_content"]:
                                preview = result["final_content"][:200].replace('\n', ' ')
                                print(f"\n{Colors.BOLD}Content Preview:{Colors.RESET}")
                                print(f"  {preview}...")
                                print(f"\n{Colors.GREEN}✓ JSON formatting applied{Colors.RESET}")

                            break

                        elif stage == "error":
                            error_msg = data.get("message", "Unknown error")
                            error_code = data.get("code", "unknown")
                            result["error"] = f"{error_code}: {error_msg}"
                            self.print_error(f"Error: {error_msg}")
                            if error_code != "unknown":
                                print(f"  Code: {Colors.YELLOW}{error_code}{Colors.RESET}")
                            break

                    except json.JSONDecodeError:
                        # Ignore non-JSON data lines
                        pass

            result["duration_ms"] = int((time.time() - start_time) * 1000)

        except requests.exceptions.Timeout:
            result["error"] = "Request timeout"
            self.print_error("Request timeout")
        except requests.exceptions.ConnectionError:
            result["error"] = "Connection failed"
            self.print_error("Connection failed")
        except Exception as e:
            result["error"] = str(e)
            self.print_error(f"Unexpected error: {e}")

        return result

    def print_summary(self, result: dict[str, any]) -> None:
        """Print test result summary."""
        self.print_header("Test Summary")

        print(f"Query: {result['query']}")
        print(f"Duration: {result['duration_ms']}ms")
        print(f"Events received: {result['events_received']}")

        if result["success"]:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ TEST PASSED{Colors.RESET}")
            if result["final_content"]:
                content_len = len(result["final_content"])
                print(f"Content length: {content_len} characters")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ TEST FAILED{Colors.RESET}")
            print(f"Error: {result['error']}")

        print(f"\n{'='*60}\n")

        # Show full content if available
        if result["final_content"] and result["success"]:
            self.print_info("Full formatted content:")
            print("-" * 60)
            print(result["final_content"])
            print("-" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test the BUTDA research API stream endpoint"
    )
    parser.add_argument(
        "--query",
        "-q",
        default="What is artificial intelligence?",
        help="Research query to test (default: 'What is artificial intelligence?')"
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=90,
        help="Maximum time to wait for completion in seconds (default: 90)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print all SSE events for debugging"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8001",
        help="Backend API base URL (default: http://localhost:8001)"
    )

    args = parser.parse_args()

    # Run tests
    tester = APIStreamTester(base_url=args.url)

    # Check health first
    if not tester.check_health():
        sys.exit(1)

    # Test stream endpoint
    result = tester.test_stream(
        query=args.query,
        timeout=args.timeout,
        verbose=args.verbose
    )

    # Print summary
    tester.print_summary(result)

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
