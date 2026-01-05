#!/usr/bin/env python3
"""
Detailed API debugging test script.
Usage: python debug_test.py

This script provides detailed debugging information for:
- Backend connectivity
- API endpoint status
- Stream endpoint functionality
- Error diagnostics
"""

import requests
import json
import sys
import time
import os
from typing import Tuple, Optional

BASE_URL = os.getenv("API_URL", "http://localhost:8001")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def print_section(title: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'═'*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'═'*60}{Colors.RESET}\n")

def print_test(name: str, passed: bool, details: str = "", data: Optional[dict] = None):
    icon = f"{Colors.GREEN}✓{Colors.RESET}" if passed else f"{Colors.RED}✗{Colors.RESET}"
    status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
    print(f"  {icon} {Colors.BOLD}{name}{Colors.RESET} [{status}]")
    if details:
        print(f"    {Colors.CYAN}➜{Colors.RESET} {details}")
    if data and not passed:
        print(f"    {Colors.YELLOW}Debug info:{Colors.RESET}")
        print(f"    {json.dumps(data, indent=6, ensure_ascii=False)}")

def check_backend_running() -> Tuple[bool, str]:
    """Check if backend server is running."""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=3)
        if response.status_code == 200:
            data = response.json()
            return True, f"Backend is healthy - {data.get('service', 'unknown')}"
        return False, f"Backend returned HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to {BASE_URL} - is the backend running?"
    except requests.exceptions.Timeout:
        return False, f"Connection timeout - backend may be starting or stuck"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def check_frontend_running() -> Tuple[bool, str]:
    """Check if frontend server is running."""
    try:
        response = requests.get(FRONTEND_URL, timeout=3)
        if response.status_code == 200:
            return True, f"Frontend accessible at {FRONTEND_URL}"
        return False, f"Frontend returned HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to {FRONTEND_URL} - is the frontend running?"
    except Exception as e:
        return False, f"Error: {str(e)}"

def check_cors_config() -> Tuple[bool, str]:
    """Check CORS configuration."""
    try:
        response = requests.options(
            f"{BASE_URL}/api/research",
            headers={
                "Origin": FRONTEND_URL,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            },
            timeout=3
        )
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
        }
        allowed = cors_headers["Access-Control-Allow-Origin"] in ["*", FRONTEND_URL]
        return allowed, f"CORS {'configured' if allowed else 'misconfigured'}", cors_headers
    except Exception as e:
        return False, f"Error checking CORS: {str(e)}", {}

def test_stream_endpoint_basic() -> Tuple[bool, str]:
    """Test if stream endpoint responds."""
    try:
        response = requests.get(
            f"{BASE_URL}/api/research/stream",
            params={"query": "test"},
            timeout=5,
            stream=True
        )
        # Read a few lines to check it's sending events
        lines = []
        for line in response.iter_lines():
            if line:
                lines.append(line.decode('utf-8'))
            if len(lines) >= 3:
                break
        response.close()

        is_sse = response.headers.get("Content-Type", "").startswith("text/event-stream")
        return is_sse, f"Stream endpoint {'working (SSE)' if is_sse else 'not SSE format'}", {
            "content_type": response.headers.get("Content-Type"),
            "first_lines": lines[:3]
        }
    except Exception as e:
        return False, f"Stream error: {str(e)}", {"error": str(e)}

def test_env_config() -> Tuple[bool, str]:
    """Check environment configuration."""
    issues = []
    warnings = []

    # Check if .env file exists
    env_path = os.path.join(os.path.dirname(__file__), "..", "server", ".env")
    if not os.path.exists(env_path):
        issues.append("server/.env file not found")
    else:
        # Try to read and check for API keys
        try:
            with open(env_path, "r") as f:
                env_content = f.read()
                has_openai_key = bool("OPENAI_API_KEY=" in env_content and not "OPENAI_API_KEY=" in env_content.split("OPENAI_API_KEY=")[1].split("\n")[0].strip() == "")
                has_deepseek_key = bool("DEEPSEEK_API_KEY=" in env_content and not "DEEPSEEK_API_KEY=" in env_content.split("DEEPSEEK_API_KEY=")[1].split("\n")[0].strip() == "")
                has_base_url = "OPENAI_BASE_URL=" in env_content

                if not has_openai_key and not has_deepseek_key:
                    issues.append("No API key configured (need OPENAI_API_KEY or DEEPSEEK_API_KEY)")
                if has_deepseek_key and not has_base_url:
                    warnings.append("Using DeepSeek but OPENAI_BASE_URL might not be set")
        except Exception as e:
            issues.append(f"Could not read .env file: {str(e)}")

    return len(issues) == 0, f"Config check: {len(issues)} issue(s), {len(warnings)} warning(s)", {
        "issues": issues,
        "warnings": warnings
    }

def main():
    print(f"{Colors.BOLD}BUTDA Debug Test Suite{Colors.RESET}")
    print(f"Backend URL: {BASE_URL}")
    print(f"Frontend URL: {FRONTEND_URL}")

    # Section 1: Server Status
    print_section("1. Server Status Check")
    backend_ok, backend_msg = check_backend_running()
    print_test("Backend Server", backend_ok, backend_msg)

    frontend_ok, frontend_msg = check_frontend_running()
    print_test("Frontend Server", frontend_ok, frontend_msg)

    if not backend_ok:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Backend is not running!{Colors.RESET}")
        print(f"{Colors.YELLOW}Start it with:{Colors.RESET}")
        print(f"  cd server && source .venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8001 --reload")
        return 1

    # Section 2: Configuration
    print_section("2. Configuration Check")
    config_ok, config_msg, config_data = test_env_config()
    print_test("Environment Config", config_ok, config_msg, config_data)
    if not config_ok:
        print(f"{Colors.YELLOW}  Issues:{Colors.RESET}")
        for issue in config_data.get("issues", []):
            print(f"    • {issue}")
    if config_data.get("warnings"):
        print(f"{Colors.YELLOW}  Warnings:{Colors.RESET}")
        for warning in config_data.get("warnings", []):
            print(f"    • {warning}")

    # Section 3: CORS Check
    print_section("3. CORS Configuration")
    cors_ok, cors_msg, cors_data = check_cors_config()
    print_test("CORS Headers", cors_ok, cors_msg)
    if not cors_ok:
        print(f"{Colors.YELLOW}  Current headers:{Colors.RESET}")
        for key, value in cors_data.items():
            if value:
                print(f"    {key}: {value}")

    # Section 4: Stream Endpoint
    print_section("4. Stream Endpoint Test")
    stream_ok, stream_msg, stream_data = test_stream_endpoint_basic()
    print_test("Stream Response", stream_ok, stream_msg, stream_data)
    if not stream_ok and "error" in stream_data:
        print(f"{Colors.YELLOW}  Error details:{Colors.RESET} {stream_data['error']}")
    elif stream_ok and "first_lines" in stream_data:
        print(f"{Colors.YELLOW}  Sample lines:{Colors.RESET}")
        for line in stream_data["first_lines"][:2]:
            print(f"    {line[:80]}...")

    # Section 5: Full Stream Test
    print_section("5. Full Stream Test (with events)")
    try:
        print(f"{Colors.CYAN}Testing stream with query 'Python 3.13'...{Colors.RESET}")
        response = requests.get(
            f"{BASE_URL}/api/research/stream",
            params={"query": "Python 3.13"},
            timeout=30,
            stream=True
        )

        events = []
        start_time = time.time()
        timeout = 20  # 20 seconds max for this test

        for line in response.iter_lines():
            if time.time() - start_time > timeout:
                print(f"  {Colors.YELLOW}⚠ Test timeout after {timeout}s{Colors.RESET}")
                break
            if line:
                decoded = line.decode('utf-8')
                events.append(decoded)
                if decoded.startswith("data:"):
                    try:
                        data = json.loads(decoded[5:].strip())
                        stage = data.get("stage", "unknown")
                        msg = data.get("message", "")
                        print(f"  {Colors.GREEN}→{Colors.RESET} Event: {stage}" + (f" - {msg}" if msg else ""))
                        if stage == "error":
                            print(f"    {Colors.RED}Error code: {data.get('code', 'unknown')}{Colors.RESET}")
                            break
                        if stage == "complete":
                            print(f"    {Colors.GREEN}✓ Research completed!{Colors.RESET}")
                            break
                    except json.JSONDecodeError:
                        pass
                elif decoded.startswith("event:"):
                    print(f"  {Colors.CYAN}→{Colors.RESET} Event type: {decoded[6:].strip()}")

        response.close()

        if events:
            print_test("Stream Events", True, f"Received {len(events)} events")
        else:
            print_test("Stream Events", False, "No events received")

    except Exception as e:
        print_test("Stream Events", False, str(e))

    # Summary
    print_section("Summary")
    all_ok = backend_ok and frontend_ok and config_ok and cors_ok and stream_ok
    if all_ok:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All checks passed!{Colors.RESET}")
        print(f"\n{Colors.GREEN}Your BUTDA setup looks good!{Colors.RESET}")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Some checks failed{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Suggestions:{Colors.RESET}")
        if not frontend_ok:
            print(f"  • Start frontend: cd client && npm run dev")
        if not config_ok:
            print(f"  • Check server/.env - ensure API keys are set")
        if not cors_ok:
            print(f"  • Check CORS configuration in main.py")
        if not stream_ok:
            print(f"  • Check agent service logs for errors")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.RESET}")
        sys.exit(1)
