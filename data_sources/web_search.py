from langchain_tavily import TavilySearch
from dotenv import load_dotenv

load_dotenv()

def create_search_web_tool(max_result=5):
    tool = TavilySearch(
        max_results=max_result,
        topic="general",
        # include_answer=False,
        # include_raw_content=False,
        # include_images=False,
        # include_image_descriptions=False,
        # search_depth="basic",
        # time_range="day",
        # include_domains=None,
        # exclude_domains=None
    )
    return tool
