import json
from typing import TypedDict, List
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph
from langchain_core.documents import Document
from config import settings


# Define LangGraph State
class QueryAgentState(TypedDict):
    """
    Represents the state of our query responder agent's processing.

    Attributes:
        query (str): The original user query.
        documents (List[Document]): A list of documents to draw information from.
        response (str): The answer derived from the provided documents.
    """

    query: str
    documents: List[Document]
    response: str


# Initialize LLM
llm = settings.llm

# Define Prompt Template
response_template = """
You are a helpful assistant. Use the following documents to answer the user's query.
If the answer cannot be found in the documents, state that you don't have enough information.

Documents:
{context}

User Query: {query}

Answer:
"""
response_prompt = PromptTemplate(
    template=response_template, input_variables=["context", "query"]
)

# Define LangChain Chain
response_chain = response_prompt | llm


# Define Graph Node Function
async def generate_response(state: QueryAgentState) -> QueryAgentState:
    """
    Generates a response to the user query based on the provided documents.

    Args:
        state (QueryAgentState): The current state containing the query and documents.

    Returns:
        QueryAgentState: The updated state with the generated response.
    """
    user_query = state["query"]
    documents = state["documents"]

    # Concatenate document content to form the context for the LLM.
    # We assume documents are a list of Document objects, each with a 'page_content' attribute.
    context_text = "\n\n".join([doc.page_content for doc in documents])

    # Invoke the response chain.
    response_result = await response_chain.ainvoke(
        {"context": context_text, "query": user_query}
    )
    generated_response = response_result.content.strip()

    # Update the state with the generated response
    return {"query": user_query, "documents": documents, "response": generated_response}


# Build the LangGraph Graph
# Create a StateGraph instance with our defined state.
query_workflow = StateGraph(QueryAgentState)

query_workflow.add_node("response_node", generate_response)


query_workflow.set_entry_point("response_node")
query_workflow.set_finish_point("response_node")
query_app = query_workflow.compile()


# Agent Invocation Function
async def run_query_responder_agent(user_query: str, documents_list: List[str]) -> str:
    """
    Runs the query responder agent.

    Args:
        user_query (str): The user's question.
        documents_list (List[str]): A list of document strings to use as context.

    Returns:
        str: A JSON string containing the original query and the derived response.
    """
    # Convert list of strings to list of LangChain Document objects
    # This is a common pattern when working with LangChain's document handling.
    documents = [Document(page_content=doc_str) for doc_str in documents_list]

    # Initial state for the graph.
    initial_state = {"query": user_query, "documents": documents, "response": ""}

    # Invoke the compiled graph.
    final_state = None
    async for s in query_app.astream(initial_state):
        final_state = s

    # Extract the results from the final state.
    final_query = final_state["response_node"]["query"]
    final_response = final_state["response_node"]["response"]

    # Format the output as a JSON string.
    output_json = {"query": final_query, "response": final_response}
    return json.dumps(output_json, indent=2)
