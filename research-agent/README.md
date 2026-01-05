# Being-Up-To-Date Assistant Tooling (AgentHub)

This document explains how to use agenthub and activate the tool server for the research agent.

## Prerequisites

Make sure you have Python 3 installed on your system. The tool server and research agent require Python 3 to run.

## Understanding the Architecture

The research agent uses the agenthub framework to load agents with specific capabilities. In this case, the research agent is loaded with the web search tool:

```python
import agenthub as ah

research_agent = ah.load_agent("agentplug/research-agent", external_tools=["web_search"])
```

The web search tool runs as a separate process called the "tool server" to allow the research agent to access web search capabilities.

## Activating the Tool Server

1. Open a new terminal window
2. Navigate to the research-agent directory:
   ```bash
   cd research-agent
   ```
3. Run the tool server:
   ```bash
   python3 tool_server.py
   ```

The tool server will start and display output similar to:
```
INFO:     Started server process [32761]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Keep this terminal running while you use the research agent.

## Using the Assistant Agent

1. Open another terminal window
2. Navigate to the research-agent directory:
   ```bash
   cd research-agent
   ```
3. Run the research agent:
   ```bash
   python3 research_agent.py
   ```

The research agent will execute the query defined in the file and display the results.

## How It Works

1. The tool server runs as an independent process that provides the web search capability
2. The research agent is loaded with the `external_tools=["web_search"]` parameter
3. When the research agent needs to perform a web search, it communicates with the tool server
4. The tool server executes the search and returns the results to the research agent
5. The research agent processes the results and generates a final response

## Troubleshooting

If you encounter issues:

1. Make sure the tool server is running before executing the research agent
2. Check that you're using `python3` instead of `python` if the latter is not available
3. Ensure both terminals are running in the correct directory
4. Check that no firewall is blocking the communication between the research agent and tool server

## Customizing the Research Query

To change the research query, modify the `research_agent.py` file:

```python
query = "Your new research question here"
result = research_agent.standard_research(query)
print(result)
```

Then run the research agent again:
```bash
python3 research_agent.py
```
