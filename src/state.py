from typing import List, Any, Dict, Union, Annotated
import operator
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field, ConfigDict

class AgentState(BaseModel):
    model_config = ConfigDict(extra="allow")
    messages: Annotated[List[Any], operator.add] = Field(default_factory=list)

    # The following fields are removed as per the instructions:
    # events: List[Dict] = Field(default_factory=list)
    # tasks: List[str] = Field(default_factory=list)
    # emails: List[Dict] = Field(default_factory=list)
    # drafts: List[str] = Field(default_factory=list)
    # user_prefs: Dict[str, Any] = {}      # Preferences (e.g., briefing time) 