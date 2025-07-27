import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
load_dotenv()


class Settings:
    """
    Application settings loaded from environment variables.
    """

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    if not OPENAI_API_KEY:
        print("WARNING: OPENAI_API_KEY environment variable not set.")
    if not TAVILY_API_KEY:
        print("WARNING: TAVILY_API_KEY environment variable not set.")

    llm = ChatOpenAI(
        model="o4-mini-2025-04-16", temperature=1, api_key=OPENAI_API_KEY
    )  # Using gpt-3.5-turbo with temperature 0


settings = Settings()
