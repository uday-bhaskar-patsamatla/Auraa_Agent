from agents.real_time_data_extractor import run_internet_agent
from agents.document_summarizer import run_document_agent
from agents.query_responder import run_query_responder_agent

import json
import os
from typing import TypedDict, List, Optional, Union
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from langchain_core.messages import (
    ToolMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)

from config import settings

#  Environment Variable Setup (Crucial for all agents)
if "OPENAI_API_KEY" not in os.environ:
    print(
        "WARNING: OPENAI_API_KEY environment variable not set. Please set it to use OpenAI models."
    )
if "TAVILY_API_KEY" not in os.environ:
    print(
        "WARNING: TAVILY_API_KEY environment variable not set. Please set it to use the Tavily search tool (Agent 3)."
    )


#  Shared LLM Instance
llm = settings.llm


#  Define Tools for the Main Agent
@tool(
    description="Summarizes a document and extracts keywords. Use this tool when the user provides a document or text and asks for a summary or keywords. Input should be the full document text."
)
async def summarize_document(document_text: str) -> str:
    """
    Summarizes a given document content and extracts a list of keywords.
    Input: A string representing the document content.
    Output: A JSON string with 'document' (summary) and 'keywords' (list of strings).
    Example: {"document": "Summary of text.", "keywords": ["keyword1", "keyword2"]}
    """
    print(
        f"Main Agent: Invoking summarize_document tool with document length {len(document_text)}."
    )
    result = await run_document_agent(document_text)
    print(f"Summarize Document Tool Output: {result}")
    return result


@tool(
    description="Answers a user's question based on provided document content. Use this tool when the user provides a question AND specific context/documents to answer from. Input requires both the 'user_query' and a 'documents_list' (list of strings)."
)
async def answer_query_from_documents(
    user_query: str, documents_list: List[str]
) -> str:
    """
    Answers a user's question based on provided document content.
    Input:
        - user_query (str): The question to answer.
        - documents_list (List[str]): A list of strings, where each string is a document or a part of a document.
    Output: A JSON string with 'query' and 'response'.
    Example: {"query": "What is x?", "response": "Answer for x."}
    """
    print(
        f"Main Agent: Invoking answer_query_from_documents tool with query '{user_query}' and {len(documents_list)} documents."
    )
    result = await run_query_responder_agent(user_query, documents_list)
    print(f"Answer Query from Documents Tool Output: {result}")
    return result


@tool(
    description="Fetches real-time, up-to-date information from the internet to answer a user's question. Use this tool when the user's question requires current information, external knowledge, or is not answerable from provided documents. Input is the 'user_query' string."
)
async def search_internet(user_query: str) -> str:
    """
    Fetches real-time, up-to-date information from the internet to answer a user's question.
    Input: A string representing the user's question that requires internet search.
    Output: A JSON string with 'query', 'response', and 'source' (URL).
    Example: {"query": "Latest news on AI?", "response": "AI is advancing rapidly...", "source": "https://example.com"}
    """
    print(f"Main Agent: Invoking search_internet tool with query '{user_query}'.")
    result = await run_internet_agent(user_query)
    print(f"Search Internet Tool Output: {result}")
    return result


# List of all tools available to the main agent
tools = [summarize_document, answer_query_from_documents, search_internet]

#  Main Graph Agent


# Define Main Agent State
class MainAgentState(TypedDict):
    """
    Represents the state of the main routing agent.
    The 'messages' field will store the conversation history, including tool calls and outputs.
    """

    messages: List[Union[HumanMessage, AIMessage, ToolMessage]]
    selected_tool_name: Optional[
        str
    ]  # To store the name of the tool selected by the router
    tool_raw_output: Optional[str]  # To store the raw JSON output from the tool
    natural_language_response: Optional[str]
    justification: Optional[str]


# Define Router LLM and Prompt for Tool Calling
router_llm_with_tools = llm.bind_tools(tools)

system_prompt = SystemMessage(
    content="""
    You are a powerful orchestrator agent named Auraa. Your primary role is to answer the user by analyzing the user's request and determining the most appropriate specialized tool to use.
    You have access to the following tools: summarize_document, answer_query_from_documents, search_internet.
    When a tool is selected, you must call it with the correct arguments.
    If the user's request can be answered by one of the tools, you must use that tool.
    If no tool is suitable, respond directly to the user indicating you cannot fulfill the request.
    """
)

router_prompt_for_tools = ChatPromptTemplate.from_messages(
    [
        system_prompt,
        MessagesPlaceholder(variable_name="messages"),
    ]
)

router_agent_executor = router_prompt_for_tools | router_llm_with_tools


# Define Graph Nodes
async def route_and_call_agent(state: MainAgentState) -> MainAgentState:
    """
    This node acts as the router. It takes the user's prompt, routes it to the LLM with tools,
    and captures the LLM's decision (tool call or direct response).
    """
    user_message = state["messages"][-1]  # Get the latest user message
    print(f"\nRouter Node: Receiving user message: '{user_message.content}'")

    response = await router_agent_executor.ainvoke({"messages": [user_message]})
    print(f"Router Node: LLM response (potential tool call): {response}")

    state["messages"].append(response)  # Add the LLM's response to the state

    selected_tool_name = None
    tool_raw_output = None

    if response.tool_calls:
        selected_tool_name = response.tool_calls[0]["name"]
        print(f"Router Node: Selected tool: {selected_tool_name}")
    else:
        # If no tool call, it means the LLM decided to respond directly
        selected_tool_name = "direct_response"
        tool_raw_output = json.dumps({"response": response.content})
        print(
            f"Router Node: LLM responded directly. Selected tool: {selected_tool_name}"
        )

    return {
        **state,
        "selected_tool_name": selected_tool_name,
        "tool_raw_output": tool_raw_output,
    }


async def call_tool_node(state: MainAgentState) -> MainAgentState:
    """
    Executes the tool chosen by the router LLM or processes a direct response.
    """
    messages = state["messages"]
    last_message = messages[-1]
    selected_tool_name = state.get("selected_tool_name")

    if selected_tool_name == "direct_response":
        print("Call Tool Node: Processing direct response from router LLM.")
        # tool_raw_output is already set by route_and_call_agent for direct_response
        return state

    if not last_message.tool_calls:
        print(
            "Call Tool Node: No tool call found in the last message, but not a direct response. This is unexpected."
        )
        # Fallback for unexpected scenarios
        return {
            **state,
            "tool_raw_output": json.dumps(
                {"error": "No tool call found after routing."}
            ),
            "selected_tool_name": "error_fallback",
        }

    tool_call = last_message.tool_calls[0]
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]
    tool_id = tool_call["id"]

    print(f"Call Tool Node: Executing tool '{tool_name}' with arguments: {tool_args}")

    tool_function = next((t for t in tools if t.name == tool_name), None)
    if tool_function:
        try:
            tool_output = await tool_function.ainvoke(tool_args)
            messages.append(ToolMessage(tool_output, tool_call_id=tool_id))
            return {**state, "messages": messages, "tool_raw_output": tool_output}
        except Exception as e:
            error_message = f"Error executing tool '{tool_name}': {e}"
            print(error_message)
            messages.append(
                ToolMessage(json.dumps({"error": error_message}), tool_call_id=tool_id)
            )
            return {
                **state,
                "messages": messages,
                "tool_raw_output": json.dumps({"error": error_message}),
            }
    else:
        error_message = f"Tool '{tool_name}' not found."
        print(error_message)
        messages.append(
            ToolMessage(json.dumps({"error": error_message}), tool_call_id=tool_id)
        )
        return {
            **state,
            "messages": messages,
            "tool_raw_output": json.dumps({"error": error_message}),
        }


async def generate_final_response_and_justify(state: MainAgentState) -> MainAgentState:
    """
    Generates a natural language response from the tool output and justifies the tool selection.
    """
    user_prompt = state["messages"][0].content
    selected_tool_name = state.get("selected_tool_name", "unknown_tool")
    tool_raw_output = state.get(
        "tool_raw_output", json.dumps({"error": "No tool output."})
    )

    print(
        f"\nFinal Response Node: Generating response for tool '{selected_tool_name}' output."
    )

    # Prompt for the final response generation and justification
    final_response_template = """
    You are a helpful AI assistant named Auraa and a manager of specialized agents.
    You have just processed a user's request.
    Your task is to:
    1.  Convert the raw JSON output (or direct response) into a natural, user-friendly answer. Ensure ALL information from the raw output without missing a single word is included in the natural language answer.
    2.  If the json output contains any links or URLs, ensure they are included in the final answer.
    3.  For summarization tool output start with the summary of the given document and then mention the keywords as well in the final natural_language_answer.
    4.  Provide a clear and concise justification for why the specific tool was chosen to address the user's original query. This justification MUST be a single line.
        If no tool was chosen (i.e., 'direct_response'), explain why a direct response was provided in a single line.

    Original User Query: {user_prompt}
    Tool Used: {selected_tool_name}
    Raw Tool Output/Direct Response (JSON): {tool_raw_output}

    Based on the above, provide your comprehensive response in the following format:

    **Answer:**
    [Natural language answer derived from the tool output, do not omit any of result except user_query, other than that keep everything in final response mentioning evrything use correct line terminations to make the response more effective. If the tool output indicates an error or no results, clearly state that. If it was a 'direct_response', provide the direct answer here.]

    **Justification for Tool Selection:**
    [Single-line explanation of why the '{selected_tool_name}' tool was chosen for the original query. If 'direct_response', explain why a direct response was given.]
    """

    final_response_prompt = ChatPromptTemplate.from_template(final_response_template)
    final_response_chain = final_response_prompt | llm

    try:
        final_llm_response = await final_response_chain.ainvoke(
            {
                "user_prompt": user_prompt,
                "selected_tool_name": selected_tool_name,
                "tool_raw_output": tool_raw_output,
            }
        )
        full_response_content = final_llm_response.content.strip()

        # Attempt to parse out Answer and Justification
        answer_start = full_response_content.find("**Answer:**")
        justification_start = full_response_content.find(
            "**Justification for Tool Selection:**"
        )

        natural_language_response = "Could not parse answer."
        justification = "Could not parse justification."

        if answer_start != -1 and justification_start != -1:
            natural_language_response = full_response_content[
                answer_start + len("**Answer:**") : justification_start
            ].strip()
            justification = full_response_content[
                justification_start + len("**Justification for Tool Selection:**") :
            ].strip()
        elif answer_start != -1:
            natural_language_response = full_response_content[
                answer_start + len("**Answer:**") :
            ].strip()
            justification = "Justification could not be clearly extracted."
        else:
            natural_language_response = (
                full_response_content  # Fallback if parsing fails
            )

        return {
            **state,
            "natural_language_response": natural_language_response,
            "justification": justification,
        }
    except Exception as e:
        error_msg = f"Error in final response generation: {e}"
        print(error_msg)
        return {
            **state,
            "natural_language_response": f"An error occurred while generating the final response: {e}",
            "justification": "Could not determine justification due to an error.",
        }


# 4. Build the Main LangGraph Graph
main_workflow = StateGraph(MainAgentState)

# Add nodes
main_workflow.add_node("router_and_tool_decider", route_and_call_agent)
main_workflow.add_node("execute_tool", call_tool_node)
main_workflow.add_node("generate_final_response", generate_final_response_and_justify)

# Set entry point
main_workflow.set_entry_point("router_and_tool_decider")

# Define edges
main_workflow.add_edge("router_and_tool_decider", "execute_tool")
main_workflow.add_edge("execute_tool", "generate_final_response")
main_workflow.add_edge("generate_final_response", END)

# Compile the graph
main_app = main_workflow.compile()


#  Main Agent Invocation Function
async def run_main_agent_orchestrator(user_prompt: str) -> str:
    """
    Runs the main graph agent to process a user prompt by selecting and invoking
    the appropriate sub-agent tool, then provides a natural language response
    and justification.

    Args:
        user_prompt (str): The user's input query.

    Returns:
        str: A JSON string containing the natural language response and justification.
    """
    initial_messages = [HumanMessage(content=user_prompt)]
    initial_state = {
        "messages": initial_messages,
        "selected_tool_name": None,
        "tool_raw_output": None,
        "natural_language_response": None,
        "justification": None,
    }

    final_state = None
    async for s in main_app.astream(initial_state):
        if "__end__" in s:
            final_state = s["__end__"]
        elif "execute_tool" in s:
            # Extract the state from the "execute_tool" key
            final_state = s["execute_tool"]
        elif "generate_final_response" in s:
            # Extract the state from the "generate_final_response" key
            final_state = s["generate_final_response"]
        else:
            final_state = s
            # Print intermediate states for debugging
            print(f"Intermediate State: {s}")

    if final_state and final_state.get("natural_language_response") is not None:
        return json.dumps(
            {
                "query": user_prompt,
                "response": final_state["natural_language_response"],
                "justification": final_state["justification"],
            },
            indent=2,
        )
    else:
        # Fallback for cases where final processing failed
        error_msg = (
            final_state.get("natural_language_response", "An unknown error occurred.")
            if final_state
            else "No final state."
        )
        justification_msg = (
            final_state.get("justification", "Could not determine justification.")
            if final_state
            else ""
        )
        return json.dumps(
            {
                "query": user_prompt,
                "response": f"Sorry, Auraa could not process your request. {error_msg}",
                "justification": justification_msg,
            },
            indent=2,
        )
