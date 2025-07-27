import json
from typing import TypedDict, List
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph
from config import settings


# Define LangGraph State
class AgentState(TypedDict):
    """
    Represents the state of our agent's processing.

    Attributes:
        document_content (str): The input document text to be processed.
        document_summary (str): The summarized content of the document.
        keywords (List[str]): A list of extracted keywords from the document.
    """

    document_content: str
    document_summary: str
    keywords: List[str]


# Initialize LLM
llm = settings.llm

# Define Prompt Templates
summary_template = """
You are an expert summarizer. Summarize the following document concisely and accurately.
Document:
{document}

Summary:
"""
summary_prompt = PromptTemplate(template=summary_template, input_variables=["document"])

# Prompt for keyword extraction.
keywords_template = """
From the following document, extract a list of important keywords.
Provide them as a comma-separated list. Do not include any other text.
Document:
{document}

Keywords:
"""
keywords_prompt = PromptTemplate(
    template=keywords_template, input_variables=["document"]
)

# Define LangChain Chains
summary_chain = summary_prompt | llm

# Create a chain for keyword extraction using LCEL.
keywords_chain = keywords_prompt | llm


# Define Graph Node Function
async def process_document(state: AgentState) -> AgentState:
    """
    Processes the input document to generate a summary and extract keywords.

    Args:
        state (AgentState): The current state containing the document content.

    Returns:
        AgentState: The updated state with document_summary and keywords.
    """
    document = state["document_content"]

    # Generate summary
    # LCEL chains use .ainvoke directly with the input dictionary.
    summary_result = await summary_chain.ainvoke({"document": document})
    doc_summary = (
        summary_result.content.strip()
    )  # Access content attribute for ChatOpenAI output

    # Extract keywords
    keywords_result = await keywords_chain.ainvoke({"document": document})
    # Split the comma-separated string into a list and clean up whitespace.
    keywords_str = keywords_result.content.strip()
    keywords = [kw.strip() for kw in keywords_str.split(",") if kw.strip()]

    # Update the state with the results
    return {
        "document_content": document,
        "document_summary": doc_summary,
        "keywords": keywords,
    }


# Build the LangGraph Graph
workflow = StateGraph(AgentState)

# Add the single node to our graph.
workflow.add_node("process_doc_node", process_document)

# Set the entry point of the graph. When the graph starts, it will execute 'process_doc_node'.
workflow.set_entry_point("process_doc_node")

# Set the exit point of the graph.
workflow.set_finish_point("process_doc_node")

# Compile the graph into an executable application.
app = workflow.compile()


# Agent Invocation Function
async def run_document_agent(document_text: str) -> str:
    """
    Runs the document summarizer and keyword extractor agent.

    Args:
        document_text (str): The text content of the document to process.

    Returns:
        str: A JSON string containing the document summary and extracted keywords.
    """
    # Initial state for the graph.
    initial_state = {
        "document_content": document_text,
        "document_summary": "",
        "keywords": [],
    }

    # Invoke the compiled graph.
    # The 'stream' method can be used for more granular control or real-time updates
    final_state = None
    async for s in app.astream(initial_state):
        final_state = s

    # Extract the results from the final state.
    summary = final_state["process_doc_node"]["document_summary"]
    keywords = final_state["process_doc_node"]["keywords"]

    # Format the output as a JSON string.
    output_json = {"document": summary, "keywords": keywords}
    return json.dumps(output_json, indent=2)
