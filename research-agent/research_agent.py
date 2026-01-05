import agenthub as ah

research_agent = ah.load_agent("agentplug/research-agent", external_tools=["web_search"])

query = "Latest news about Cambodia war?"
result = research_agent.instant_research(query)
print(result)

