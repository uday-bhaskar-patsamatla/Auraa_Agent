from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import json

from agents.main_agent import run_main_agent_orchestrator
from agents.document_summarizer import run_document_agent
from agents.query_responder import run_query_responder_agent
from agents.real_time_data_extractor import run_internet_agent

router = APIRouter()


# Pydantic Models for Main Agent Route
class MainQueryRequest(BaseModel):
    user_prompt: str


class MainQueryResponse(BaseModel):
    query: str
    response: str
    justification: str


# Pydantic Models for Agent 1: Document Summarizer and Keyword Extractor
class DocumentSummarizerRequest(BaseModel):
    document_content: str = Field(
        ...,
        description="The full text content of the document to be summarized and from which keywords will be extracted.",
    )


class DocumentSummarizerResponse(BaseModel):
    document: str = Field(
        ..., alias="doc_summary", description="The summarized content of the document."
    )
    keywords: List[str] = Field(
        ..., description="A list of important keywords extracted from the document."
    )

    class Config:
        populate_by_name = True  # Allows using alias for field name in Pydantic v2


# Pydantic Models for Agent 2: Query Responder
class QueryResponderRequest(BaseModel):
    user_query: str = Field(..., description="The user's question to be answered.")
    documents_list: List[str] = Field(
        ...,
        description="A list of document strings that the query responder should use as context to answer the query.",
    )


class QueryResponderResponse(BaseModel):
    query: str = Field(..., description="The original user query.")
    response: str = Field(
        ..., description="The answer derived from the provided documents."
    )


# Pydantic Models for Agent 3: Internet-Connected Agent
class InternetAgentRequest(BaseModel):
    user_query: str = Field(
        ...,
        description="The user's question that requires up-to-date information from the internet.",
    )


class InternetAgentResponse(BaseModel):
    query: str = Field(..., description="The original user query.")
    response: str = Field(
        ..., description="The real-time answer fetched from the internet."
    )
    source: Optional[str] = Field(
        None, description="URL or source of the fetched information."
    )


# Main Agent Route
@router.post(
    "/process_query",
    response_model=MainQueryResponse,
    summary="Process user query with Auraa Manager Agent",
)
async def process_user_query(request: MainQueryRequest):
    """
    Processes a user query by routing it to the appropriate specialized agent
    and returning a natural language response with justification.
    """
    try:
        print(f"Received query for Manager Agent: {request.user_prompt}")
        result_json_str = await run_main_agent_orchestrator(request.user_prompt)
        result_data = json.loads(result_json_str)

        if "error" in result_data:
            raise HTTPException(status_code=500, detail=result_data["error"])

        return MainQueryResponse(
            query=result_data.get("query", request.user_prompt),
            response=result_data.get("response", "No response generated."),
            justification=result_data.get(
                "justification", "No justification provided."
            ),
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred in Manager Agent route: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


# Individual Agent Routes


@router.post(
    "/agent1/summarize",
    response_model=DocumentSummarizerResponse,
    summary="Document Summarizer and Keyword Extractor (Agent 1)",
)
async def summarize_document_route(request: DocumentSummarizerRequest):
    """
    Summarizes the given document content and extracts a list of keywords.
    """
    try:
        print(
            f"Received request for Agent 1 (Summarizer). Document length: {len(request.document_content)}"
        )
        result_json_str = await run_document_agent(request.document_content)
        result_data = json.loads(result_json_str)

        if "error" in result_data:
            raise HTTPException(status_code=500, detail=result_data["error"])

        # Use the alias for 'document' field as per assignment PDF
        return DocumentSummarizerResponse(
            doc_summary=result_data.get("document", ""),
            keywords=result_data.get("keywords", []),
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred in Agent 1 route: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.post(
    "/agent2/respond_to_query",
    response_model=QueryResponderResponse,
    summary="Query Responder (Agent 2)",
)
async def respond_to_query_route(request: QueryResponderRequest):
    """
    Responds to a user query based on provided document content.
    """
    try:
        print(
            f"Received request for Agent 2 (Query Responder). Query: {request.user_query}"
        )
        result_json_str = await run_query_responder_agent(
            request.user_query, request.documents_list
        )
        result_data = json.loads(result_json_str)

        if "error" in result_data:
            raise HTTPException(status_code=500, detail=result_data["error"])

        return QueryResponderResponse(
            query=result_data.get("query", request.user_query),
            response=result_data.get("response", "No response generated."),
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred in Agent 2 route: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.post(
    "/agent3/search_internet",
    response_model=InternetAgentResponse,
    summary="Internet-Connected Agent (Agent 3)",
)
async def search_internet_route(request: InternetAgentRequest):
    """
    Fetches real-time, up-to-date information from the internet to answer a user's question.
    """
    try:
        print(
            f"Received request for Agent 3 (Internet Agent). Query: {request.user_query}"
        )
        result_json_str = await run_internet_agent(request.user_query)
        result_data = json.loads(result_json_str)

        if "error" in result_data:
            raise HTTPException(status_code=500, detail=result_data["error"])

        return InternetAgentResponse(
            query=result_data.get("query", request.user_query),
            response=result_data.get("response", "No response generated."),
            source=result_data.get("source"),  # Source can be optional
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred in Agent 3 route: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
