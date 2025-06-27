from typing import TypedDict, Annotated

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


class FlightSearchInput(BaseModel):
    origin: str = Field(description="The starting location or airport.")
    destination: str = Field(description="The destination location or airport.")
    date_range: str = Field(description="The desired travel dates, e.g., 'July 10-17'.")

class HotelSearchInput(BaseModel):
    destination: str = Field(description="The city or area to search for hotels.")
    date_range: str = Field(description="The check-in and check-out dates.")
    num_travelers: int = Field(description="The number of people needing accommodation.")

class AttractionSearchInput(BaseModel):
    destination: str = Field(description="The city or area to search for attractions.")
    interests: str = Field(description="Keywords describing the user's interests, e.g., 'history, food, museums'.")

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], lambda x, y: x + y]