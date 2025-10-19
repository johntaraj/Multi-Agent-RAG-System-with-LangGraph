# tools.py

from langchain_community.tools.tavily_search import TavilySearchResults

# Initialize the web search tool.
# k=5 means it will return the top 5 most relevant search results.
web_search_tool = TavilySearchResults(k=5)