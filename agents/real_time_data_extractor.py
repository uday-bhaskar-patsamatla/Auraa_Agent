# import asyncio
import json
import os  # Import os to access environment variables
from typing import TypedDict, Optional
from langchain_core.prompts import PromptTemplate

# from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langchain_tavily import TavilySearch
from config import settings

llm = settings.llm  # Use the LLM instance from the settings
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


# Define LangGraph State
class InternetAgentState(TypedDict):
    """
    Represents the state of our internet-connected agent's processing.

    Attributes:
        query (str): The original user query.
        response (str): The real-time answer fetched from the internet.
        source (Optional[str]): URL or source of the fetched information.
    """

    query: str
    response: str
    source: Optional[str]


# Initialize the Tavily search tool.
tavily_tool = TavilySearch(max_results=5)  # Limit to 5 search results for conciseness

# Define Prompt Template
response_template_internet = """
You are an intelligent assistant that can answer questions by searching the internet.
Use the following search results to answer the user's query.
If the search results do not contain enough information, state that you cannot find a definitive answer.

Search Results:
{search_results}

User Query: {query}

Answer:
"""
response_prompt_internet = PromptTemplate(
    template=response_template_internet, input_variables=["search_results", "query"]
)

# Define LangChain Chain
response_chain_internet = response_prompt_internet | llm


# Define Graph Node Function
async def fetch_and_respond(state: InternetAgentState) -> InternetAgentState:
    """
    Fetches information from the internet based on the query and generates a response.

    Args:
        state (InternetAgentState): The current state containing the user query.

    Returns:
        InternetAgentState: The updated state with the response and source URL.
    """
    user_query = state["query"]

    # Perform the web search using the Tavily tool.
    # The output of TavilySearchResults is a list of dictionaries.
    search_results = tavily_tool.invoke({"query": user_query})
    results_list = search_results.get("results", [])

    # We'll concatenate snippets and try to get a primary source URL.
    context_for_llm = ""
    source_url = None
    if results_list:
        # Concatenate snippets from search results
        context_for_llm = "\n\n".join(
            [
                f"Title: {res.get('title', 'N/A')}\nURL: {res.get('url', 'N/A')}\nSnippet: {res.get('content', 'N/A')}"
                for res in results_list
            ]
        )
        # Try to get the URL of the first result as the primary source
        if results_list[0].get("url"):
            source_url = results_list[0]["url"]
    else:
        context_for_llm = "No relevant search results found."
        source_url = "N/A"

    # Invoke the response chain with the search results and query.
    response_result = await response_chain_internet.ainvoke(
        {"search_results": context_for_llm, "query": user_query}
    )
    generated_response = response_result.content.strip()

    # Update the state with the generated response and source.
    return {"query": user_query, "response": generated_response, "source": source_url}


# Build the LangGraph Graph
internet_workflow = StateGraph(InternetAgentState)


internet_workflow.add_node("internet_search_node", fetch_and_respond)
internet_workflow.set_entry_point("internet_search_node")
internet_workflow.set_finish_point("internet_search_node")
internet_app = internet_workflow.compile()


# Agent Invocation Function
async def run_internet_agent(user_query: str) -> str:
    """
    Runs the internet-connected agent to fetch real-time information.

    Args:
        user_query (str): The user's question.

    Returns:
        str: A JSON string containing the original query, the real-time answer, and the source.
    """
    # Initial state for the graph.
    initial_state = {"query": user_query, "response": "", "source": None}

    # Invoke the compiled graph.
    final_state = None
    async for s in internet_app.astream(initial_state):
        final_state = s

    # Extract the results from the final state.
    final_query = final_state["internet_search_node"]["query"]
    final_response = final_state["internet_search_node"]["response"]
    final_source = final_state["internet_search_node"]["source"]

    # Format the output as a JSON string.
    output_json = {
        "query": final_query,
        "response": final_response,
        "source": final_source,
    }
    return json.dumps(output_json, indent=2)
